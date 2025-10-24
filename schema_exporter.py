"""
Schema Exporter - Módulo para exportar esquemas e información a diferentes formatos
Incluye exportación a SQL, JSON, Excel, y reportes HTML
"""

import logging
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from schema_analyzer import SchemaInfo, TableInfo, ViewInfo, SequenceInfo, ProcedureInfo, TriggerInfo, IndexInfo


class SchemaExporter:
    """Exportador de esquemas a diferentes formatos"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def export_to_sql_ddl(self, schema_info: SchemaInfo, output_path: str, 
                          target_db_type: str = 'oracle') -> bool:
        """Exporta el esquema completo como DDL SQL"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"-- DDL Export for Schema: {schema_info.schema_name}\n")
                f.write(f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- Target Database: {target_db_type.upper()}\n")
                f.write("-- " + "="*60 + "\n\n")
                
                # Crear esquema si es necesario
                if target_db_type.lower() != 'oracle':
                    f.write(f"CREATE SCHEMA IF NOT EXISTS {schema_info.schema_name};\n\n")
                
                # Secuencias
                if schema_info.objects.sequences:
                    f.write("-- SECUENCIAS\n")
                    f.write("-- " + "-"*40 + "\n\n")
                    
                    for seq_name, seq_info in schema_info.objects.sequences.items():
                        f.write(self._generate_sequence_ddl(seq_info, target_db_type))
                        f.write("\n")
                
                # Tablas
                if schema_info.objects.tables:
                    f.write("-- TABLAS\n")
                    f.write("-- " + "-"*40 + "\n\n")
                    
                    # Usar orden de dependencias
                    for table_name in schema_info.dependency_order:
                        if table_name in schema_info.objects.tables:
                            table_info = schema_info.objects.tables[table_name]
                            f.write(self._generate_table_ddl(table_info, target_db_type))
                            f.write("\n")
                
                # Vistas
                if schema_info.objects.views:
                    f.write("-- VISTAS\n")
                    f.write("-- " + "-"*40 + "\n\n")
                    
                    for view_name, view_info in schema_info.objects.views.items():
                        f.write(self._generate_view_ddl(view_info, target_db_type))
                        f.write("\n")
                
                # Índices
                if schema_info.objects.indexes:
                    f.write("-- ÍNDICES\n")
                    f.write("-- " + "-"*40 + "\n\n")
                    
                    for index_name, index_info in schema_info.objects.indexes.items():
                        if not self._is_system_index(index_info):
                            f.write(self._generate_index_ddl(index_info, target_db_type))
                            f.write("\n")
                
                # Procedimientos
                if schema_info.objects.procedures:
                    f.write("-- PROCEDIMIENTOS Y FUNCIONES\n")
                    f.write("-- " + "-"*40 + "\n\n")
                    
                    for proc_name, proc_info in schema_info.objects.procedures.items():
                        f.write(self._generate_procedure_ddl(proc_info, target_db_type))
                        f.write("\n")
                
                # Triggers
                if schema_info.objects.triggers:
                    f.write("-- TRIGGERS\n")
                    f.write("-- " + "-"*40 + "\n\n")
                    
                    for trigger_name, trigger_info in schema_info.objects.triggers.items():
                        f.write(self._generate_trigger_ddl(trigger_info, target_db_type))
                        f.write("\n")
            
            self.logger.info(f"DDL exportado exitosamente a: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exportando DDL: {str(e)}")
            return False
    
    def export_to_json(self, schema_info: SchemaInfo, output_path: str, 
                       include_data_samples: bool = False) -> bool:
        """Exporta el esquema completo a JSON"""
        try:
            export_data = {
                "metadata": {
                    "schema_name": schema_info.schema_name,
                    "exported_on": datetime.now().isoformat(),
                    "export_version": "1.0"
                },
                "statistics": {
                    "total_tables": len(schema_info.objects.tables),
                    "total_views": len(schema_info.objects.views),
                    "total_sequences": len(schema_info.objects.sequences),
                    "total_procedures": len(schema_info.objects.procedures),
                    "total_triggers": len(schema_info.objects.triggers),
                    "total_indexes": len(schema_info.objects.indexes),
                    "total_rows": sum(t.row_count for t in schema_info.objects.tables.values())
                },
                "objects": {
                    "tables": self._serialize_tables(schema_info.objects.tables),
                    "views": self._serialize_views(schema_info.objects.views),
                    "sequences": self._serialize_sequences(schema_info.objects.sequences),
                    "procedures": self._serialize_procedures(schema_info.objects.procedures),
                    "triggers": self._serialize_triggers(schema_info.objects.triggers),
                    "indexes": self._serialize_indexes(schema_info.objects.indexes)
                },
                "dependencies": {
                    "table_order": schema_info.dependency_order,
                    "creation_order": [(obj_type, obj_name) for obj_type, obj_name in schema_info.creation_order]
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"JSON exportado exitosamente a: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exportando JSON: {str(e)}")
            return False
    
    def export_to_html_report(self, schema_info: SchemaInfo, output_path: str) -> bool:
        """Exporta un reporte HTML detallado del esquema"""
        try:
            html_content = self._generate_html_report(schema_info)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"Reporte HTML exportado exitosamente a: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exportando reporte HTML: {str(e)}")
            return False
    
    def export_to_csv_summary(self, schema_info: SchemaInfo, output_dir: str) -> bool:
        """Exporta resúmenes de objetos a archivos CSV"""
        try:
            import csv
            
            # Crear directorio si no existe
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Exportar tablas
            if schema_info.objects.tables:
                tables_file = os.path.join(output_dir, 'tables_summary.csv')
                with open(tables_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Tabla', 'Filas', 'Columnas', 'Llaves_Foraneas', 'Dependencias'])
                    
                    for name, table in schema_info.objects.tables.items():
                        writer.writerow([
                            name, 
                            table.row_count, 
                            len(table.columns),
                            len(table.foreign_keys),
                            len(table.dependencies)
                        ])
            
            # Exportar vistas
            if schema_info.objects.views:
                views_file = os.path.join(output_dir, 'views_summary.csv')
                with open(views_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Vista', 'Actualizable', 'Columnas', 'Dependencias'])
                    
                    for name, view in schema_info.objects.views.items():
                        writer.writerow([
                            name,
                            'Si' if view.is_updatable else 'No',
                            len(view.columns),
                            len(view.dependencies)
                        ])
            
            # Exportar secuencias
            if schema_info.objects.sequences:
                sequences_file = os.path.join(output_dir, 'sequences_summary.csv')
                with open(sequences_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Secuencia', 'Inicio', 'Incremento', 'Min', 'Max', 'Ciclo'])
                    
                    for name, seq in schema_info.objects.sequences.items():
                        writer.writerow([
                            name,
                            seq.start_value,
                            seq.increment_by,
                            seq.min_value,
                            seq.max_value,
                            'Si' if seq.cycle_flag else 'No'
                        ])
            
            self.logger.info(f"CSVs exportados exitosamente en: {output_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exportando CSVs: {str(e)}")
            return False
    
    # Métodos auxiliares para generar DDL
    def _generate_sequence_ddl(self, seq_info: SequenceInfo, target_db_type: str) -> str:
        """Genera DDL para una secuencia"""
        if target_db_type.lower() == 'oracle':
            ddl = f"CREATE SEQUENCE {seq_info.schema_name}.{seq_info.sequence_name}\n"
            ddl += f"    START WITH {seq_info.start_value}\n"
            ddl += f"    INCREMENT BY {seq_info.increment_by}\n"
            
            if seq_info.min_value is not None:
                ddl += f"    MINVALUE {seq_info.min_value}\n"
            if seq_info.max_value is not None:
                ddl += f"    MAXVALUE {seq_info.max_value}\n"
                
            ddl += f"    {'CYCLE' if seq_info.cycle_flag else 'NOCYCLE'}\n"
            
            if seq_info.cache_size:
                ddl += f"    CACHE {seq_info.cache_size}\n"
                
            ddl += ";\n"
            
        elif target_db_type.lower() == 'postgresql':
            ddl = f"CREATE SEQUENCE {seq_info.schema_name}.{seq_info.sequence_name}\n"
            ddl += f"    START {seq_info.start_value}\n"
            ddl += f"    INCREMENT {seq_info.increment_by}\n"
            
            if seq_info.min_value is not None:
                ddl += f"    MINVALUE {seq_info.min_value}\n"
            if seq_info.max_value is not None:
                ddl += f"    MAXVALUE {seq_info.max_value}\n"
                
            if seq_info.cycle_flag:
                ddl += "    CYCLE\n"
                
            ddl += ";\n"
            
        else:
            ddl = f"-- Secuencia {seq_info.sequence_name} no soportada en {target_db_type}\n"
        
        return ddl
    
    def _generate_table_ddl(self, table_info: TableInfo, target_db_type: str) -> str:
        """Genera DDL para una tabla"""
        ddl = f"CREATE TABLE {table_info.schema_name}.{table_info.table_name} (\n"
        
        # Columnas
        column_ddls = []
        for col in table_info.columns:
            col_ddl = f"    {col.name} {col.data_type}"
            
            if col.max_length:
                col_ddl += f"({col.max_length})"
            elif col.precision:
                if col.scale:
                    col_ddl += f"({col.precision},{col.scale})"
                else:
                    col_ddl += f"({col.precision})"
            
            if not col.is_nullable:
                col_ddl += " NOT NULL"
                
            if col.default_value:
                col_ddl += f" DEFAULT {col.default_value}"
                
            column_ddls.append(col_ddl)
        
        ddl += ",\n".join(column_ddls)
        
        # Llave primaria
        if table_info.primary_keys:
            pk_cols = ", ".join(table_info.primary_keys)
            ddl += f",\n    CONSTRAINT PK_{table_info.table_name} PRIMARY KEY ({pk_cols})"
        
        ddl += "\n);\n\n"
        
        # Llaves foráneas
        for fk in table_info.foreign_keys:
            ddl += f"ALTER TABLE {table_info.schema_name}.{table_info.table_name}\n"
            ddl += f"    ADD CONSTRAINT {fk.constraint_name}\n"
            ddl += f"    FOREIGN KEY ({fk.column_name})\n"
            ddl += f"    REFERENCES {fk.referenced_schema}.{fk.referenced_table}({fk.referenced_column});\n\n"
        
        return ddl
    
    def _generate_view_ddl(self, view_info: ViewInfo, target_db_type: str) -> str:
        """Genera DDL para una vista"""
        ddl = f"CREATE VIEW {view_info.schema_name}.{view_info.view_name} AS\n"
        ddl += f"{view_info.definition};\n"
        return ddl
    
    def _generate_index_ddl(self, index_info: IndexInfo, target_db_type: str) -> str:
        """Genera DDL para un índice"""
        unique_clause = "UNIQUE " if index_info.is_unique else ""
        columns_str = ", ".join(index_info.columns)
        
        ddl = f"CREATE {unique_clause}INDEX {index_info.index_name}\n"
        ddl += f"    ON {index_info.schema_name}.{index_info.table_name} ({columns_str});\n"
        
        return ddl
    
    def _generate_procedure_ddl(self, proc_info: ProcedureInfo, target_db_type: str) -> str:
        """Genera DDL para un procedimiento"""
        return f"{proc_info.definition};\n"
    
    def _generate_trigger_ddl(self, trigger_info: TriggerInfo, target_db_type: str) -> str:
        """Genera DDL para un trigger"""
        return f"{trigger_info.definition};\n"
    
    def _is_system_index(self, index_info: IndexInfo) -> bool:
        """Determina si un índice es del sistema"""
        index_name = index_info.index_name.upper()
        return (index_name.startswith('PK_') or 
                index_name.startswith('FK_') or
                index_name.startswith('SYS_'))
    
    # Métodos de serialización para JSON
    def _serialize_tables(self, tables: Dict[str, TableInfo]) -> Dict:
        """Serializa tablas a diccionario"""
        result = {}
        for name, table in tables.items():
            result[name] = {
                "schema_name": table.schema_name,
                "table_name": table.table_name,
                "row_count": table.row_count,
                "columns": [
                    {
                        "name": col.name,
                        "data_type": col.data_type,
                        "is_nullable": col.is_nullable,
                        "is_primary_key": col.is_primary_key,
                        "is_foreign_key": col.is_foreign_key,
                        "max_length": col.max_length,
                        "precision": col.precision,
                        "scale": col.scale
                    }
                    for col in table.columns
                ],
                "primary_keys": table.primary_keys,
                "foreign_keys": [
                    {
                        "column_name": fk.column_name,
                        "referenced_schema": fk.referenced_schema,
                        "referenced_table": fk.referenced_table,
                        "referenced_column": fk.referenced_column,
                        "constraint_name": fk.constraint_name
                    }
                    for fk in table.foreign_keys
                ],
                "dependencies": list(table.dependencies),
                "dependents": list(table.dependents)
            }
        return result
    
    def _serialize_views(self, views: Dict[str, ViewInfo]) -> Dict:
        """Serializa vistas a diccionario"""
        result = {}
        for name, view in views.items():
            result[name] = {
                "schema_name": view.schema_name,
                "view_name": view.view_name,
                "is_updatable": view.is_updatable,
                "column_count": len(view.columns),
                "dependencies": list(view.dependencies)
            }
        return result
    
    def _serialize_sequences(self, sequences: Dict[str, SequenceInfo]) -> Dict:
        """Serializa secuencias a diccionario"""
        result = {}
        for name, seq in sequences.items():
            result[name] = {
                "schema_name": seq.schema_name,
                "sequence_name": seq.sequence_name,
                "start_value": seq.start_value,
                "increment_by": seq.increment_by,
                "min_value": seq.min_value,
                "max_value": seq.max_value,
                "cycle_flag": seq.cycle_flag,
                "cache_size": seq.cache_size,
                "last_number": seq.last_number
            }
        return result
    
    def _serialize_procedures(self, procedures: Dict[str, ProcedureInfo]) -> Dict:
        """Serializa procedimientos a diccionario"""
        result = {}
        for name, proc in procedures.items():
            result[name] = {
                "schema_name": proc.schema_name,
                "procedure_name": proc.procedure_name,
                "procedure_type": proc.procedure_type,
                "language": proc.language,
                "parameter_count": len(proc.parameters),
                "dependencies": list(proc.dependencies)
            }
        return result
    
    def _serialize_triggers(self, triggers: Dict[str, TriggerInfo]) -> Dict:
        """Serializa triggers a diccionario"""
        result = {}
        for name, trigger in triggers.items():
            result[name] = {
                "schema_name": trigger.schema_name,
                "trigger_name": trigger.trigger_name,
                "table_name": trigger.table_name,
                "trigger_type": trigger.trigger_type,
                "triggering_event": trigger.triggering_event,
                "status": trigger.status
            }
        return result
    
    def _serialize_indexes(self, indexes: Dict[str, IndexInfo]) -> Dict:
        """Serializa índices a diccionario"""
        result = {}
        for name, index in indexes.items():
            if not self._is_system_index(index):
                result[name] = {
                    "schema_name": index.schema_name,
                    "index_name": index.index_name,
                    "table_name": index.table_name,
                    "index_type": index.index_type,
                    "is_unique": index.is_unique,
                    "columns": index.columns
                }
        return result
    
    def _generate_html_report(self, schema_info: SchemaInfo) -> str:
        """Genera un reporte HTML completo"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Reporte de Esquema: {schema_info.schema_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; }}
        .stats {{ display: flex; flex-wrap: wrap; gap: 20px; }}
        .stat-box {{ background-color: #e7f3ff; padding: 15px; border-radius: 5px; min-width: 150px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .object-type {{ color: #0066cc; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Reporte de Esquema: {schema_info.schema_name}</h1>
        <p>Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="section">
        <h2>📈 Estadísticas Generales</h2>
        <div class="stats">
            <div class="stat-box">
                <strong>📊 Tablas</strong><br>
                {len(schema_info.objects.tables)}
            </div>
            <div class="stat-box">
                <strong>👁 Vistas</strong><br>
                {len(schema_info.objects.views)}
            </div>
            <div class="stat-box">
                <strong>🔢 Secuencias</strong><br>
                {len(schema_info.objects.sequences)}
            </div>
            <div class="stat-box">
                <strong>⚙️ Procedimientos</strong><br>
                {len(schema_info.objects.procedures)}
            </div>
            <div class="stat-box">
                <strong>🎯 Triggers</strong><br>
                {len(schema_info.objects.triggers)}
            </div>
            <div class="stat-box">
                <strong>📇 Índices</strong><br>
                {len([idx for idx in schema_info.objects.indexes.values() if not self._is_system_index(idx)])}
            </div>
            <div class="stat-box">
                <strong>💾 Filas Totales</strong><br>
                {sum(t.row_count for t in schema_info.objects.tables.values()):,}
            </div>
        </div>
    </div>
"""
        
        # Agregar detalles de tablas
        if schema_info.objects.tables:
            html += """
    <div class="section">
        <h2 class="object-type">📊 Tablas</h2>
        <table>
            <tr>
                <th>Nombre</th>
                <th>Filas</th>
                <th>Columnas</th>
                <th>Llaves Foráneas</th>
                <th>Dependencias</th>
            </tr>
"""
            for name, table in schema_info.objects.tables.items():
                html += f"""
            <tr>
                <td>{name}</td>
                <td>{table.row_count:,}</td>
                <td>{len(table.columns)}</td>
                <td>{len(table.foreign_keys)}</td>
                <td>{len(table.dependencies)}</td>
            </tr>"""
            
            html += """
        </table>
    </div>
"""
        
        # Agregar otras secciones si existen objetos
        if schema_info.objects.views:
            html += self._add_views_section(schema_info.objects.views)
        
        if schema_info.objects.sequences:
            html += self._add_sequences_section(schema_info.objects.sequences)
        
        html += """
</body>
</html>
"""
        return html
    
    def _add_views_section(self, views: Dict[str, ViewInfo]) -> str:
        """Agrega sección de vistas al HTML"""
        html = """
    <div class="section">
        <h2 class="object-type">👁 Vistas</h2>
        <table>
            <tr>
                <th>Nombre</th>
                <th>Actualizable</th>
                <th>Columnas</th>
                <th>Dependencias</th>
            </tr>
"""
        for name, view in views.items():
            html += f"""
            <tr>
                <td>{name}</td>
                <td>{'Sí' if view.is_updatable else 'No'}</td>
                <td>{len(view.columns)}</td>
                <td>{len(view.dependencies)}</td>
            </tr>"""
        
        html += """
        </table>
    </div>
"""
        return html
    
    def _add_sequences_section(self, sequences: Dict[str, SequenceInfo]) -> str:
        """Agrega sección de secuencias al HTML"""
        html = """
    <div class="section">
        <h2 class="object-type">🔢 Secuencias</h2>
        <table>
            <tr>
                <th>Nombre</th>
                <th>Inicio</th>
                <th>Incremento</th>
                <th>Min</th>
                <th>Max</th>
                <th>Ciclo</th>
            </tr>
"""
        for name, seq in sequences.items():
            html += f"""
            <tr>
                <td>{name}</td>
                <td>{seq.start_value}</td>
                <td>{seq.increment_by}</td>
                <td>{seq.min_value or 'N/A'}</td>
                <td>{seq.max_value or 'N/A'}</td>
                <td>{'Sí' if seq.cycle_flag else 'No'}</td>
            </tr>"""
        
        html += """
        </table>
    </div>
"""
        return html