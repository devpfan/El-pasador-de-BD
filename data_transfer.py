"""
Data Transfer - Maneja la transferencia real de datos entre esquemas
Incluye creación de estructura, inserción de datos, manejo de errores y progreso
"""

import logging
import threading
import time
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, inspect
from sqlalchemy.engine import Engine
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

from database_manager import DatabaseManager
from schema_analyzer import SchemaInfo, TableInfo, ColumnInfo, ForeignKeyInfo
from dependency_resolver import DependencyResolver, TransferBatch


@dataclass
class TransferProgress:
    """Estado del progreso de transferencia"""
    current_table: str = ""
    tables_completed: int = 0
    total_tables: int = 0
    rows_transferred: int = 0
    total_rows: int = 0
    current_operation: str = "Preparando..."
    errors: List[str] = None
    warnings: List[str] = None
    start_time: Optional[float] = None
    estimated_remaining: Optional[float] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


@dataclass
class TransferOptions:
    """Opciones de configuración para la transferencia"""
    batch_size: int = 1000
    max_workers: int = 4
    create_schema: bool = True
    create_tables: bool = True
    drop_existing_tables: bool = False
    disable_constraints: bool = False
    ignore_foreign_keys: bool = False
    handle_circular_deps: bool = True
    continue_on_error: bool = False
    verify_data: bool = True
    parallel_tables: bool = False
    timeout_per_table: int = 3600  # segundos
    

class DataTransfer:
    """Maneja la transferencia completa de datos entre esquemas"""
    
    def __init__(self, db_manager: DatabaseManager, 
                 progress_callback: Optional[Callable[[TransferProgress], None]] = None):
        self.db_manager = db_manager
        self.progress_callback = progress_callback
        self.logger = logging.getLogger(__name__)
        self.dependency_resolver = DependencyResolver()
        
        # Control de transferencia
        self._stop_requested = False
        self._current_progress = TransferProgress()
        self._lock = threading.Lock()
        
    def transfer_schema(self, source_schema: SchemaInfo,
                       source_engine: Engine, target_engine: Engine,
                       target_schema_name: str, options: TransferOptions) -> bool:
        """Transfiere un esquema completo entre bases de datos"""
        
        self.logger.info(f"Iniciando transferencia: {source_schema.schema_name} -> {target_schema_name}")
        
        try:
            # Inicializar progreso
            with self._lock:
                self._current_progress = TransferProgress(
                    total_tables=len(source_schema.objects.tables),
                    total_rows=sum(t.row_count for t in source_schema.objects.tables.values()),
                    start_time=time.time(),
                    current_operation="Inicializando transferencia..."
                )
                self._stop_requested = False
            
            self._notify_progress()
            
            # Paso 1: Crear esquema destino si es necesario
            if options.create_schema:
                self._update_progress("Creando esquema destino...")
                if not self._create_target_schema(target_engine, target_schema_name):
                    return False
            
            # Paso 2: Crear estructura de tablas
            if options.create_tables:
                self._update_progress("Creando estructura de tablas...")
                if not self._create_table_structures(source_schema, source_engine, 
                                                   target_engine, target_schema_name, options):
                    return False
            
            # Paso 3: Deshabilitar constraints si es necesario
            if options.disable_constraints:
                self._update_progress("Deshabilitando constraints...")
                self._disable_foreign_keys(target_engine, target_schema_name, source_schema)
            
            # Paso 4: Transferir datos
            self._update_progress("Transfiriendo datos...")
            if not self._transfer_data(source_schema, source_engine, target_engine, 
                                     target_schema_name, options):
                return False
            
            # Paso 5: Restaurar constraints
            if options.disable_constraints:
                self._update_progress("Restaurando constraints...")
                self._enable_foreign_keys(target_engine, target_schema_name, source_schema)
            
            # Paso 6: Verificar datos si está habilitado
            if options.verify_data:
                self._update_progress("Verificando integridad de datos...")
                self._verify_transfer(source_schema, source_engine, target_engine, 
                                   target_schema_name)
            
            # Completado
            with self._lock:
                self._current_progress.current_operation = "Transferencia completada"
            self._notify_progress()
            
            self.logger.info("Transferencia completada exitosamente")
            return True
            
        except Exception as e:
            error_msg = f"Error durante transferencia: {str(e)}"
            self.logger.error(error_msg)
            with self._lock:
                self._current_progress.errors.append(error_msg)
                self._current_progress.current_operation = "Error en transferencia"
            self._notify_progress()
            return False
    
    def _create_target_schema(self, target_engine: Engine, schema_name: str) -> bool:
        """Crea el esquema destino si no existe"""
        try:
            # Obtener tipo de BD para usar sintaxis correcta
            db_type = target_engine.dialect.name.lower()
            
            with target_engine.connect() as conn:
                if db_type == 'postgresql':
                    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                elif db_type == 'mysql':
                    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                elif db_type == 'mssql':
                    # SQL Server usa CREATE SCHEMA
                    conn.execute(text(f"""
                        IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = '{schema_name}')
                        BEGIN
                            EXEC('CREATE SCHEMA {schema_name}')
                        END
                    """))
                # SQLite no tiene esquemas múltiples, no hacer nada
                
                conn.commit()
            
            return True
            
        except Exception as e:
            error_msg = f"Error creando esquema destino: {str(e)}"
            self.logger.error(error_msg)
            with self._lock:
                self._current_progress.errors.append(error_msg)
            return False
    
    def _create_table_structures(self, source_schema: SchemaInfo, source_engine: Engine,
                               target_engine: Engine, target_schema_name: str, 
                               options: TransferOptions) -> bool:
        """Crea la estructura de todas las tablas"""
        
        try:
            # Crear tablas en orden de dependencias
            for table_name in source_schema.dependency_order:
                if self._stop_requested:
                    return False
                
                self._update_progress(f"Creando tabla {table_name}...")
                
                table_info = source_schema.objects.tables[table_name]
                
                if not self._create_single_table(table_info, source_engine, target_engine, 
                                               target_schema_name, options):
                    if not options.continue_on_error:
                        return False
            
            return True
            
        except Exception as e:
            error_msg = f"Error creando estructuras de tablas: {str(e)}"
            self.logger.error(error_msg)
            with self._lock:
                self._current_progress.errors.append(error_msg)
            return False
    
    def _create_single_table(self, table_info: TableInfo, source_engine: Engine,
                           target_engine: Engine, target_schema_name: str,
                           options: TransferOptions) -> bool:
        """Crea una tabla individual"""
        
        try:
            # Obtener DDL de la tabla origen
            ddl = self._generate_create_table_ddl(table_info, source_engine, target_engine, 
                                                target_schema_name, options)
            
            # Ejecutar DDL en destino
            with target_engine.connect() as conn:
                # Eliminar tabla si existe y está configurado
                if options.drop_existing_tables:
                    drop_sql = f"DROP TABLE IF EXISTS {target_schema_name}.{table_info.table_name}"
                    try:
                        conn.execute(text(drop_sql))
                    except:
                        pass  # Ignorar error si la tabla no existe
                
                conn.execute(text(ddl))
                conn.commit()
            
            return True
            
        except Exception as e:
            error_msg = f"Error creando tabla {table_info.table_name}: {str(e)}"
            self.logger.error(error_msg)
            with self._lock:
                self._current_progress.errors.append(error_msg)
            return False
    
    def _generate_create_table_ddl(self, table_info: TableInfo, source_engine: Engine,
                                 target_engine: Engine, target_schema_name: str,
                                 options: TransferOptions) -> str:
        """Genera DDL CREATE TABLE adaptado para la BD destino"""
        
        target_db_type = target_engine.dialect.name.lower()
        
        # Mapeo de tipos de datos entre diferentes BD
        type_mapping = self._get_type_mapping(source_engine.dialect.name.lower(), target_db_type)
        
        # Construir DDL
        columns_ddl = []
        
        for column in table_info.columns:
            column_ddl = self._generate_column_ddl(column, type_mapping, target_db_type)
            columns_ddl.append(column_ddl)
        
        # Primary key
        pk_ddl = ""
        if table_info.primary_keys:
            pk_columns = ", ".join(table_info.primary_keys)
            pk_ddl = f", PRIMARY KEY ({pk_columns})"
        
        # Foreign keys (solo si no se ignoran)
        fk_ddl = ""
        if not options.ignore_foreign_keys and not options.disable_constraints:
            for fk in table_info.foreign_keys:
                # Solo crear FK si la tabla referenciada está en el mismo esquema
                if fk.referenced_schema == table_info.schema_name:
                    fk_ddl += f", FOREIGN KEY ({fk.column_name}) REFERENCES {target_schema_name}.{fk.referenced_table}({fk.referenced_column})"
        
        # Ensamblar DDL completo
        table_name = f"{target_schema_name}.{table_info.table_name}"
        if target_db_type == 'sqlite':
            table_name = table_info.table_name  # SQLite no usa esquemas
        
        ddl = f"""
        CREATE TABLE {table_name} (
            {', '.join(columns_ddl)}
            {pk_ddl}
            {fk_ddl}
        )
        """
        
        return ddl
    
    def _generate_column_ddl(self, column: ColumnInfo, type_mapping: Dict[str, str], 
                           target_db_type: str) -> str:
        """Genera DDL para una columna individual"""
        
        # Mapear tipo de dato
        data_type = type_mapping.get(column.data_type.lower(), column.data_type)
        
        # Agregar longitud si es aplicable
        if column.max_length and data_type.lower() in ['varchar', 'char', 'text']:
            if column.max_length > 0:
                data_type = f"{data_type}({column.max_length})"
        
        # Agregar precisión y escala para números
        if column.precision and data_type.lower() in ['decimal', 'numeric']:
            if column.scale:
                data_type = f"{data_type}({column.precision}, {column.scale})"
            else:
                data_type = f"{data_type}({column.precision})"
        
        # NULL/NOT NULL
        nullable = "NULL" if column.is_nullable else "NOT NULL"
        
        # Default value
        default = ""
        if column.default_value:
            # Limpiar valor por defecto
            default_val = column.default_value
            if not default_val.startswith("'") and not default_val.isdigit():
                # Agregar comillas si no las tiene y no es un número
                default_val = f"'{default_val}'"
            default = f" DEFAULT {default_val}"
        
        return f"{column.name} {data_type} {nullable}{default}"
    
    def _get_type_mapping(self, source_db: str, target_db: str) -> Dict[str, str]:
        """Obtiene mapeo de tipos de datos entre BD"""
        
        # Mapeos básicos (se puede extender)
        mappings = {
            'postgresql_to_mysql': {
                'serial': 'INT AUTO_INCREMENT',
                'bigserial': 'BIGINT AUTO_INCREMENT',
                'boolean': 'TINYINT(1)',
                'bytea': 'LONGBLOB',
                'text': 'LONGTEXT'
            },
            'mysql_to_postgresql': {
                'tinyint': 'SMALLINT',
                'mediumint': 'INTEGER',
                'longtext': 'TEXT',
                'longblob': 'BYTEA'
            },
            'postgresql_to_sqlite': {
                'serial': 'INTEGER',
                'bigserial': 'INTEGER',
                'boolean': 'INTEGER',
                'bytea': 'BLOB'
            }
            # Agregar más mapeos según necesidad
        }
        
        mapping_key = f"{source_db}_to_{target_db}"
        return mappings.get(mapping_key, {})
    
    def _transfer_data(self, source_schema: SchemaInfo, source_engine: Engine,
                      target_engine: Engine, target_schema_name: str,
                      options: TransferOptions) -> bool:
        """Transfiere todos los datos según el orden de dependencias"""
        
        try:
            if options.parallel_tables:
                return self._transfer_data_parallel(source_schema, source_engine, 
                                                  target_engine, target_schema_name, options)
            else:
                return self._transfer_data_sequential(source_schema, source_engine,
                                                   target_engine, target_schema_name, options)
        except Exception as e:
            error_msg = f"Error en transferencia de datos: {str(e)}"
            self.logger.error(error_msg)
            with self._lock:
                self._current_progress.errors.append(error_msg)
            return False
    
    def _transfer_data_sequential(self, source_schema: SchemaInfo, source_engine: Engine,
                                target_engine: Engine, target_schema_name: str,
                                options: TransferOptions) -> bool:
        """Transfiere datos tabla por tabla secuencialmente"""
        
        for i, table_name in enumerate(source_schema.dependency_order):
            if self._stop_requested:
                return False
            
            table_info = source_schema.objects.tables[table_name]
            
            with self._lock:
                self._current_progress.current_table = table_name
                self._current_progress.tables_completed = i
                self._current_progress.current_operation = f"Transfiriendo {table_name}..."
            
            self._notify_progress()
            
            success = self._transfer_single_table(table_info, source_engine, target_engine,
                                                source_schema.schema_name, target_schema_name, options)
            
            if not success and not options.continue_on_error:
                return False
            
            with self._lock:
                self._current_progress.tables_completed = i + 1
            
            self._notify_progress()
        
        return True
    
    def _transfer_data_parallel(self, source_schema: SchemaInfo, source_engine: Engine,
                              target_engine: Engine, target_schema_name: str,
                              options: TransferOptions) -> bool:
        """Transfiere datos en paralelo respetando dependencias"""
        
        # Crear batches por nivel de dependencias
        batches = self.dependency_resolver.create_transfer_batches(
            source_schema, 
            self.dependency_resolver.create_dependency_graph(source_schema),
            max_batch_size=options.max_workers
        )
        
        for batch in batches:
            if self._stop_requested:
                return False
            
            # Transferir tablas del batch en paralelo
            with ThreadPoolExecutor(max_workers=min(options.max_workers, len(batch.tables))) as executor:
                futures = {}
                
                for table_name in batch.tables:
                    table_info = source_schema.objects.tables[table_name]
                    
                    future = executor.submit(
                        self._transfer_single_table,
                        table_info, source_engine, target_engine,
                        source_schema.schema_name, target_schema_name, options
                    )
                    futures[future] = table_name
                
                # Esperar a que terminen todas las tablas del batch
                for future in as_completed(futures):
                    table_name = futures[future]
                    try:
                        success = future.result(timeout=options.timeout_per_table)
                        if not success and not options.continue_on_error:
                            return False
                    except Exception as e:
                        error_msg = f"Error en tabla {table_name}: {str(e)}"
                        self.logger.error(error_msg)
                        with self._lock:
                            self._current_progress.errors.append(error_msg)
                        if not options.continue_on_error:
                            return False
        
        return True
    
    def _transfer_single_table(self, table_info: TableInfo, source_engine: Engine,
                             target_engine: Engine, source_schema_name: str,
                             target_schema_name: str, options: TransferOptions) -> bool:
        """Transfiere datos de una tabla individual"""
        
        try:
            # Construir query de origen
            source_table = f"{source_schema_name}.{table_info.table_name}"
            if source_engine.dialect.name.lower() == 'sqlite':
                source_table = table_info.table_name
            
            # Leer datos en chunks
            chunk_size = options.batch_size
            offset = 0
            rows_transferred = 0
            
            while True:
                if self._stop_requested:
                    return False
                
                # Leer chunk de datos
                query = f"SELECT * FROM {source_table} LIMIT {chunk_size} OFFSET {offset}"
                
                with source_engine.connect() as source_conn:
                    df = pd.read_sql(query, source_conn)
                
                if df.empty:
                    break
                
                # Insertar en destino
                target_table = f"{target_schema_name}.{table_info.table_name}"
                if target_engine.dialect.name.lower() == 'sqlite':
                    target_table = table_info.table_name
                
                with target_engine.connect() as target_conn:
                    df.to_sql(
                        table_info.table_name,
                        target_conn,
                        schema=target_schema_name if target_engine.dialect.name.lower() != 'sqlite' else None,
                        if_exists='append',
                        index=False,
                        method='multi'
                    )
                    target_conn.commit()
                
                rows_transferred += len(df)
                offset += chunk_size
                
                # Actualizar progreso
                with self._lock:
                    self._current_progress.rows_transferred += len(df)
                
                self._notify_progress()
                
                # Si el chunk no está completo, hemos terminado
                if len(df) < chunk_size:
                    break
            
            self.logger.info(f"Tabla {table_info.table_name}: {rows_transferred:,} filas transferidas")
            return True
            
        except Exception as e:
            error_msg = f"Error transfiriendo tabla {table_info.table_name}: {str(e)}"
            self.logger.error(error_msg)
            with self._lock:
                self._current_progress.errors.append(error_msg)
            return False
    
    def _disable_foreign_keys(self, engine: Engine, schema_name: str, 
                            source_schema: SchemaInfo):
        """Deshabilita las foreign keys temporalmente"""
        try:
            db_type = engine.dialect.name.lower()
            
            with engine.connect() as conn:
                if db_type == 'postgresql':
                    # PostgreSQL: Eliminar constraints temporalmente
                    for table_name, table_info in source_schema.objects.tables.items():
                        for fk in table_info.foreign_keys:
                            try:
                                conn.execute(text(f"""
                                    ALTER TABLE {schema_name}.{table_name} 
                                    DROP CONSTRAINT IF EXISTS {fk.constraint_name}
                                """))
                            except:
                                pass  # Ignorar errores
                
                elif db_type == 'mysql':
                    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
                
                elif db_type == 'sqlite':
                    conn.execute(text("PRAGMA foreign_keys = OFF"))
                
                conn.commit()
                
        except Exception as e:
            self.logger.warning(f"No se pudieron deshabilitar las FK: {str(e)}")
    
    def _enable_foreign_keys(self, engine: Engine, schema_name: str,
                           source_schema: SchemaInfo):
        """Restaura las foreign keys"""
        try:
            db_type = engine.dialect.name.lower()
            
            with engine.connect() as conn:
                if db_type == 'postgresql':
                    # PostgreSQL: Recrear constraints
                    for table_name, table_info in source_schema.objects.tables.items():
                        for fk in table_info.foreign_keys:
                            try:
                                conn.execute(text(f"""
                                    ALTER TABLE {schema_name}.{table_name} 
                                    ADD CONSTRAINT {fk.constraint_name} 
                                    FOREIGN KEY ({fk.column_name}) 
                                    REFERENCES {schema_name}.{fk.referenced_table}({fk.referenced_column})
                                """))
                            except Exception as e:
                                self.logger.warning(f"No se pudo restaurar FK {fk.constraint_name}: {str(e)}")
                
                elif db_type == 'mysql':
                    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
                
                elif db_type == 'sqlite':
                    conn.execute(text("PRAGMA foreign_keys = ON"))
                
                conn.commit()
                
        except Exception as e:
            self.logger.warning(f"No se pudieron restaurar las FK: {str(e)}")
    
    def _verify_transfer(self, source_schema: SchemaInfo, source_engine: Engine,
                        target_engine: Engine, target_schema_name: str):
        """Verifica la integridad de la transferencia"""
        
        self.logger.info("Verificando transferencia...")
        
        for table_name, table_info in source_schema.objects.tables.items():
            try:
                # Contar filas en origen
                source_table = f"{source_schema.schema_name}.{table_name}"
                if source_engine.dialect.name.lower() == 'sqlite':
                    source_table = table_name
                
                with source_engine.connect() as conn:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {source_table}"))
                    source_count = result.fetchone()[0]
                
                # Contar filas en destino
                target_table = f"{target_schema_name}.{table_name}"
                if target_engine.dialect.name.lower() == 'sqlite':
                    target_table = table_name
                
                with target_engine.connect() as conn:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {target_table}"))
                    target_count = result.fetchone()[0]
                
                # Comparar
                if source_count != target_count:
                    warning_msg = f"Discrepancia en {table_name}: origen={source_count}, destino={target_count}"
                    self.logger.warning(warning_msg)
                    with self._lock:
                        self._current_progress.warnings.append(warning_msg)
                else:
                    self.logger.info(f"Tabla {table_name} verificada: {source_count:,} filas")
                    
            except Exception as e:
                warning_msg = f"No se pudo verificar tabla {table_name}: {str(e)}"
                self.logger.warning(warning_msg)
                with self._lock:
                    self._current_progress.warnings.append(warning_msg)
    
    def _update_progress(self, operation: str):
        """Actualiza el progreso actual"""
        with self._lock:
            self._current_progress.current_operation = operation
            
            # Calcular tiempo restante estimado
            if self._current_progress.start_time and self._current_progress.tables_completed > 0:
                elapsed = time.time() - self._current_progress.start_time
                rate = self._current_progress.tables_completed / elapsed
                remaining_tables = self._current_progress.total_tables - self._current_progress.tables_completed
                self._current_progress.estimated_remaining = remaining_tables / rate if rate > 0 else None
        
        self._notify_progress()
    
    def _notify_progress(self):
        """Notifica el progreso actual al callback"""
        if self.progress_callback:
            with self._lock:
                progress_copy = TransferProgress(
                    current_table=self._current_progress.current_table,
                    tables_completed=self._current_progress.tables_completed,
                    total_tables=self._current_progress.total_tables,
                    rows_transferred=self._current_progress.rows_transferred,
                    total_rows=self._current_progress.total_rows,
                    current_operation=self._current_progress.current_operation,
                    errors=self._current_progress.errors.copy(),
                    warnings=self._current_progress.warnings.copy(),
                    start_time=self._current_progress.start_time,
                    estimated_remaining=self._current_progress.estimated_remaining
                )
            
            try:
                self.progress_callback(progress_copy)
            except Exception as e:
                self.logger.error(f"Error en callback de progreso: {str(e)}")
    
    def stop_transfer(self):
        """Solicita detener la transferencia"""
        with self._lock:
            self._stop_requested = True
            self._current_progress.current_operation = "Deteniendo transferencia..."
        self._notify_progress()
    
    def get_current_progress(self) -> TransferProgress:
        """Obtiene el progreso actual"""
        with self._lock:
            return TransferProgress(
                current_table=self._current_progress.current_table,
                tables_completed=self._current_progress.tables_completed,
                total_tables=self._current_progress.total_tables,
                rows_transferred=self._current_progress.rows_transferred,
                total_rows=self._current_progress.total_rows,
                current_operation=self._current_progress.current_operation,
                errors=self._current_progress.errors.copy(),
                warnings=self._current_progress.warnings.copy(),
                start_time=self._current_progress.start_time,
                estimated_remaining=self._current_progress.estimated_remaining
            )


class TransferDialog:
    """Diálogo de configuración y progreso de transferencia"""
    
    def __init__(self, parent, source_schema: SchemaInfo):
        self.parent = parent
        self.source_schema = source_schema
        self.transfer_options = TransferOptions()
        self.data_transfer: Optional[DataTransfer] = None
        self.transfer_thread: Optional[threading.Thread] = None
        
        self.setup_dialog()
    
    def setup_dialog(self):
        """Configura el diálogo de transferencia"""
        import tkinter as tk
        from tkinter import ttk
        
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Configurar Transferencia")
        self.dialog.geometry("600x700")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Notebook para diferentes configuraciones
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Pestaña de opciones generales
        self.setup_general_tab(notebook)
        
        # Pestaña de opciones avanzadas
        self.setup_advanced_tab(notebook)
        
        # Pestaña de progreso
        self.setup_progress_tab(notebook)
        
        # Botones
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.start_btn = ttk.Button(button_frame, text="Iniciar Transferencia",
                                  command=self.start_transfer)
        self.start_btn.pack(side='right', padx=(5, 0))
        
        self.stop_btn = ttk.Button(button_frame, text="Detener",
                                 command=self.stop_transfer, state='disabled')
        self.stop_btn.pack(side='right', padx=(5, 0))
        
        ttk.Button(button_frame, text="Cerrar",
                  command=self.close_dialog).pack(side='right')
    
    def setup_general_tab(self, notebook):
        """Configura la pestaña de opciones generales"""
        import tkinter as tk
        from tkinter import ttk
        
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="General")
        
        # Variables para checkboxes
        self.create_schema_var = tk.BooleanVar(value=True)
        self.create_tables_var = tk.BooleanVar(value=True)
        self.drop_existing_var = tk.BooleanVar(value=False)
        
        # Checkboxes
        ttk.Checkbutton(general_frame, text="Crear esquema destino",
                       variable=self.create_schema_var).pack(anchor='w', pady=5)
        
        ttk.Checkbutton(general_frame, text="Crear tablas",
                       variable=self.create_tables_var).pack(anchor='w', pady=5)
        
        ttk.Checkbutton(general_frame, text="Eliminar tablas existentes",
                       variable=self.drop_existing_var).pack(anchor='w', pady=5)
        
        # Tamaño de lote
        batch_frame = ttk.Frame(general_frame)
        batch_frame.pack(fill='x', pady=10)
        
        ttk.Label(batch_frame, text="Tamaño de lote:").pack(side='left')
        self.batch_size_var = tk.StringVar(value="1000")
        ttk.Entry(batch_frame, textvariable=self.batch_size_var, width=10).pack(side='right')
    
    def setup_advanced_tab(self, notebook):
        """Configura la pestaña de opciones avanzadas"""
        import tkinter as tk
        from tkinter import ttk
        
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="Avanzado")
        
        # Variables avanzadas
        self.disable_constraints_var = tk.BooleanVar(value=False)
        self.ignore_fks_var = tk.BooleanVar(value=False)
        self.continue_on_error_var = tk.BooleanVar(value=False)
        self.verify_data_var = tk.BooleanVar(value=True)
        self.parallel_tables_var = tk.BooleanVar(value=False)
        
        # Checkboxes avanzados
        ttk.Checkbutton(advanced_frame, text="Deshabilitar constraints temporalmente",
                       variable=self.disable_constraints_var).pack(anchor='w', pady=5)
        
        ttk.Checkbutton(advanced_frame, text="Ignorar llaves foráneas",
                       variable=self.ignore_fks_var).pack(anchor='w', pady=5)
        
        ttk.Checkbutton(advanced_frame, text="Continuar en caso de error",
                       variable=self.continue_on_error_var).pack(anchor='w', pady=5)
        
        ttk.Checkbutton(advanced_frame, text="Verificar datos al final",
                       variable=self.verify_data_var).pack(anchor='w', pady=5)
        
        ttk.Checkbutton(advanced_frame, text="Transferencia paralela",
                       variable=self.parallel_tables_var).pack(anchor='w', pady=5)
    
    def setup_progress_tab(self, notebook):
        """Configura la pestaña de progreso"""
        import tkinter as tk
        from tkinter import ttk
        
        progress_frame = ttk.Frame(notebook)
        notebook.add(progress_frame, text="Progreso")
        
        # Información de progreso
        self.progress_text = tk.Text(progress_frame, height=20, wrap='word')
        
        scroll = ttk.Scrollbar(progress_frame, orient='vertical', command=self.progress_text.yview)
        self.progress_text.configure(yscrollcommand=scroll.set)
        
        self.progress_text.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        
        # Barra de progreso
        progress_info_frame = ttk.Frame(self.dialog)
        progress_info_frame.pack(fill='x', padx=10, pady=(0, 5))
        
        self.progress_label = ttk.Label(progress_info_frame, text="Listo para transferir")
        self.progress_label.pack(anchor='w')
        
        self.progress_bar = ttk.Progressbar(progress_info_frame, mode='determinate')
        self.progress_bar.pack(fill='x', pady=(5, 0))
    
    def start_transfer(self):
        """Inicia la transferencia"""
        # Obtener configuraciones
        self.transfer_options.create_schema = self.create_schema_var.get()
        self.transfer_options.create_tables = self.create_tables_var.get()
        self.transfer_options.drop_existing_tables = self.drop_existing_var.get()
        self.transfer_options.batch_size = int(self.batch_size_var.get())
        self.transfer_options.disable_constraints = self.disable_constraints_var.get()
        self.transfer_options.ignore_foreign_keys = self.ignore_fks_var.get()
        self.transfer_options.continue_on_error = self.continue_on_error_var.get()
        self.transfer_options.verify_data = self.verify_data_var.get()
        self.transfer_options.parallel_tables = self.parallel_tables_var.get()
        
        # Configurar UI para transferencia activa
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        
        # Iniciar transferencia en hilo separado
        self.transfer_thread = threading.Thread(target=self._run_transfer, daemon=True)
        self.transfer_thread.start()
    
    def _run_transfer(self):
        """Ejecuta la transferencia en hilo separado"""
        try:
            # Aquí iría la lógica real de transferencia
            # Por ahora simulamos el progreso
            
            for i in range(len(self.source_schema.tables)):
                if hasattr(self, '_stop_requested') and self._stop_requested:
                    break
                
                table_name = list(self.source_schema.objects.tables.keys())[i]
                
                # Simular progreso
                progress = TransferProgress(
                    current_table=table_name,
                    tables_completed=i,
                    total_tables=len(self.source_schema.tables),
                    rows_transferred=i * 1000,
                    total_rows=sum(t.row_count for t in self.source_schema.objects.tables.values()),
                    current_operation=f"Transfiriendo {table_name}..."
                )
                
                self.dialog.after(0, lambda p=progress: self.update_progress_display(p))
                
                time.sleep(1)  # Simular trabajo
            
            # Completado
            final_progress = TransferProgress(
                tables_completed=len(self.source_schema.tables),
                total_tables=len(self.source_schema.tables),
                current_operation="Transferencia completada"
            )
            
            self.dialog.after(0, lambda: self.update_progress_display(final_progress))
            self.dialog.after(0, self.on_transfer_complete)
            
        except Exception as e:
            self.dialog.after(0, lambda: self.on_transfer_error(str(e)))
    
    def update_progress_display(self, progress: TransferProgress):
        """Actualiza la visualización del progreso"""
        import tkinter as tk
        
        # Actualizar barra de progreso
        if progress.total_tables > 0:
            percent = (progress.tables_completed / progress.total_tables) * 100
            self.progress_bar['value'] = percent
        
        # Actualizar etiqueta
        self.progress_label.config(text=progress.current_operation)
        
        # Agregar al log
        timestamp = time.strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {progress.current_operation}\n"
        
        if progress.current_table:
            log_msg += f"  Tabla actual: {progress.current_table}\n"
        
        if progress.tables_completed > 0:
            log_msg += f"  Progreso: {progress.tables_completed}/{progress.total_tables} tablas\n"
        
        if progress.rows_transferred > 0:
            log_msg += f"  Filas: {progress.rows_transferred:,}/{progress.total_rows:,}\n"
        
        self.progress_text.insert(tk.END, log_msg)
        self.progress_text.see(tk.END)
    
    def stop_transfer(self):
        """Detiene la transferencia"""
        self._stop_requested = True
        if self.data_transfer:
            self.data_transfer.stop_transfer()
    
    def on_transfer_complete(self):
        """Maneja la finalización de la transferencia"""
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.progress_bar['value'] = 100
    
    def on_transfer_error(self, error_msg: str):
        """Maneja errores en la transferencia"""
        import tkinter as tk
        
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        
        timestamp = time.strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] ERROR: {error_msg}\n"
        self.progress_text.insert(tk.END, log_msg)
        self.progress_text.see(tk.END)
    
    def close_dialog(self):
        """Cierra el diálogo"""
        if self.transfer_thread and self.transfer_thread.is_alive():
            self.stop_transfer()
        
        self.dialog.destroy()
    
    def show(self):
        """Muestra el diálogo"""
        self.dialog.wait_window()


# Ejemplo de uso
if __name__ == "__main__":
    # Este archivo se puede probar independientemente
    logging.basicConfig(level=logging.INFO)
    
    def progress_callback(progress: TransferProgress):
        print(f"Progreso: {progress.current_operation} - "
              f"{progress.tables_completed}/{progress.total_tables} tablas")
    
    # Aquí iría código de prueba si fuera necesario