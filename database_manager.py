"""
Database Manager - Maneja conexiones a diferentes tipos de bases de datos
Soporta: PostgreSQL, MySQL, SQL Server, SQLite
"""

import sqlite3
import logging
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.engine import Engine
import psycopg2
import mysql.connector
import pymssql
try:
    import cx_Oracle
except ImportError:
    cx_Oracle = None


class DatabaseManager:
    """Clase para manejar conexiones a diferentes tipos de bases de datos"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.engines: Dict[str, Engine] = {}
        
    def create_connection_string(self, db_type: str, config: Dict[str, Any]) -> str:
        """Crea la cadena de conexión según el tipo de BD"""
        
        if db_type.lower() == 'postgresql':
            return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config.get('port', 5432)}/{config['database']}"
            
        elif db_type.lower() == 'mysql':
            return f"mysql+mysqlconnector://{config['user']}:{config['password']}@{config['host']}:{config.get('port', 3306)}/{config['database']}"
            
        elif db_type.lower() == 'sqlserver':
            return f"mssql+pymssql://{config['user']}:{config['password']}@{config['host']}:{config.get('port', 1433)}/{config['database']}"
            
        elif db_type.lower() == 'oracle':
            # Oracle puede usar service name o SID
            service_name = config['database']
            return f"oracle+cx_oracle://{config['user']}:{config['password']}@{config['host']}:{config.get('port', 1521)}/{service_name}"
            
        elif db_type.lower() == 'sqlite':
            return f"sqlite:///{config['database']}"
            
        else:
            raise ValueError(f"Tipo de base de datos no soportado: {db_type}")
    
    def test_connection(self, db_type: str, config: Dict[str, Any]) -> Tuple[bool, str]:
        """Prueba la conexión a la base de datos"""
        try:
            connection_string = self.create_connection_string(db_type, config)
            engine = create_engine(connection_string, echo=False)
            
            # Intentar conectar
            with engine.connect() as conn:
                if db_type.lower() == 'postgresql':
                    conn.execute(text("SELECT 1"))
                elif db_type.lower() == 'mysql':
                    conn.execute(text("SELECT 1"))
                elif db_type.lower() == 'sqlserver':
                    conn.execute(text("SELECT 1"))
                elif db_type.lower() == 'oracle':
                    conn.execute(text("SELECT 1 FROM DUAL"))
                elif db_type.lower() == 'sqlite':
                    conn.execute(text("SELECT 1"))
            
            engine.dispose()
            return True, "Conexión exitosa"
            
        except Exception as e:
            self.logger.error(f"Error al conectar: {str(e)}")
            return False, f"Error: {str(e)}"
    
    def get_engine(self, connection_id: str, db_type: str, config: Dict[str, Any]) -> Engine:
        """Obtiene o crea un engine SQLAlchemy para la conexión"""
        if connection_id in self.engines:
            return self.engines[connection_id]
            
        connection_string = self.create_connection_string(db_type, config)
        engine = create_engine(connection_string, echo=False, pool_pre_ping=True)
        self.engines[connection_id] = engine
        return engine
    
    def get_schemas(self, engine: Engine, db_type: str) -> List[str]:
        """Obtiene la lista de esquemas disponibles"""
        schemas = []
        
        try:
            with engine.connect() as conn:
                if db_type.lower() == 'postgresql':
                    result = conn.execute(text("""
                        SELECT schema_name 
                        FROM information_schema.schemata 
                        WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                        ORDER BY schema_name
                    """))
                    
                elif db_type.lower() == 'mysql':
                    result = conn.execute(text("""
                        SELECT schema_name 
                        FROM information_schema.schemata 
                        WHERE schema_name NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
                        ORDER BY schema_name
                    """))
                    
                elif db_type.lower() == 'sqlserver':
                    result = conn.execute(text("""
                        SELECT name 
                        FROM sys.schemas 
                        WHERE name NOT IN ('dbo', 'guest', 'INFORMATION_SCHEMA', 'sys', 'db_owner', 'db_accessadmin', 
                                         'db_securityadmin', 'db_ddladmin', 'db_backupoperator', 'db_datareader', 
                                         'db_datawriter', 'db_denydatareader', 'db_denydatawriter')
                        ORDER BY name
                    """))
                    
                elif db_type.lower() == 'oracle':
                    result = conn.execute(text("""
                        SELECT username 
                        FROM all_users 
                        WHERE username NOT IN ('SYS', 'SYSTEM', 'DBSNMP', 'SYSMAN', 'OUTLN', 'MGMT_VIEW', 
                                             'DIP', 'ORACLE_OCM', 'APPQOSSYS', 'WMSYS', 'EXFSYS', 'CTXSYS', 
                                             'XDB', 'ANONYMOUS', 'HR', 'OE', 'PM', 'IX', 'SH', 'BI')
                        ORDER BY username
                    """))
                    
                elif db_type.lower() == 'sqlite':
                    # SQLite no tiene esquemas múltiples, retorna 'main'
                    return ['main']
                
                schemas = [row[0] for row in result]
                
        except Exception as e:
            self.logger.error(f"Error al obtener esquemas: {str(e)}")
            
        return schemas
    
    def get_tables(self, engine: Engine, db_type: str, schema: str) -> List[str]:
        """Obtiene la lista de tablas en un esquema"""
        tables = []
        
        try:
            with engine.connect() as conn:
                if db_type.lower() == 'postgresql':
                    result = conn.execute(text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = :schema AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                    """), {"schema": schema})
                    
                elif db_type.lower() == 'mysql':
                    result = conn.execute(text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = :schema AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                    """), {"schema": schema})
                    
                elif db_type.lower() == 'sqlserver':
                    result = conn.execute(text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = :schema AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                    """), {"schema": schema})
                    
                elif db_type.lower() == 'oracle':
                    result = conn.execute(text("""
                        SELECT table_name 
                        FROM all_tables 
                        WHERE owner = :schema 
                        ORDER BY table_name
                    """), {"schema": schema})
                    
                elif db_type.lower() == 'sqlite':
                    result = conn.execute(text("""
                        SELECT name 
                        FROM sqlite_master 
                        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                        ORDER BY name
                    """))
                
                tables = [row[0] for row in result]
                
        except Exception as e:
            self.logger.error(f"Error al obtener tablas: {str(e)}")
            
        return tables
    
    def get_table_info(self, engine: Engine, db_type: str, schema: str, table: str) -> Dict[str, Any]:
        """Obtiene información detallada de una tabla"""
        table_info = {
            'columns': [],
            'primary_keys': [],
            'foreign_keys': [],
            'indexes': [],
            'row_count': 0
        }
        
        try:
            with engine.connect() as conn:
                # Obtener columnas
                if db_type.lower() in ['postgresql', 'mysql', 'sqlserver']:
                    columns_query = """
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
                    result = conn.execute(text(columns_query), {"schema": schema, "table": table})
                    
                elif db_type.lower() == 'oracle':
                    columns_query = """
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
                    result = conn.execute(text(columns_query), {"schema": schema, "table": table})
                    
                elif db_type.lower() == 'sqlite':
                    result = conn.execute(text(f"PRAGMA table_info({table})"))
                    
                for row in result:
                    if db_type.lower() == 'sqlite':
                        table_info['columns'].append({
                            'name': row[1],
                            'type': row[2],
                            'nullable': not bool(row[3]),
                            'default': row[4],
                            'primary_key': bool(row[5])
                        })
                    elif db_type.lower() == 'oracle':
                        table_info['columns'].append({
                            'name': row[0],
                            'type': row[1],
                            'nullable': row[2] == 'Y',
                            'default': row[3],
                            'max_length': row[4],
                            'precision': row[5],
                            'scale': row[6]
                        })
                    else:
                        table_info['columns'].append({
                            'name': row[0],
                            'type': row[1],
                            'nullable': row[2] == 'YES',
                            'default': row[3],
                            'max_length': row[4],
                            'precision': row[5],
                            'scale': row[6]
                        })
                
                # Obtener llaves foráneas
                if db_type.lower() == 'postgresql':
                    fk_query = """
                        SELECT 
                            kcu.column_name,
                            ccu.table_schema AS foreign_table_schema,
                            ccu.table_name AS foreign_table_name,
                            ccu.column_name AS foreign_column_name,
                            rc.constraint_name
                        FROM information_schema.table_constraints AS tc 
                        JOIN information_schema.key_column_usage AS kcu
                            ON tc.constraint_name = kcu.constraint_name
                            AND tc.table_schema = kcu.table_schema
                        JOIN information_schema.constraint_column_usage AS ccu
                            ON ccu.constraint_name = tc.constraint_name
                            AND ccu.table_schema = tc.table_schema
                        JOIN information_schema.referential_constraints AS rc
                            ON tc.constraint_name = rc.constraint_name
                        WHERE tc.constraint_type = 'FOREIGN KEY' 
                            AND tc.table_schema = :schema 
                            AND tc.table_name = :table
                    """
                    result = conn.execute(text(fk_query), {"schema": schema, "table": table})
                    
                    for row in result:
                        table_info['foreign_keys'].append({
                            'column': row[0],
                            'referenced_schema': row[1],
                            'referenced_table': row[2],
                            'referenced_column': row[3],
                            'constraint_name': row[4]
                        })
                
                elif db_type.lower() == 'oracle':
                    fk_query = """
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
                    result = conn.execute(text(fk_query), {"schema": schema, "table": table})
                    
                    for row in result:
                        table_info['foreign_keys'].append({
                            'column': row[0],
                            'referenced_schema': row[1],
                            'referenced_table': row[2],
                            'referenced_column': row[3],
                            'constraint_name': row[4]
                        })
                
                # Obtener conteo de filas
                if db_type.lower() == 'sqlite':
                    count_query = f"SELECT COUNT(*) FROM {table}"
                else:
                    count_query = f"SELECT COUNT(*) FROM {schema}.{table}"
                    
                result = conn.execute(text(count_query))
                table_info['row_count'] = result.fetchone()[0]
                
        except Exception as e:
            self.logger.error(f"Error al obtener información de tabla: {str(e)}")
            
        return table_info
    
    def close_all_connections(self):
        """Cierra todas las conexiones abiertas"""
        for connection_id, engine in self.engines.items():
            try:
                engine.dispose()
            except Exception as e:
                self.logger.error(f"Error al cerrar conexión {connection_id}: {str(e)}")
        
        self.engines.clear()
    
    def execute_query(self, engine: Engine, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Ejecuta una consulta y retorna los resultados"""
        results = []
        
        try:
            with engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                columns = result.keys()
                
                for row in result:
                    results.append(dict(zip(columns, row)))
                    
        except Exception as e:
            self.logger.error(f"Error al ejecutar consulta: {str(e)}")
            raise
            
        return results