"""
Extended Transfer - Transferidor extendido que maneja todos los objetos de base de datos
Incluye vistas, procedimientos, secuencias, triggers, índices, etc.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from sqlalchemy import text
from sqlalchemy.engine import Engine

from schema_analyzer import SchemaInfo, SchemaObjects, SequenceInfo, ViewInfo, ProcedureInfo, TriggerInfo, IndexInfo
from database_manager import DatabaseManager
from data_transfer import DataTransfer


@dataclass
class TransferStats:
    """Estadísticas de la transferencia extendida"""
    sequences_created: int = 0
    tables_created: int = 0
    views_created: int = 0
    procedures_created: int = 0
    triggers_created: int = 0
    indexes_created: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class ExtendedTransfer:
    """Transferidor extendido para todos los objetos de base de datos"""
    
    def __init__(self, source_db_manager: DatabaseManager, target_db_manager: DatabaseManager):
        self.source_db = source_db_manager
        self.target_db = target_db_manager
        self.logger = logging.getLogger(__name__)
        
        # Para transferencia de datos de tablas
        self.data_transfer = DataTransfer(source_db_manager, target_db_manager)
    
    def transfer_complete_schema(self, 
                               source_engine: Engine, 
                               target_engine: Engine,
                               source_db_type: str,
                               target_db_type: str,
                               source_schema_info: SchemaInfo,
                               target_schema: str,
                               transfer_data: bool = True,
                               progress_callback: Optional[callable] = None) -> TransferStats:
        """Transfiere un esquema completo con todos los objetos"""
        
        self.logger.info(f"Iniciando transferencia completa del esquema: {source_schema_info.schema_name}")
        
        stats = TransferStats()
        total_objects = self._count_total_objects(source_schema_info)
        processed_objects = 0
        
        try:
            # 1. Crear secuencias
            if source_schema_info.objects.sequences:
                self.logger.info("Creando secuencias...")
                for seq_name, seq_info in source_schema_info.objects.sequences.items():
                    try:
                        self._create_sequence(target_engine, target_db_type, target_schema, seq_info)
                        stats.sequences_created += 1
                        processed_objects += 1
                        
                        if progress_callback:
                            progress_callback(processed_objects, total_objects, f"Secuencia creada: {seq_name}")
                            
                    except Exception as e:
                        error_msg = f"Error creando secuencia {seq_name}: {str(e)}"
                        self.logger.error(error_msg)
                        stats.errors.append(error_msg)
            
            # 2. Crear tablas (estructura) - usar el transferidor existente
            if source_schema_info.objects.tables:
                self.logger.info("Creando estructura de tablas...")
                for table_name in source_schema_info.dependency_order:
                    try:
                        table_info = source_schema_info.objects.tables[table_name]
                        self._create_table_structure(target_engine, target_db_type, target_schema, table_info)
                        stats.tables_created += 1
                        processed_objects += 1
                        
                        if progress_callback:
                            progress_callback(processed_objects, total_objects, f"Tabla creada: {table_name}")
                            
                    except Exception as e:
                        error_msg = f"Error creando tabla {table_name}: {str(e)}"
                        self.logger.error(error_msg)
                        stats.errors.append(error_msg)
            
            # 3. Transferir datos de tablas si se solicita
            if transfer_data and source_schema_info.objects.tables:
                self.logger.info("Transfiriendo datos de tablas...")
                # Usar el transferidor de datos existente
                self.data_transfer.transfer_schema_data(
                    source_engine, target_engine,
                    source_db_type, target_db_type,
                    source_schema_info, target_schema,
                    progress_callback
                )
            
            # 4. Crear vistas
            if source_schema_info.objects.views:
                self.logger.info("Creando vistas...")
                # Usar el orden calculado para vistas
                view_order = self._get_view_creation_order(source_schema_info)
                for view_name in view_order:
                    try:
                        view_info = source_schema_info.objects.views[view_name]
                        self._create_view(target_engine, target_db_type, target_schema, view_info)
                        stats.views_created += 1
                        processed_objects += 1
                        
                        if progress_callback:
                            progress_callback(processed_objects, total_objects, f"Vista creada: {view_name}")
                            
                    except Exception as e:
                        error_msg = f"Error creando vista {view_name}: {str(e)}"
                        self.logger.error(error_msg)
                        stats.errors.append(error_msg)
            
            # 5. Crear índices personalizados
            if source_schema_info.objects.indexes:
                self.logger.info("Creando índices...")
                for index_name, index_info in source_schema_info.objects.indexes.items():
                    try:
                        if not self._is_system_index(index_info):
                            self._create_index(target_engine, target_db_type, target_schema, index_info)
                            stats.indexes_created += 1
                            processed_objects += 1
                            
                            if progress_callback:
                                progress_callback(processed_objects, total_objects, f"Índice creado: {index_name}")
                                
                    except Exception as e:
                        error_msg = f"Error creando índice {index_name}: {str(e)}"
                        self.logger.error(error_msg)
                        stats.errors.append(error_msg)
            
            # 6. Crear procedimientos y funciones
            if source_schema_info.objects.procedures:
                self.logger.info("Creando procedimientos y funciones...")
                for proc_name, proc_info in source_schema_info.objects.procedures.items():
                    try:
                        self._create_procedure(target_engine, target_db_type, target_schema, proc_info)
                        stats.procedures_created += 1
                        processed_objects += 1
                        
                        if progress_callback:
                            progress_callback(processed_objects, total_objects, f"Procedimiento creado: {proc_name}")
                            
                    except Exception as e:
                        error_msg = f"Error creando procedimiento {proc_name}: {str(e)}"
                        self.logger.error(error_msg)
                        stats.errors.append(error_msg)
            
            # 7. Crear triggers (al final)
            if source_schema_info.objects.triggers:
                self.logger.info("Creando triggers...")
                for trigger_name, trigger_info in source_schema_info.objects.triggers.items():
                    try:
                        self._create_trigger(target_engine, target_db_type, target_schema, trigger_info)
                        stats.triggers_created += 1
                        processed_objects += 1
                        
                        if progress_callback:
                            progress_callback(processed_objects, total_objects, f"Trigger creado: {trigger_name}")
                            
                    except Exception as e:
                        error_msg = f"Error creando trigger {trigger_name}: {str(e)}"
                        self.logger.error(error_msg)
                        stats.errors.append(error_msg)
            
            self.logger.info("Transferencia completa terminada exitosamente")
            
        except Exception as e:
            error_msg = f"Error general en transferencia: {str(e)}"
            self.logger.error(error_msg)
            stats.errors.append(error_msg)
        
        return stats
    
    def _count_total_objects(self, schema_info: SchemaInfo) -> int:
        """Cuenta el total de objetos a transferir"""
        total = 0
        total += len(schema_info.objects.sequences)
        total += len(schema_info.objects.tables)
        total += len(schema_info.objects.views)
        total += len(schema_info.objects.procedures)
        total += len(schema_info.objects.triggers)
        total += len([idx for idx in schema_info.objects.indexes.values() if not self._is_system_index(idx)])
        return total
    
    def _create_sequence(self, engine: Engine, db_type: str, schema: str, seq_info: SequenceInfo):
        """Crea una secuencia en la base de datos destino"""
        
        with engine.connect() as conn:
            if db_type.lower() == 'oracle':
                sql = f"""
                    CREATE SEQUENCE {schema}.{seq_info.sequence_name}
                    START WITH {seq_info.start_value}
                    INCREMENT BY {seq_info.increment_by}
                """
                
                if seq_info.min_value is not None:
                    sql += f" MINVALUE {seq_info.min_value}"
                if seq_info.max_value is not None:
                    sql += f" MAXVALUE {seq_info.max_value}"
                if seq_info.cycle_flag:
                    sql += " CYCLE"
                else:
                    sql += " NOCYCLE"
                if seq_info.cache_size:
                    sql += f" CACHE {seq_info.cache_size}"
                
                conn.execute(text(sql))
                conn.commit()
                
            elif db_type.lower() == 'postgresql':
                sql = f"""
                    CREATE SEQUENCE {schema}.{seq_info.sequence_name}
                    START {seq_info.start_value}
                    INCREMENT {seq_info.increment_by}
                """
                
                if seq_info.min_value is not None:
                    sql += f" MINVALUE {seq_info.min_value}"
                if seq_info.max_value is not None:
                    sql += f" MAXVALUE {seq_info.max_value}"
                if seq_info.cycle_flag:
                    sql += " CYCLE"
                if seq_info.cache_size:
                    sql += f" CACHE {seq_info.cache_size}"
                
                conn.execute(text(sql))
                conn.commit()
                
            elif db_type.lower() in ['sqlserver', 'mssql']:
                sql = f"""
                    CREATE SEQUENCE {schema}.{seq_info.sequence_name}
                    START WITH {seq_info.start_value}
                    INCREMENT BY {seq_info.increment_by}
                """
                
                if seq_info.min_value is not None:
                    sql += f" MINVALUE {seq_info.min_value}"
                if seq_info.max_value is not None:
                    sql += f" MAXVALUE {seq_info.max_value}"
                if seq_info.cycle_flag:
                    sql += " CYCLE"
                else:
                    sql += " NO CYCLE"
                if seq_info.cache_size:
                    sql += f" CACHE {seq_info.cache_size}"
                
                conn.execute(text(sql))
                conn.commit()
    
    def _create_table_structure(self, engine: Engine, db_type: str, schema: str, table_info):
        """Crea la estructura de una tabla (sin datos)"""
        # Reutilizar lógica del data_transfer existente
        self.data_transfer._create_table_if_not_exists(
            engine, db_type, schema, table_info.table_name, table_info
        )
    
    def _create_view(self, engine: Engine, db_type: str, schema: str, view_info: ViewInfo):
        """Crea una vista en la base de datos destino"""
        
        with engine.connect() as conn:
            # Adaptar la definición según el tipo de base de datos
            adapted_definition = self._adapt_view_definition(view_info.definition, db_type, schema)
            
            sql = f"CREATE VIEW {schema}.{view_info.view_name} AS {adapted_definition}"
            
            conn.execute(text(sql))
            conn.commit()
    
    def _create_index(self, engine: Engine, db_type: str, schema: str, index_info: IndexInfo):
        """Crea un índice en la base de datos destino"""
        
        with engine.connect() as conn:
            unique_clause = "UNIQUE " if index_info.is_unique else ""
            columns_str = ", ".join(index_info.columns)
            
            sql = f"""
                CREATE {unique_clause}INDEX {index_info.index_name} 
                ON {schema}.{index_info.table_name} ({columns_str})
            """
            
            conn.execute(text(sql))
            conn.commit()
    
    def _create_procedure(self, engine: Engine, db_type: str, schema: str, proc_info: ProcedureInfo):
        """Crea un procedimiento o función en la base de datos destino"""
        
        with engine.connect() as conn:
            # Adaptar la definición según el tipo de base de datos
            adapted_definition = self._adapt_procedure_definition(
                proc_info.definition, 
                proc_info.language,
                db_type, 
                schema, 
                proc_info.procedure_name
            )
            
            conn.execute(text(adapted_definition))
            conn.commit()
    
    def _create_trigger(self, engine: Engine, db_type: str, schema: str, trigger_info: TriggerInfo):
        """Crea un trigger en la base de datos destino"""
        
        with engine.connect() as conn:
            # Adaptar la definición según el tipo de base de datos
            adapted_definition = self._adapt_trigger_definition(
                trigger_info.definition,
                db_type,
                schema,
                trigger_info
            )
            
            conn.execute(text(adapted_definition))
            conn.commit()
    
    def _get_view_creation_order(self, schema_info: SchemaInfo) -> List[str]:
        """Obtiene el orden correcto de creación de vistas"""
        # Usar ordenamiento topológico para vistas también
        in_degree = {}
        graph = {}
        
        for view_name in schema_info.objects.views:
            in_degree[view_name] = 0
            graph[view_name] = []
        
        # Calcular dependencias entre vistas
        for view_name, view_info in schema_info.objects.views.items():
            for dep in view_info.dependencies:
                if dep in schema_info.objects.views:  # Solo dependencias de otras vistas
                    graph[dep].append(view_name)
                    in_degree[view_name] += 1
        
        # Ordenamiento topológico
        queue = [view for view, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for dependent in graph[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        return result
    
    def _is_system_index(self, index_info: IndexInfo) -> bool:
        """Determina si un índice es del sistema"""
        index_name = index_info.index_name.upper()
        return (index_name.startswith('PK_') or 
                index_name.startswith('FK_') or
                index_name.startswith('SYS_'))
    
    def _adapt_view_definition(self, definition: str, target_db_type: str, target_schema: str) -> str:
        """Adapta la definición de una vista al tipo de base de datos destino"""
        # Implementar adaptaciones específicas según el tipo de BD
        adapted = definition
        
        # Ejemplo: reemplazar nombres de esquema si es necesario
        # adapted = adapted.replace('old_schema.', f'{target_schema}.')
        
        return adapted
    
    def _adapt_procedure_definition(self, definition: str, language: str, target_db_type: str, 
                                  target_schema: str, proc_name: str) -> str:
        """Adapta la definición de un procedimiento al tipo de base de datos destino"""
        # Implementar adaptaciones específicas según el tipo de BD y lenguaje
        adapted = definition
        
        # Aquí se pueden hacer conversiones de sintaxis entre Oracle PL/SQL, T-SQL, PL/pgSQL, etc.
        
        return adapted
    
    def _adapt_trigger_definition(self, definition: str, target_db_type: str, 
                                target_schema: str, trigger_info: TriggerInfo) -> str:
        """Adapta la definición de un trigger al tipo de base de datos destino"""
        # Implementar adaptaciones específicas según el tipo de BD
        adapted = definition
        
        # Adaptar sintaxis de triggers entre diferentes BD
        
        return adapted