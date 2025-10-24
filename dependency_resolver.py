"""
Dependency Resolver - Resuelve dependencias entre tablas y calcula orden óptimo de transferencia
Incluye manejo de dependencias circulares y optimizaciones de rendimiento
"""

import logging
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass
from schema_analyzer import SchemaInfo, TableInfo, ForeignKeyInfo, SchemaObjects
from treelib import Node, Tree


@dataclass
class TransferBatch:
    """Lote de tablas que pueden transferirse en paralelo"""
    level: int
    tables: List[str]
    estimated_time: float
    total_rows: int


@dataclass
class DependencyGraph:
    """Grafo de dependencias entre tablas"""
    nodes: Dict[str, Set[str]]  # tabla -> dependencias
    reverse_nodes: Dict[str, Set[str]]  # tabla -> dependientes
    cycles: List[List[str]]  # Ciclos detectados
    levels: Dict[str, int]  # Nivel de cada tabla en el grafo


class DependencyResolver:
    """Resuelve dependencias entre tablas y optimiza el orden de transferencia"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_dependency_graph(self, schema_info: SchemaInfo) -> DependencyGraph:
        """Crea el grafo de dependencias del esquema de manera robusta"""
        
        try:
            self.logger.info(f"Creando grafo de dependencias para esquema: {schema_info.schema_name}")
            
            nodes = {}
            reverse_nodes = {}
            
            # Verificar que hay tablas
            if not schema_info.objects.tables:
                self.logger.warning("No hay tablas para analizar dependencias")
                return DependencyGraph(nodes={}, reverse_nodes={}, cycles=[], levels={})
            
            # Inicializar nodos de manera segura
            for table_name in schema_info.objects.tables:
                nodes[table_name] = set()
                reverse_nodes[table_name] = set()
            
            # Construir grafo de manera robusta
            for table_name, table_info in schema_info.objects.tables.items():
                try:
                    for fk in table_info.foreign_keys:
                        referenced_table = fk.referenced_table
                        
                        # Solo considerar referencias dentro del esquema
                        if (referenced_table and 
                            hasattr(fk, 'referenced_schema') and 
                            fk.referenced_schema == schema_info.schema_name and 
                            referenced_table in schema_info.objects.tables):
                            
                            nodes[table_name].add(referenced_table)
                            reverse_nodes[referenced_table].add(table_name)
                            
                except Exception as e:
                    self.logger.warning(f"Error procesando FK de tabla {table_name}: {e}")
                    continue
            
            # Detectar ciclos de manera segura
            try:
                cycles = self._detect_cycles(nodes)
            except Exception as e:
                self.logger.warning(f"Error detectando ciclos: {e}")
                cycles = []
            
            # Calcular niveles de manera segura
            try:
                levels = self._calculate_levels(nodes, cycles)
            except Exception as e:
                self.logger.warning(f"Error calculando niveles: {e}")
                # Asignar nivel 0 a todas las tablas como fallback
                levels = {table: 0 for table in nodes.keys()}
                
        except Exception as e:
            self.logger.error(f"Error crítico creando grafo de dependencias: {e}")
            # Crear grafo vacío como fallback
            return DependencyGraph(nodes={}, reverse_nodes={}, cycles=[], levels={})
        
        return DependencyGraph(
            nodes=nodes,
            reverse_nodes=reverse_nodes,
            cycles=cycles,
            levels=levels
        )
    
    def _detect_cycles(self, nodes: Dict[str, Set[str]]) -> List[List[str]]:
        """Detecta ciclos en el grafo usando DFS"""
        
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str) -> bool:
            if node in rec_stack:
                # Encontramos un ciclo
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return True
            
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in nodes.get(node, set()):
                if dfs(neighbor):
                    return True
            
            rec_stack.remove(node)
            path.pop()
            return False
        
        for node in nodes:
            if node not in visited:
                dfs(node)
        
        return cycles
    
    def _calculate_levels(self, nodes: Dict[str, Set[str]], cycles: List[List[str]]) -> Dict[str, int]:
        """Calcula el nivel de cada tabla en el grafo"""
        
        levels = {}
        
        # Tablas en ciclos se asignan al mismo nivel
        cycle_tables = set()
        for cycle in cycles:
            cycle_tables.update(cycle)
        
        # Algoritmo de Kahn modificado para calcular niveles
        in_degree = {}
        for table in nodes:
            in_degree[table] = len(nodes[table])
        
        # Tablas sin dependencias están en el nivel 0
        current_level = 0
        queue = [table for table, degree in in_degree.items() if degree == 0]
        
        while queue:
            next_queue = []
            
            for table in queue:
                levels[table] = current_level
            
            # Procesar dependientes
            for table in queue:
                for dependent_table in nodes:
                    if table in nodes[dependent_table]:
                        in_degree[dependent_table] -= 1
                        if in_degree[dependent_table] == 0:
                            next_queue.append(dependent_table)
            
            queue = next_queue
            current_level += 1
        
        # Asignar tablas restantes (probablemente en ciclos) al último nivel
        max_level = max(levels.values()) if levels else 0
        for table in nodes:
            if table not in levels:
                levels[table] = max_level + 1
        
        return levels
    
    def create_transfer_batches(self, schema_info: SchemaInfo, 
                               dependency_graph: DependencyGraph,
                               max_batch_size: int = 5) -> List[TransferBatch]:
        """Crea lotes optimizados para transferencia paralela"""
        
        self.logger.info("Creando lotes de transferencia optimizados")
        
        batches = []
        
        # Agrupar tablas por nivel
        level_groups = {}
        for table, level in dependency_graph.levels.items():
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(table)
        
        # Crear lotes por nivel
        for level in sorted(level_groups.keys()):
            tables_in_level = level_groups[level]
            
            # Dividir en lotes más pequeños si es necesario
            for i in range(0, len(tables_in_level), max_batch_size):
                batch_tables = tables_in_level[i:i + max_batch_size]
                
                # Calcular estadísticas del lote
                total_rows = sum(schema_info.objects.tables[table].row_count 
                               for table in batch_tables)
                
                estimated_time = self._estimate_transfer_time(
                    schema_info, batch_tables
                )
                
                batch = TransferBatch(
                    level=level,
                    tables=batch_tables,
                    estimated_time=estimated_time,
                    total_rows=total_rows
                )
                
                batches.append(batch)
        
        return batches
    
    def _estimate_transfer_time(self, schema_info: SchemaInfo, tables: List[str]) -> float:
        """Estima el tiempo de transferencia para un lote de tablas"""
        
        base_time_per_row = 0.001  # segundos por fila (estimación)
        setup_time_per_table = 1.0  # segundos de setup por tabla
        
        total_rows = sum(schema_info.objects.tables[table].row_count for table in tables)
        total_tables = len(tables)
        
        estimated_time = (total_rows * base_time_per_row + 
                         total_tables * setup_time_per_table)
        
        return estimated_time
    
    def resolve_circular_dependencies(self, schema_info: SchemaInfo, 
                                    cycles: List[List[str]]) -> Dict[str, List[str]]:
        """Resuelve dependencias circulares sugiriendo estrategias"""
        
        self.logger.warning(f"Resolviendo {len(cycles)} dependencias circulares")
        
        resolution_strategies = {}
        
        for cycle in cycles:
            strategies = []
            
            # Analizar cada tabla en el ciclo
            for table_name in cycle:
                table_info = schema_info.objects.tables[table_name]
                
                # Buscar FK que pueden ser nullable
                nullable_fks = []
                for fk in table_info.foreign_keys:
                    if fk.referenced_table in cycle:
                        # Verificar si la columna FK es nullable
                        for column in table_info.columns:
                            if (column.name == fk.column_name and 
                                column.is_nullable):
                                nullable_fks.append(fk)
                
                if nullable_fks:
                    strategies.append({
                        'type': 'nullable_fk',
                        'table': table_name,
                        'description': f'Insertar {table_name} con FK nulos, actualizar después',
                        'foreign_keys': [fk.column_name for fk in nullable_fks]
                    })
            
            if not strategies:
                # Si no hay FK nullable, sugerir deshabilitar constraints temporalmente
                strategies.append({
                    'type': 'disable_constraints',
                    'tables': cycle,
                    'description': 'Deshabilitar constraints de FK temporalmente'
                })
            
            resolution_strategies[f"cycle_{cycles.index(cycle)}"] = strategies
        
        return resolution_strategies
    
    def optimize_transfer_order(self, schema_info: SchemaInfo,
                               priority_tables: Optional[List[str]] = None,
                               size_threshold: int = 1000000) -> List[str]:
        """Optimiza el orden de transferencia considerando prioridades y tamaño"""
        
        self.logger.info("Optimizando orden de transferencia")
        
        dependency_graph = self.create_dependency_graph(schema_info)
        base_order = schema_info.dependency_order.copy()
        
        # Separar tablas grandes y pequeñas
        large_tables = []
        small_tables = []
        
        for table in base_order:
            table_info = schema_info.objects.tables[table]
            if table_info.row_count > size_threshold:
                large_tables.append(table)
            else:
                small_tables.append(table)
        
        # Aplicar prioridades
        if priority_tables:
            prioritized = []
            remaining = []
            
            for table in base_order:
                if table in priority_tables:
                    prioritized.append(table)
                else:
                    remaining.append(table)
            
            # Verificar que las dependencias se respeten
            final_order = self._respect_dependencies(
                prioritized + remaining, dependency_graph
            )
        else:
            # Orden optimizado: pequeñas primero dentro de cada nivel
            final_order = self._interleave_by_size(
                small_tables, large_tables, dependency_graph
            )
        
        return final_order
    
    def _respect_dependencies(self, proposed_order: List[str], 
                            dependency_graph: DependencyGraph) -> List[str]:
        """Ajusta el orden propuesto para respetar dependencias"""
        
        adjusted_order = []
        remaining = set(proposed_order)
        
        while remaining:
            # Encontrar tablas sin dependencias pendientes
            ready_tables = []
            
            for table in proposed_order:
                if table not in remaining:
                    continue
                
                # Verificar si todas las dependencias ya están en adjusted_order
                dependencies = dependency_graph.nodes.get(table, set())
                if dependencies.issubset(set(adjusted_order)):
                    ready_tables.append(table)
            
            if not ready_tables:
                # Ciclo detectado o error, agregar tabla arbitraria
                ready_tables = [next(iter(remaining))]
                self.logger.warning(f"Forzando orden para tabla: {ready_tables[0]}")
            
            # Agregar la primera tabla lista (respeta el orden original)
            for table in proposed_order:
                if table in ready_tables:
                    adjusted_order.append(table)
                    remaining.remove(table)
                    break
        
        return adjusted_order
    
    def _interleave_by_size(self, small_tables: List[str], 
                           large_tables: List[str],
                           dependency_graph: DependencyGraph) -> List[str]:
        """Intercala tablas pequeñas y grandes respetando dependencias"""
        
        # Por ahora, simplemente concatenar manteniendo el orden por dependencias
        all_tables = small_tables + large_tables
        return self._respect_dependencies(all_tables, dependency_graph)
    
    def create_dependency_tree(self, schema_info: SchemaInfo) -> Tree:
        """Crea un árbol visual de dependencias de manera robusta"""
        
        try:
            tree = Tree()
            dependency_graph = self.create_dependency_graph(schema_info)
            
            # Siempre crear una raíz única para evitar problemas
            tree.create_node("📊 Esquema: " + schema_info.schema_name, "schema_root")
            
            # Obtener todas las tablas
            all_tables = set(schema_info.objects.tables.keys())
            if not all_tables:
                tree.create_node("❌ Sin tablas", "no_tables", parent="schema_root")
                return tree
            
            # Encontrar tablas raíz (sin dependencias)
            root_tables = [table for table, deps in dependency_graph.nodes.items() 
                          if not deps and table in all_tables]
            
            # Crear sección de tablas raíz
            if root_tables:
                tree.create_node("🌱 Tablas Raíz", "root_section", parent="schema_root")
                for table in root_tables:
                    tree.create_node(f"📋 {table}", f"root_{table}", parent="root_section")
            
            # Crear sección de tablas con dependencias
            dependent_tables = [table for table in all_tables if table not in root_tables]
            if dependent_tables:
                tree.create_node("🔗 Tablas con Dependencias", "dep_section", parent="schema_root")
                
                # Agrupar por nivel de dependencia
                levels = dependency_graph.levels
                max_level = max(levels.values()) if levels else 0
                
                for level in range(1, max_level + 1):
                    tables_in_level = [table for table, lvl in levels.items() 
                                     if lvl == level and table in all_tables]
                    
                    if tables_in_level:
                        level_node_id = f"level_{level}"
                        tree.create_node(f"📚 Nivel {level}", level_node_id, parent="dep_section")
                        
                        for table in tables_in_level:
                            deps = dependency_graph.nodes.get(table, set())
                            deps_info = f" (deps: {len(deps)})" if deps else ""
                            tree.create_node(f"📋 {table}{deps_info}", f"dep_{table}", parent=level_node_id)
            
            # Agregar sección de ciclos si existen
            if dependency_graph.cycles:
                tree.create_node("🔄 Dependencias Circulares", "cycles_section", parent="schema_root")
                
                for i, cycle in enumerate(dependency_graph.cycles, 1):
                    cycle_id = f"cycle_{i}"
                    cycle_text = " → ".join(cycle[:3]) + ("..." if len(cycle) > 3 else "")
                    tree.create_node(f"⚠️ Ciclo {i}: {cycle_text}", cycle_id, parent="cycles_section")
            
            # Agregar estadísticas
            stats_text = f"📊 {len(all_tables)} tablas, {len(root_tables)} raíz, {len(dependent_tables)} con deps"
            tree.create_node(stats_text, "stats", parent="schema_root")
            
            return tree
            
        except Exception as e:
            # Si falla, crear árbol básico
            self.logger.error(f"Error creando árbol de dependencias: {e}")
            
            fallback_tree = Tree()
            fallback_tree.create_node("❌ Error en árbol", "error_root")
            fallback_tree.create_node(f"Error: {str(e)}", "error_msg", parent="error_root")
            
            # Listar tablas básicamente
            for table in schema_info.objects.tables.keys():
                fallback_tree.create_node(f"📋 {table}", f"table_{table}", parent="error_root")
            
            return fallback_tree
    
    def validate_transfer_plan(self, schema_info: SchemaInfo, 
                             transfer_order: List[str]) -> Dict[str, Any]:
        """Valida el plan de transferencia y retorna estadísticas"""
        
        dependency_graph = self.create_dependency_graph(schema_info)
        
        validation_result = {
            'is_valid': True,
            'issues': [],
            'statistics': {
                'total_tables': len(transfer_order),
                'total_rows': 0,
                'estimated_time': 0,
                'cycles_detected': len(dependency_graph.cycles),
                'levels': max(dependency_graph.levels.values()) + 1 if dependency_graph.levels else 0
            }
        }
        
        # Verificar orden de dependencias
        processed = set()
        for table in transfer_order:
            if table not in schema_info.tables:
                validation_result['issues'].append({
                    'type': 'missing_table',
                    'table': table,
                    'message': f'Tabla {table} no existe en el esquema'
                })
                validation_result['is_valid'] = False
                continue
            
            # Verificar dependencias
            dependencies = dependency_graph.nodes.get(table, set())
            missing_deps = dependencies - processed
            
            if missing_deps:
                validation_result['issues'].append({
                    'type': 'dependency_violation',
                    'table': table,
                    'missing_dependencies': list(missing_deps),
                    'message': f'Tabla {table} requiere que se procesen primero: {missing_deps}'
                })
                validation_result['is_valid'] = False
            
            processed.add(table)
            
            # Actualizar estadísticas
            table_info = schema_info.objects.tables[table]
            validation_result['statistics']['total_rows'] += table_info.row_count
        
        # Estimar tiempo total
        validation_result['statistics']['estimated_time'] = self._estimate_transfer_time(
            schema_info, transfer_order
        )
        
        return validation_result
    
    def suggest_optimizations(self, schema_info: SchemaInfo) -> List[Dict[str, Any]]:
        """Sugiere optimizaciones para mejorar el rendimiento de transferencia"""
        
        suggestions = []
        dependency_graph = self.create_dependency_graph(schema_info)
        
        # Sugerir índices para FK
        for table_name, table_info in schema_info.objects.tables.items():
            for fk in table_info.foreign_keys:
                # Verificar si existe índice en la FK
                fk_indexed = any(
                    fk.column_name in str(idx.get('definition', '')) or
                    fk.column_name in str(idx.get('name', ''))
                    for idx in table_info.indexes
                )
                
                if not fk_indexed:
                    suggestions.append({
                        'type': 'add_index',
                        'table': table_name,
                        'column': fk.column_name,
                        'message': f'Agregar índice en {table_name}.{fk.column_name} para mejorar rendimiento de FK'
                    })
        
        # Sugerir procesamiento por lotes para tablas grandes
        large_tables = [
            (name, info.row_count) 
            for name, info in schema_info.objects.tables.items() 
            if info.row_count > 100000
        ]
        
        for table_name, row_count in large_tables:
            suggestions.append({
                'type': 'batch_processing',
                'table': table_name,
                'rows': row_count,
                'message': f'Procesar {table_name} por lotes ({row_count:,} filas)'
            })
        
        # Sugerir paralelización
        if len(dependency_graph.cycles) == 0:
            parallel_groups = {}
            for table, level in dependency_graph.levels.items():
                if level not in parallel_groups:
                    parallel_groups[level] = []
                parallel_groups[level].append(table)
            
            for level, tables in parallel_groups.items():
                if len(tables) > 1:
                    suggestions.append({
                        'type': 'parallel_processing',
                        'level': level,
                        'tables': tables,
                        'message': f'Procesar en paralelo nivel {level}: {", ".join(tables)}'
                    })
        
        return suggestions