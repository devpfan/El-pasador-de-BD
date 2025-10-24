"""
Schema Analyzer - Analiza esquemas de bases de datos y extrae metadata completa
Incluye análisis de dependencias entre tablas
"""

import logging
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass
from database_manager import DatabaseManager
from sqlalchemy import text
from sqlalchemy.engine import Engine


@dataclass
class ColumnInfo:
    """Información de una columna"""
    name: str
    data_type: str
    is_nullable: bool
    default_value: Optional[str]
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    is_primary_key: bool = False
    is_foreign_key: bool = False


@dataclass
class ForeignKeyInfo:
    """Información de una llave foránea"""
    column_name: str
    referenced_schema: str
    referenced_table: str
    referenced_column: str
    constraint_name: str


@dataclass
class TableInfo:
    """Información completa de una tabla"""
    schema_name: str
    table_name: str
    columns: List[ColumnInfo]
    primary_keys: List[str]
    foreign_keys: List[ForeignKeyInfo]
    indexes: List[Dict[str, Any]]
    row_count: int
    dependencies: Set[str]  # Tablas de las que depende
    dependents: Set[str]    # Tablas que dependen de esta


@dataclass
class ViewInfo:
    """Información de una vista"""
    schema_name: str
    view_name: str
    definition: str
    is_updatable: bool
    columns: List[ColumnInfo]
    dependencies: Set[str]  # Tablas/vistas de las que depende


@dataclass
class SequenceInfo:
    """Información de una secuencia"""
    schema_name: str
    sequence_name: str
    start_value: int
    increment_by: int
    min_value: Optional[int]
    max_value: Optional[int]
    cycle_flag: bool
    cache_size: Optional[int]
    last_number: Optional[int]


@dataclass
class ProcedureInfo:
    """Información de un procedimiento almacenado"""
    schema_name: str
    procedure_name: str
    procedure_type: str  # PROCEDURE, FUNCTION, PACKAGE
    definition: str
    parameters: List[Dict[str, Any]]
    language: str
    dependencies: Set[str]  # Objetos de los que depende


@dataclass
class TriggerInfo:
    """Información de un trigger"""
    schema_name: str
    trigger_name: str
    table_name: str
    trigger_type: str  # BEFORE, AFTER, INSTEAD OF
    triggering_event: str  # INSERT, UPDATE, DELETE
    definition: str
    status: str  # ENABLED, DISABLED


@dataclass
class IndexInfo:
    """Información detallada de un índice"""
    schema_name: str
    index_name: str
    table_name: str
    index_type: str
    is_unique: bool
    columns: List[str]
    definition: str


@dataclass
class SchemaObjects:
    """Container para todos los objetos de un esquema"""
    tables: Dict[str, TableInfo]
    views: Dict[str, ViewInfo]
    sequences: Dict[str, SequenceInfo]
    procedures: Dict[str, ProcedureInfo]
    triggers: Dict[str, TriggerInfo]
    indexes: Dict[str, IndexInfo]


@dataclass
class SchemaInfo:
    """Información completa de un esquema"""
    schema_name: str
    objects: SchemaObjects
    dependency_order: List[str]  # Orden correcto para inserción de tablas
    creation_order: List[Tuple[str, str]]  # (tipo_objeto, nombre) en orden de creación


class SchemaAnalyzer:
    """Analiza esquemas y genera información completa de metadata y dependencias"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def analyze_schema(self, engine: Engine, db_type: str, schema_name: str, 
                      selected_tables: Optional[List[str]] = None,
                      include_views: bool = True, include_procedures: bool = True,
                      include_sequences: bool = True, include_triggers: bool = True,
                      include_indexes: bool = True) -> SchemaInfo:
        """Analiza un esquema completo y retorna toda la información necesaria"""
        
        self.logger.info(f"Analizando esquema completo: {schema_name}")
        
        # Inicializar contenedor de objetos
        schema_objects = SchemaObjects(
            tables={},
            views={},
            sequences={},
            procedures={},
            triggers={},
            indexes={}
        )
        
        schema_info = SchemaInfo(
            schema_name=schema_name,
            objects=schema_objects,
            dependency_order=[],
            creation_order=[]
        )
        
        # Analizar tablas
        all_tables = self.db_manager.get_tables(engine, db_type, schema_name)
        tables_to_analyze = selected_tables if selected_tables else all_tables
        
        for table_name in tables_to_analyze:
            if table_name in all_tables:
                table_info = self._analyze_table(engine, db_type, schema_name, table_name)
                schema_objects.tables[table_name] = table_info
        
        # Analizar otros objetos si están habilitados
        if include_sequences:
            sequences = self._analyze_sequences(engine, db_type, schema_name)
            schema_objects.sequences.update(sequences)
            
        if include_views:
            views = self._analyze_views(engine, db_type, schema_name)
            schema_objects.views.update(views)
            
        if include_procedures:
            procedures = self._analyze_procedures(engine, db_type, schema_name)
            schema_objects.procedures.update(procedures)
            
        if include_triggers:
            triggers = self._analyze_triggers(engine, db_type, schema_name)
            schema_objects.triggers.update(triggers)
            
        if include_indexes:
            indexes = self._analyze_indexes(engine, db_type, schema_name)
            schema_objects.indexes.update(indexes)
        
        # Calcular dependencias entre tablas
        self._calculate_dependencies(schema_info)
        
        # Determinar orden de inserción para tablas
        schema_info.dependency_order = self._calculate_insertion_order(schema_info)
        
        # Determinar orden de creación para todos los objetos
        schema_info.creation_order = self._calculate_creation_order(schema_info)
        
        return schema_info
    
    def _analyze_table(self, engine: Engine, db_type: str, schema_name: str, table_name: str) -> TableInfo:
        """Analiza una tabla individual"""
        
        self.logger.debug(f"Analizando tabla: {schema_name}.{table_name}")
        
        table_info = TableInfo(
            schema_name=schema_name,
            table_name=table_name,
            columns=[],
            primary_keys=[],
            foreign_keys=[],
            indexes=[],
            row_count=0,
            dependencies=set(),
            dependents=set()
        )
        
        try:
            with engine.connect() as conn:
                # Obtener información de columnas
                columns_info = self._get_columns_info(conn, db_type, schema_name, table_name)
                table_info.columns = columns_info
                
                # Obtener llaves primarias
                table_info.primary_keys = self._get_primary_keys(conn, db_type, schema_name, table_name)
                
                # Obtener llaves foráneas
                table_info.foreign_keys = self._get_foreign_keys(conn, db_type, schema_name, table_name)
                
                # Obtener índices
                table_info.indexes = self._get_indexes(conn, db_type, schema_name, table_name)
                
                # Obtener conteo de filas
                table_info.row_count = self._get_row_count(conn, db_type, schema_name, table_name)
                
                # Marcar columnas que son FK y PK
                self._mark_key_columns(table_info)
                
        except Exception as e:
            self.logger.error(f"Error analizando tabla {table_name}: {str(e)}")
            
        return table_info
    
    def _safe_row_access(self, row, index, default=None):
        """Acceso seguro a elementos de fila para evitar IndexError"""
        try:
            return row[index] if len(row) > index else default
        except (IndexError, TypeError):
            return default
    
    def _get_columns_info(self, conn, db_type: str, schema_name: str, table_name: str) -> List[ColumnInfo]:
        """Obtiene información detallada de las columnas"""
        columns = []
        
        try:
            if db_type.lower() == 'postgresql':
                query = """
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale,
                        udt_name
                    FROM information_schema.columns 
                    WHERE table_schema = :schema AND table_name = :table
                    ORDER BY ordinal_position
                """
                result = conn.execute(text(query), {"schema": schema_name, "table": table_name})
                
            elif db_type.lower() == 'oracle':
                query = """
                    SELECT 
                        column_name,
                        data_type,
                        nullable,
                        data_default,
                        data_length,
                        data_precision,
                        data_scale
                    FROM all_tab_columns 
                    WHERE owner = :schema AND table_name = :table
                    ORDER BY column_id
                """
                result = conn.execute(text(query), {"schema": schema_name, "table": table_name})
                
                for row in result:
                    try:
                        udt_name = self._safe_row_access(row, 7)
                        columns.append(ColumnInfo(
                            name=self._safe_row_access(row, 0, 'unknown'),
                            data_type=udt_name if udt_name else self._safe_row_access(row, 1, 'VARCHAR'),
                            is_nullable=self._safe_row_access(row, 2) == 'YES',
                            default_value=self._safe_row_access(row, 3),
                            max_length=self._safe_row_access(row, 4),
                            precision=self._safe_row_access(row, 5),
                            scale=self._safe_row_access(row, 6)
                        ))
                    except Exception as e:
                        self.logger.warning(f"Error procesando columna PostgreSQL: {e}, row: {row}")
                        continue
                    
            elif db_type.lower() == 'oracle':
                for row in result:
                    columns.append(ColumnInfo(
                        name=row[0],
                        data_type=row[1],
                        is_nullable=row[2] == 'Y',
                        default_value=row[3],
                        max_length=row[4],
                        precision=row[5],
                        scale=row[6]
                    ))
                    
            elif db_type.lower() == 'mysql':
                query = """
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale
                    FROM information_schema.columns 
                    WHERE table_schema = :schema AND table_name = :table
                    ORDER BY ordinal_position
                """
                result = conn.execute(text(query), {"schema": schema_name, "table": table_name})
                
                for row in result:
                    columns.append(ColumnInfo(
                        name=row[0],
                        data_type=row[1],
                        is_nullable=row[2] == 'YES',
                        default_value=row[3],
                        max_length=row[4],
                        precision=row[5],
                        scale=row[6]
                    ))
                    
            elif db_type.lower() == 'sqlserver':
                query = """
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale
                    FROM information_schema.columns 
                    WHERE table_schema = :schema AND table_name = :table
                    ORDER BY ordinal_position
                """
                result = conn.execute(text(query), {"schema": schema_name, "table": table_name})
                
                for row in result:
                    columns.append(ColumnInfo(
                        name=row[0],
                        data_type=row[1],
                        is_nullable=row[2] == 'YES',
                        default_value=row[3],
                        max_length=row[4],
                        precision=row[5],
                        scale=row[6]
                    ))
                    
            elif db_type.lower() == 'sqlite':
                result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                
                for row in result:
                    # Hacer más robusto el acceso a los datos
                    try:
                        columns.append(ColumnInfo(
                            name=row[1] if len(row) > 1 else 'unknown',
                            data_type=row[2] if len(row) > 2 else 'TEXT',
                            is_nullable=not bool(row[3]) if len(row) > 3 else True,
                            default_value=row[4] if len(row) > 4 else None,
                            is_primary_key=bool(row[5]) if len(row) > 5 else False
                        ))
                    except (IndexError, TypeError) as e:
                        self.logger.warning(f"Error procesando columna: {e}, row: {row}")
                        continue
                    
        except Exception as e:
            self.logger.error(f"Error obteniendo columnas: {str(e)}")
            
        return columns
    
    def _get_primary_keys(self, conn, db_type: str, schema_name: str, table_name: str) -> List[str]:
        """Obtiene las llaves primarias de la tabla"""
        primary_keys = []
        
        try:
            if db_type.lower() in ['postgresql', 'mysql', 'sqlserver']:
                query = """
                    SELECT column_name
                    FROM information_schema.key_column_usage
                    WHERE table_schema = :schema 
                        AND table_name = :table
                        AND constraint_name IN (
                            SELECT constraint_name
                            FROM information_schema.table_constraints
                            WHERE table_schema = :schema 
                                AND table_name = :table
                                AND constraint_type = 'PRIMARY KEY'
                        )
                    ORDER BY ordinal_position
                """
                result = conn.execute(text(query), {"schema": schema_name, "table": table_name})
                primary_keys = [row[0] for row in result]
                
            elif db_type.lower() == 'oracle':
                query = """
                    SELECT acc.column_name
                    FROM all_cons_columns acc
                    JOIN all_constraints ac ON acc.constraint_name = ac.constraint_name
                    WHERE ac.constraint_type = 'P'
                        AND acc.owner = :schema 
                        AND acc.table_name = :table
                    ORDER BY acc.position
                """
                result = conn.execute(text(query), {"schema": schema_name, "table": table_name})
                primary_keys = [row[0] for row in result]
                
            elif db_type.lower() == 'sqlite':
                result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                primary_keys = [row[1] for row in result if row[5]]
                
        except Exception as e:
            self.logger.error(f"Error obteniendo llaves primarias: {str(e)}")
            
        return primary_keys
    
    def _get_foreign_keys(self, conn, db_type: str, schema_name: str, table_name: str) -> List[ForeignKeyInfo]:
        """Obtiene las llaves foráneas de la tabla"""
        foreign_keys = []
        
        try:
            if db_type.lower() == 'postgresql':
                query = """
                    SELECT 
                        kcu.column_name,
                        ccu.table_schema AS foreign_table_schema,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name,
                        tc.constraint_name
                    FROM information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY' 
                        AND tc.table_schema = :schema 
                        AND tc.table_name = :table
                    ORDER BY kcu.ordinal_position
                """
                result = conn.execute(text(query), {"schema": schema_name, "table": table_name})
                
                for row in result:
                    foreign_keys.append(ForeignKeyInfo(
                        column_name=row[0],
                        referenced_schema=row[1],
                        referenced_table=row[2],
                        referenced_column=row[3],
                        constraint_name=row[4]
                    ))
                    
            elif db_type.lower() == 'mysql':
                query = """
                    SELECT 
                        column_name,
                        referenced_table_schema,
                        referenced_table_name,
                        referenced_column_name,
                        constraint_name
                    FROM information_schema.key_column_usage
                    WHERE table_schema = :schema 
                        AND table_name = :table
                        AND referenced_table_name IS NOT NULL
                    ORDER BY ordinal_position
                """
                result = conn.execute(text(query), {"schema": schema_name, "table": table_name})
                
                for row in result:
                    foreign_keys.append(ForeignKeyInfo(
                        column_name=row[0],
                        referenced_schema=row[1],
                        referenced_table=row[2],
                        referenced_column=row[3],
                        constraint_name=row[4]
                    ))
                    
            elif db_type.lower() == 'oracle':
                query = """
                    SELECT 
                        acc.column_name,
                        r_acc.owner AS foreign_table_schema,
                        r_acc.table_name AS foreign_table_name,
                        r_acc.column_name AS foreign_column_name,
                        acc.constraint_name
                    FROM all_cons_columns acc
                    JOIN all_constraints ac ON acc.constraint_name = ac.constraint_name
                    JOIN all_cons_columns r_acc ON ac.r_constraint_name = r_acc.constraint_name
                    WHERE ac.constraint_type = 'R'
                        AND acc.owner = :schema 
                        AND acc.table_name = :table
                    ORDER BY acc.position
                """
                result = conn.execute(text(query), {"schema": schema_name, "table": table_name})
                
                for row in result:
                    foreign_keys.append(ForeignKeyInfo(
                        column_name=row[0],
                        referenced_schema=row[1],
                        referenced_table=row[2],
                        referenced_column=row[3],
                        constraint_name=row[4]
                    ))
                    
            elif db_type.lower() == 'sqlite':
                result = conn.execute(text(f"PRAGMA foreign_key_list({table_name})"))
                
                for row in result:
                    foreign_keys.append(ForeignKeyInfo(
                        column_name=row[3],
                        referenced_schema=schema_name,  # SQLite no tiene esquemas múltiples
                        referenced_table=row[2],
                        referenced_column=row[4],
                        constraint_name=f"fk_{table_name}_{row[0]}"
                    ))
                    
        except Exception as e:
            self.logger.error(f"Error obteniendo llaves foráneas: {str(e)}")
            
        return foreign_keys
    
    def _get_indexes(self, conn, db_type: str, schema_name: str, table_name: str) -> List[Dict[str, Any]]:
        """Obtiene los índices de la tabla"""
        indexes = []
        
        try:
            if db_type.lower() == 'postgresql':
                query = """
                    SELECT 
                        indexname,
                        indexdef
                    FROM pg_indexes
                    WHERE schemaname = :schema AND tablename = :table
                """
                result = conn.execute(text(query), {"schema": schema_name, "table": table_name})
                
                for row in result:
                    indexes.append({
                        'name': row[0],
                        'definition': row[1]
                    })
                    
            elif db_type.lower() == 'sqlite':
                result = conn.execute(text(f"PRAGMA index_list({table_name})"))
                
                for row in result:
                    indexes.append({
                        'name': row[1],
                        'unique': bool(row[2])
                    })
                    
        except Exception as e:
            self.logger.error(f"Error obteniendo índices: {str(e)}")
            
        return indexes
    
    def _get_row_count(self, conn, db_type: str, schema_name: str, table_name: str) -> int:
        """Obtiene el conteo de filas de la tabla"""
        try:
            if db_type.lower() == 'sqlite':
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            else:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {schema_name}.{table_name}"))
                
            return result.fetchone()[0]
            
        except Exception as e:
            self.logger.error(f"Error obteniendo conteo de filas: {str(e)}")
            return 0
    
    def _mark_key_columns(self, table_info: TableInfo):
        """Marca las columnas que son PK o FK"""
        # Marcar primary keys
        for column in table_info.columns:
            if column.name in table_info.primary_keys:
                column.is_primary_key = True
        
        # Marcar foreign keys
        fk_columns = {fk.column_name for fk in table_info.foreign_keys}
        for column in table_info.columns:
            if column.name in fk_columns:
                column.is_foreign_key = True
    
    def _calculate_dependencies(self, schema_info: SchemaInfo):
        """Calcula las dependencias entre tablas del esquema"""
        
        for table_name, table_info in schema_info.objects.tables.items():
            for fk in table_info.foreign_keys:
                referenced_table = fk.referenced_table
                
                # Solo considerar dependencias dentro del mismo esquema
                if (fk.referenced_schema == schema_info.schema_name and 
                    referenced_table in schema_info.objects.tables):
                    
                    # Esta tabla depende de la tabla referenciada
                    table_info.dependencies.add(referenced_table)
                    
                    # La tabla referenciada tiene esta tabla como dependiente
                    schema_info.objects.tables[referenced_table].dependents.add(table_name)
    
    def _calculate_insertion_order(self, schema_info: SchemaInfo) -> List[str]:
        """Calcula el orden correcto de inserción usando ordenamiento topológico"""
        
        # Implementación del algoritmo de Kahn para ordenamiento topológico
        in_degree = {}
        graph = {}
        
        # Inicializar contadores de grado de entrada
        for table_name in schema_info.objects.tables:
            in_degree[table_name] = 0
            graph[table_name] = list(schema_info.objects.tables[table_name].dependents)
        
        # Calcular grados de entrada
        for table_name, table_info in schema_info.objects.tables.items():
            for dependency in table_info.dependencies:
                if dependency in in_degree:
                    in_degree[table_name] += 1
        
        # Cola con nodos sin dependencias
        queue = [table for table, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            # Tomar un nodo sin dependencias
            current = queue.pop(0)
            result.append(current)
            
            # Para cada dependiente de este nodo
            for dependent in graph[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # Verificar si hay ciclos (dependencias circulares)
        if len(result) != len(schema_info.objects.tables):
            self.logger.warning("Se detectaron dependencias circulares en el esquema")
            # Agregar las tablas restantes al final
            remaining = set(schema_info.objects.tables.keys()) - set(result)
            result.extend(list(remaining))
        
        return result
    
    def get_table_dependencies(self, schema_info: SchemaInfo, table_name: str) -> Dict[str, List[str]]:
        """Obtiene las dependencias directas e indirectas de una tabla"""
        if table_name not in schema_info.objects.tables:
            return {"direct": [], "indirect": []}
        
        table = schema_info.objects.tables[table_name]
        direct_deps = list(table.dependencies)
        
        # Calcular dependencias indirectas
        indirect_deps = set()
        to_check = list(direct_deps)
        checked = set()
        
        while to_check:
            current = to_check.pop(0)
            if current in checked or current not in schema_info.objects.tables:
                continue
                
            checked.add(current)
            for dep in schema_info.objects.tables[current].dependencies:
                if dep not in direct_deps and dep != table_name:
                    indirect_deps.add(dep)
                    to_check.append(dep)
        
        return {
            "direct": direct_deps,
            "indirect": list(indirect_deps)
        }
    
    def validate_schema_integrity(self, schema_info: SchemaInfo) -> List[Dict[str, str]]:
        """Valida la integridad del esquema y retorna problemas encontrados"""
        issues = []
        
        for table_name, table_info in schema_info.objects.tables.items():
            # Verificar que las tablas referenciadas existen
            for fk in table_info.foreign_keys:
                if (fk.referenced_schema == schema_info.schema_name and
                    fk.referenced_table not in schema_info.objects.tables):
                    issues.append({
                        "type": "missing_reference",
                        "table": table_name,
                        "description": f"Tabla {fk.referenced_table} referenciada por FK no está incluida"
                    })
            
            # Verificar que las tablas tienen llaves primarias
            if not table_info.primary_keys:
                issues.append({
                    "type": "no_primary_key",
                    "table": table_name,
                    "description": "Tabla sin llave primaria definida"
                })
        
        return issues

    def _analyze_sequences(self, engine: Engine, db_type: str, schema_name: str) -> Dict[str, SequenceInfo]:
        """Analiza todas las secuencias del esquema"""
        self.logger.info(f"Analizando secuencias en esquema: {schema_name}")
        sequences = {}
        
        try:
            with engine.connect() as conn:
                if db_type.lower() == 'oracle':
                    query = text("""
                        SELECT sequence_name, min_value, max_value, increment_by, 
                               cycle_flag, order_flag, cache_size, last_number
                        FROM all_sequences 
                        WHERE sequence_owner = :schema_name
                    """)
                    result = conn.execute(query, {"schema_name": schema_name.upper()})
                    
                    for row in result:
                        sequences[row[0]] = SequenceInfo(
                            schema_name=schema_name,
                            sequence_name=row[0],
                            start_value=1,  # Oracle no guarda start_value, usar min_value o 1
                            increment_by=row[3] or 1,
                            min_value=row[1],
                            max_value=row[2],
                            cycle_flag=row[4] == 'Y',
                            cache_size=row[6],
                            last_number=row[7]
                        )
                
                elif db_type.lower() == 'postgresql':
                    query = text("""
                        SELECT sequencename as sequence_name, start_value, increment_by, 
                               min_value, max_value, cycle, cache_size
                        FROM pg_sequences 
                        WHERE schemaname = :schema_name
                    """)
                    result = conn.execute(query, {"schema_name": schema_name})
                    
                    for row in result:
                        sequences[row[0]] = SequenceInfo(
                            schema_name=schema_name,
                            sequence_name=row[0],
                            start_value=row[1] or 1,
                            increment_by=row[2] or 1,
                            min_value=row[3],
                            max_value=row[4],
                            cycle_flag=bool(row[5]),
                            cache_size=row[6],
                            last_number=None
                        )
                
                elif db_type.lower() in ['mysql', 'mariadb']:
                    # MySQL usa AUTO_INCREMENT, no secuencias tradicionales
                    # Podríamos analizar las tablas con AUTO_INCREMENT
                    pass
                    
                elif db_type.lower() in ['sqlserver', 'mssql']:
                    query = text("""
                        SELECT name, start_value, increment, minimum_value, 
                               maximum_value, is_cycling, cache_size, current_value
                        FROM sys.sequences s
                        INNER JOIN sys.schemas sch ON s.schema_id = sch.schema_id
                        WHERE sch.name = :schema_name
                    """)
                    result = conn.execute(query, {"schema_name": schema_name})
                    
                    for row in result:
                        sequences[row[0]] = SequenceInfo(
                            schema_name=schema_name,
                            sequence_name=row[0],
                            start_value=row[1],
                            increment_by=row[2],
                            min_value=row[3],
                            max_value=row[4],
                            cycle_flag=bool(row[5]),
                            cache_size=row[6],
                            last_number=row[7]
                        )
                        
        except Exception as e:
            self.logger.error(f"Error analizando secuencias: {str(e)}")
            
        return sequences

    def _analyze_views(self, engine: Engine, db_type: str, schema_name: str) -> Dict[str, ViewInfo]:
        """Analiza todas las vistas del esquema"""
        self.logger.info(f"Analizando vistas en esquema: {schema_name}")
        views = {}
        
        try:
            with engine.connect() as conn:
                if db_type.lower() == 'oracle':
                    # Obtener definición de vistas
                    query = text("""
                        SELECT view_name, text, read_only
                        FROM all_views 
                        WHERE owner = :schema_name
                    """)
                    result = conn.execute(query, {"schema_name": schema_name.upper()})
                    
                    for row in result:
                        view_name = row[0]
                        definition = row[1]
                        is_updatable = row[2] != 'Y'
                        
                        # Obtener columnas de la vista
                        columns = self._get_view_columns(conn, db_type, schema_name, view_name)
                        
                        # Analizar dependencias (tablas/vistas que usa)
                        dependencies = self._get_view_dependencies(conn, db_type, schema_name, view_name)
                        
                        views[view_name] = ViewInfo(
                            schema_name=schema_name,
                            view_name=view_name,
                            definition=definition,
                            is_updatable=is_updatable,
                            columns=columns,
                            dependencies=dependencies
                        )
                
                elif db_type.lower() == 'postgresql':
                    query = text("""
                        SELECT table_name as view_name, view_definition, is_updatable
                        FROM information_schema.views 
                        WHERE table_schema = :schema_name
                    """)
                    result = conn.execute(query, {"schema_name": schema_name})
                    
                    for row in result:
                        view_name = row[0]
                        definition = row[1]
                        is_updatable = row[2] == 'YES'
                        
                        columns = self._get_view_columns(conn, db_type, schema_name, view_name)
                        dependencies = self._get_view_dependencies(conn, db_type, schema_name, view_name)
                        
                        views[view_name] = ViewInfo(
                            schema_name=schema_name,
                            view_name=view_name,
                            definition=definition,
                            is_updatable=is_updatable,
                            columns=columns,
                            dependencies=dependencies
                        )
                
                elif db_type.lower() in ['mysql', 'mariadb']:
                    query = text("""
                        SELECT table_name as view_name, view_definition, is_updatable
                        FROM information_schema.views 
                        WHERE table_schema = :schema_name
                    """)
                    result = conn.execute(query, {"schema_name": schema_name})
                    
                    for row in result:
                        view_name = row[0]
                        definition = row[1]
                        is_updatable = row[2] == 'YES'
                        
                        columns = self._get_view_columns(conn, db_type, schema_name, view_name)
                        dependencies = self._get_view_dependencies(conn, db_type, schema_name, view_name)
                        
                        views[view_name] = ViewInfo(
                            schema_name=schema_name,
                            view_name=view_name,
                            definition=definition,
                            is_updatable=is_updatable,
                            columns=columns,
                            dependencies=dependencies
                        )
                
                elif db_type.lower() in ['sqlserver', 'mssql']:
                    query = text("""
                        SELECT v.name as view_name, m.definition, 
                               CASE WHEN v.is_updatable = 1 THEN 'YES' ELSE 'NO' END as is_updatable
                        FROM sys.views v
                        INNER JOIN sys.schemas s ON v.schema_id = s.schema_id
                        INNER JOIN sys.sql_modules m ON v.object_id = m.object_id
                        WHERE s.name = :schema_name
                    """)
                    result = conn.execute(query, {"schema_name": schema_name})
                    
                    for row in result:
                        view_name = row[0]
                        definition = row[1]
                        is_updatable = row[2] == 'YES'
                        
                        columns = self._get_view_columns(conn, db_type, schema_name, view_name)
                        dependencies = self._get_view_dependencies(conn, db_type, schema_name, view_name)
                        
                        views[view_name] = ViewInfo(
                            schema_name=schema_name,
                            view_name=view_name,
                            definition=definition,
                            is_updatable=is_updatable,
                            columns=columns,
                            dependencies=dependencies
                        )
                        
        except Exception as e:
            self.logger.error(f"Error analizando vistas: {str(e)}")
            
        return views

    def _analyze_procedures(self, engine: Engine, db_type: str, schema_name: str) -> Dict[str, ProcedureInfo]:
        """Analiza todos los procedimientos, funciones y paquetes del esquema"""
        self.logger.info(f"Analizando procedimientos en esquema: {schema_name}")
        procedures = {}
        
        try:
            with engine.connect() as conn:
                if db_type.lower() == 'oracle':
                    # Procedimientos y funciones
                    query = text("""
                        SELECT object_name, object_type, status
                        FROM all_objects 
                        WHERE owner = :schema_name 
                        AND object_type IN ('PROCEDURE', 'FUNCTION', 'PACKAGE', 'PACKAGE BODY')
                    """)
                    result = conn.execute(query, {"schema_name": schema_name.upper()})
                    
                    for row in result:
                        proc_name = row[0]
                        proc_type = row[1]
                        
                        # Obtener definición
                        definition = self._get_procedure_definition(conn, db_type, schema_name, proc_name, proc_type)
                        
                        # Obtener parámetros
                        parameters = self._get_procedure_parameters(conn, db_type, schema_name, proc_name)
                        
                        # Analizar dependencias
                        dependencies = self._get_procedure_dependencies(conn, db_type, schema_name, proc_name)
                        
                        procedures[proc_name] = ProcedureInfo(
                            schema_name=schema_name,
                            procedure_name=proc_name,
                            procedure_type=proc_type,
                            definition=definition,
                            parameters=parameters,
                            language='PLSQL',
                            dependencies=dependencies
                        )
                
                elif db_type.lower() == 'postgresql':
                    query = text("""
                        SELECT p.proname as procedure_name, 
                               CASE WHEN p.prokind = 'f' THEN 'FUNCTION' 
                                    WHEN p.prokind = 'p' THEN 'PROCEDURE' 
                                    ELSE 'FUNCTION' END as procedure_type,
                               pg_get_functiondef(p.oid) as definition,
                               l.lanname as language
                        FROM pg_proc p
                        INNER JOIN pg_namespace n ON p.pronamespace = n.oid
                        INNER JOIN pg_language l ON p.prolang = l.oid
                        WHERE n.nspname = :schema_name
                    """)
                    result = conn.execute(query, {"schema_name": schema_name})
                    
                    for row in result:
                        proc_name = row[0]
                        proc_type = row[1]
                        definition = row[2]
                        language = row[3]
                        
                        parameters = self._get_procedure_parameters(conn, db_type, schema_name, proc_name)
                        dependencies = self._get_procedure_dependencies(conn, db_type, schema_name, proc_name)
                        
                        procedures[proc_name] = ProcedureInfo(
                            schema_name=schema_name,
                            procedure_name=proc_name,
                            procedure_type=proc_type,
                            definition=definition,
                            parameters=parameters,
                            language=language.upper(),
                            dependencies=dependencies
                        )
                
                elif db_type.lower() in ['sqlserver', 'mssql']:
                    query = text("""
                        SELECT p.name as procedure_name, p.type_desc as procedure_type, 
                               m.definition, 'T-SQL' as language
                        FROM sys.procedures p
                        INNER JOIN sys.schemas s ON p.schema_id = s.schema_id
                        INNER JOIN sys.sql_modules m ON p.object_id = m.object_id
                        WHERE s.name = :schema_name
                        
                        UNION ALL
                        
                        SELECT f.name as procedure_name, f.type_desc as procedure_type, 
                               m.definition, 'T-SQL' as language
                        FROM sys.objects f
                        INNER JOIN sys.schemas s ON f.schema_id = s.schema_id
                        INNER JOIN sys.sql_modules m ON f.object_id = m.object_id
                        WHERE s.name = :schema_name AND f.type IN ('FN', 'IF', 'TF')
                    """)
                    result = conn.execute(query, {"schema_name": schema_name})
                    
                    for row in result:
                        proc_name = row[0]
                        proc_type = row[1]
                        definition = row[2]
                        language = row[3]
                        
                        parameters = self._get_procedure_parameters(conn, db_type, schema_name, proc_name)
                        dependencies = self._get_procedure_dependencies(conn, db_type, schema_name, proc_name)
                        
                        procedures[proc_name] = ProcedureInfo(
                            schema_name=schema_name,
                            procedure_name=proc_name,
                            procedure_type=proc_type,
                            definition=definition,
                            parameters=parameters,
                            language=language,
                            dependencies=dependencies
                        )
                        
        except Exception as e:
            self.logger.error(f"Error analizando procedimientos: {str(e)}")
            
        return procedures

    def _analyze_triggers(self, engine: Engine, db_type: str, schema_name: str) -> Dict[str, TriggerInfo]:
        """Analiza todos los triggers del esquema"""
        self.logger.info(f"Analizando triggers en esquema: {schema_name}")
        triggers = {}
        
        try:
            with engine.connect() as conn:
                if db_type.lower() == 'oracle':
                    query = text("""
                        SELECT trigger_name, table_name, trigger_type, triggering_event, 
                               status, trigger_body
                        FROM all_triggers 
                        WHERE owner = :schema_name
                    """)
                    result = conn.execute(query, {"schema_name": schema_name.upper()})
                    
                    for row in result:
                        triggers[row[0]] = TriggerInfo(
                            schema_name=schema_name,
                            trigger_name=row[0],
                            table_name=row[1],
                            trigger_type=row[2],
                            triggering_event=row[3],
                            definition=row[5],
                            status=row[4]
                        )
                
                elif db_type.lower() == 'postgresql':
                    query = text("""
                        SELECT t.tgname as trigger_name, 
                               c.relname as table_name,
                               CASE 
                                   WHEN t.tgtype & 2 = 2 THEN 'BEFORE'
                                   WHEN t.tgtype & 4 = 4 THEN 'AFTER'
                                   ELSE 'INSTEAD OF'
                               END as trigger_type,
                               CASE 
                                   WHEN t.tgtype & 4 = 4 THEN 'INSERT'
                                   WHEN t.tgtype & 8 = 8 THEN 'DELETE'
                                   WHEN t.tgtype & 16 = 16 THEN 'UPDATE'
                                   ELSE 'MULTIPLE'
                               END as triggering_event,
                               pg_get_triggerdef(t.oid) as definition,
                               CASE WHEN t.tgenabled = 'O' THEN 'ENABLED' ELSE 'DISABLED' END as status
                        FROM pg_trigger t
                        INNER JOIN pg_class c ON t.tgrelid = c.oid
                        INNER JOIN pg_namespace n ON c.relnamespace = n.oid
                        WHERE n.nspname = :schema_name AND NOT t.tgisinternal
                    """)
                    result = conn.execute(query, {"schema_name": schema_name})
                    
                    for row in result:
                        triggers[row[0]] = TriggerInfo(
                            schema_name=schema_name,
                            trigger_name=row[0],
                            table_name=row[1],
                            trigger_type=row[2],
                            triggering_event=row[3],
                            definition=row[4],
                            status=row[5]
                        )
                
                elif db_type.lower() in ['sqlserver', 'mssql']:
                    query = text("""
                        SELECT tr.name as trigger_name, t.name as table_name,
                               CASE WHEN tr.is_instead_of_trigger = 1 THEN 'INSTEAD OF' ELSE 'AFTER' END as trigger_type,
                               'MULTIPLE' as triggering_event,  -- SQL Server puede tener múltiples eventos
                               m.definition,
                               CASE WHEN tr.is_disabled = 0 THEN 'ENABLED' ELSE 'DISABLED' END as status
                        FROM sys.triggers tr
                        INNER JOIN sys.tables t ON tr.parent_id = t.object_id
                        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                        INNER JOIN sys.sql_modules m ON tr.object_id = m.object_id
                        WHERE s.name = :schema_name
                    """)
                    result = conn.execute(query, {"schema_name": schema_name})
                    
                    for row in result:
                        triggers[row[0]] = TriggerInfo(
                            schema_name=schema_name,
                            trigger_name=row[0],
                            table_name=row[1],
                            trigger_type=row[2],
                            triggering_event=row[3],
                            definition=row[4],
                            status=row[5]
                        )
                        
        except Exception as e:
            self.logger.error(f"Error analizando triggers: {str(e)}")
            
        return triggers

    def _analyze_indexes(self, engine: Engine, db_type: str, schema_name: str) -> Dict[str, IndexInfo]:
        """Analiza todos los índices del esquema"""
        self.logger.info(f"Analizando índices en esquema: {schema_name}")
        indexes = {}
        
        try:
            with engine.connect() as conn:
                if db_type.lower() == 'oracle':
                    query = text("""
                        SELECT i.index_name, i.table_name, i.index_type, i.uniqueness,
                               LISTAGG(ic.column_name, ', ') WITHIN GROUP (ORDER BY ic.column_position) as columns
                        FROM all_indexes i
                        INNER JOIN all_ind_columns ic ON i.index_name = ic.index_name AND i.owner = ic.index_owner
                        WHERE i.owner = :schema_name
                        GROUP BY i.index_name, i.table_name, i.index_type, i.uniqueness
                    """)
                    result = conn.execute(query, {"schema_name": schema_name.upper()})
                    
                    for row in result:
                        indexes[row[0]] = IndexInfo(
                            schema_name=schema_name,
                            index_name=row[0],
                            table_name=row[1],
                            index_type=row[2],
                            is_unique=row[3] == 'UNIQUE',
                            columns=row[4].split(', ') if row[4] else [],
                            definition=f"CREATE {'UNIQUE ' if row[3] == 'UNIQUE' else ''}INDEX {row[0]} ON {row[1]} ({row[4]})"
                        )
                
                elif db_type.lower() == 'postgresql':
                    query = text("""
                        SELECT i.indexname as index_name, i.tablename as table_name,
                               am.amname as index_type, idx.indisunique as is_unique,
                               array_to_string(array_agg(a.attname ORDER BY array_position(idx.indkey, a.attnum)), ', ') as columns,
                               pg_get_indexdef(idx.indexrelid) as definition
                        FROM pg_indexes i
                        INNER JOIN pg_class c ON i.indexname = c.relname
                        INNER JOIN pg_index idx ON c.oid = idx.indexrelid
                        INNER JOIN pg_class t ON idx.indrelid = t.oid
                        INNER JOIN pg_am am ON c.relam = am.oid
                        INNER JOIN pg_attribute a ON t.oid = a.attrelid AND a.attnum = ANY(idx.indkey)
                        WHERE i.schemaname = :schema_name
                        GROUP BY i.indexname, i.tablename, am.amname, idx.indisunique, idx.indexrelid
                    """)
                    result = conn.execute(query, {"schema_name": schema_name})
                    
                    for row in result:
                        indexes[row[0]] = IndexInfo(
                            schema_name=schema_name,
                            index_name=row[0],
                            table_name=row[1],
                            index_type=row[2],
                            is_unique=bool(row[3]),
                            columns=row[4].split(', ') if row[4] else [],
                            definition=row[5]
                        )
                        
        except Exception as e:
            self.logger.error(f"Error analizando índices: {str(e)}")
            
        return indexes

    def _calculate_creation_order(self, schema_info: SchemaInfo) -> List[Tuple[str, str]]:
        """Calcula el orden correcto de creación para todos los objetos"""
        creation_order = []
        
        # 1. Secuencias (pueden ser usadas por tablas)
        for seq_name in schema_info.objects.sequences:
            creation_order.append(('SEQUENCE', seq_name))
        
        # 2. Tablas en orden de dependencias
        for table_name in schema_info.dependency_order:
            creation_order.append(('TABLE', table_name))
        
        # 3. Vistas (dependen de tablas)
        # Ordenar vistas por dependencias también
        view_order = self._calculate_view_order(schema_info)
        for view_name in view_order:
            creation_order.append(('VIEW', view_name))
        
        # 4. Índices (después de tablas)
        for index_name, index_info in schema_info.objects.indexes.items():
            # Solo incluir índices no automáticos (no PK/FK)
            if not self._is_system_index(index_info):
                creation_order.append(('INDEX', index_name))
        
        # 5. Procedimientos y funciones
        for proc_name in schema_info.objects.procedures:
            creation_order.append(('PROCEDURE', proc_name))
        
        # 6. Triggers (al final, después de todo lo demás)
        for trigger_name in schema_info.objects.triggers:
            creation_order.append(('TRIGGER', trigger_name))
        
        return creation_order

    def _calculate_view_order(self, schema_info: SchemaInfo) -> List[str]:
        """Calcula el orden de creación de vistas basado en dependencias"""
        # Similar al ordenamiento topológico para tablas
        in_degree = {}
        graph = {}
        
        # Inicializar
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
        """Determina si un índice es del sistema (PK, FK automáticos)"""
        index_name = index_info.index_name.upper()
        return (index_name.startswith('PK_') or 
                index_name.startswith('FK_') or
                index_name.startswith('SYS_'))

    # Métodos auxiliares para obtener información específica
    def _get_view_columns(self, conn, db_type: str, schema_name: str, view_name: str) -> List[ColumnInfo]:
        """Obtiene las columnas de una vista"""
        columns = []
        try:
            if db_type.lower() == 'oracle':
                query = text("""
                    SELECT column_name, data_type, nullable, data_length, data_precision, data_scale
                    FROM all_tab_columns 
                    WHERE owner = :schema_name AND table_name = :view_name
                    ORDER BY column_id
                """)
                result = conn.execute(query, {"schema_name": schema_name.upper(), "view_name": view_name.upper()})
                
                for row in result:
                    columns.append(ColumnInfo(
                        name=row[0],
                        data_type=row[1],
                        is_nullable=row[2] == 'Y',
                        default_value=None,
                        max_length=row[3],
                        precision=row[4],
                        scale=row[5]
                    ))
        except Exception as e:
            self.logger.error(f"Error obteniendo columnas de vista {view_name}: {str(e)}")
        
        return columns

    def _get_view_dependencies(self, conn, db_type: str, schema_name: str, view_name: str) -> Set[str]:
        """Obtiene las dependencias de una vista"""
        dependencies = set()
        try:
            if db_type.lower() == 'oracle':
                query = text("""
                    SELECT referenced_name
                    FROM all_dependencies 
                    WHERE owner = :schema_name 
                    AND name = :view_name
                    AND referenced_type IN ('TABLE', 'VIEW')
                """)
                result = conn.execute(query, {"schema_name": schema_name.upper(), "view_name": view_name.upper()})
                
                for row in result:
                    dependencies.add(row[0])
        except Exception as e:
            self.logger.error(f"Error obteniendo dependencias de vista {view_name}: {str(e)}")
        
        return dependencies

    def _get_procedure_definition(self, conn, db_type: str, schema_name: str, proc_name: str, proc_type: str) -> str:
        """Obtiene la definición completa de un procedimiento"""
        try:
            if db_type.lower() == 'oracle':
                query = text("""
                    SELECT text
                    FROM all_source 
                    WHERE owner = :schema_name 
                    AND name = :proc_name 
                    AND type = :proc_type
                    ORDER BY line
                """)
                result = conn.execute(query, {
                    "schema_name": schema_name.upper(), 
                    "proc_name": proc_name.upper(),
                    "proc_type": proc_type.upper()
                })
                
                lines = [row[0] for row in result]
                return ''.join(lines)
        except Exception as e:
            self.logger.error(f"Error obteniendo definición de {proc_name}: {str(e)}")
        
        return ""

    def _get_procedure_parameters(self, conn, db_type: str, schema_name: str, proc_name: str) -> List[Dict[str, Any]]:
        """Obtiene los parámetros de un procedimiento"""
        parameters = []
        try:
            if db_type.lower() == 'oracle':
                query = text("""
                    SELECT argument_name, data_type, in_out, position
                    FROM all_arguments 
                    WHERE owner = :schema_name 
                    AND object_name = :proc_name
                    AND argument_name IS NOT NULL
                    ORDER BY position
                """)
                result = conn.execute(query, {"schema_name": schema_name.upper(), "proc_name": proc_name.upper()})
                
                for row in result:
                    parameters.append({
                        'name': row[0],
                        'data_type': row[1],
                        'direction': row[2],
                        'position': row[3]
                    })
        except Exception as e:
            self.logger.error(f"Error obteniendo parámetros de {proc_name}: {str(e)}")
        
        return parameters

    def _get_procedure_dependencies(self, conn, db_type: str, schema_name: str, proc_name: str) -> Set[str]:
        """Obtiene las dependencias de un procedimiento"""
        dependencies = set()
        try:
            if db_type.lower() == 'oracle':
                query = text("""
                    SELECT referenced_name
                    FROM all_dependencies 
                    WHERE owner = :schema_name 
                    AND name = :proc_name
                    AND referenced_type IN ('TABLE', 'VIEW', 'SEQUENCE', 'FUNCTION', 'PROCEDURE')
                """)
                result = conn.execute(query, {"schema_name": schema_name.upper(), "proc_name": proc_name.upper()})
                
                for row in result:
                    dependencies.add(row[0])
        except Exception as e:
            self.logger.error(f"Error obteniendo dependencias de {proc_name}: {str(e)}")
        
        return dependencies