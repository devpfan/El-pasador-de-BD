"""
Modern GUI - Interfaz gráfica moderna usando CustomTkinter
Versión modernizada con apariencia profesional y temas dark/light
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import tkinter as tk
import logging
import threading
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from pathlib import Path

from database_manager import DatabaseManager
from schema_analyzer import SchemaAnalyzer, SchemaInfo
from dependency_resolver import DependencyResolver
from schema_exporter import SchemaExporter

# Configurar CustomTkinter
ctk.set_appearance_mode("system")  # system, light, dark
ctk.set_default_color_theme("blue")  # blue, green, dark-blue


class ModernConnectionFrame(ctk.CTkFrame):
    """Frame moderno para configuración de conexiones de BD"""
    
    def __init__(self, parent, title: str, connection_type: str):
        super().__init__(parent)
        
        self.connection_type = connection_type
        self.connection_config = {}
        
        # Título con icono
        title_frame = ctk.CTkFrame(self)
        title_frame.pack(fill='x', padx=10, pady=(10, 5))
        
        icon = "🗄️" if connection_type == "source" else "📊"
        title_label = ctk.CTkLabel(
            title_frame, 
            text=f"{icon} {title}", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=10)
        
        # Frame principal de contenido
        content_frame = ctk.CTkFrame(self)
        content_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.setup_connection_ui(content_frame)
        
    def setup_connection_ui(self, parent):
        """Configura la interfaz de conexión moderna"""
        
        # Tipo de BD
        db_type_frame = ctk.CTkFrame(parent)
        db_type_frame.pack(fill='x', padx=15, pady=(15, 10))
        
        ctk.CTkLabel(
            db_type_frame, 
            text="Tipo de Base de Datos:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor='w', padx=10, pady=(10, 5))
        
        self.db_type_var = ctk.StringVar(value="oracle")
        
        # Botones de tipo de BD modernos
        db_buttons_frame = ctk.CTkFrame(db_type_frame)
        db_buttons_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        db_types = [
            ("🔶 Oracle", "oracle"),
            ("🐘 PostgreSQL", "postgresql"),
            ("🐬 MySQL", "mysql"),
            ("🏢 SQL Server", "sqlserver"),
            ("📁 SQLite", "sqlite")
        ]
        
        for i, (text, value) in enumerate(db_types):
            btn = ctk.CTkRadioButton(
                db_buttons_frame,
                text=text,
                variable=self.db_type_var,
                value=value,
                command=self.on_db_type_change
            )
            btn.grid(row=0, column=i, padx=5, pady=5, sticky='w')
        
        # Configurar grid
        db_buttons_frame.grid_columnconfigure(tuple(range(5)), weight=1)
        
        # Campos de conexión
        fields_frame = ctk.CTkFrame(parent)
        fields_frame.pack(fill='x', padx=15, pady=(0, 10))
        
        ctk.CTkLabel(
            fields_frame,
            text="Parámetros de Conexión:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor='w', padx=10, pady=(10, 5))
        
        # Grid para campos
        self.fields_container = ctk.CTkFrame(fields_frame)
        self.fields_container.pack(fill='x', padx=10, pady=(0, 10))
        
        # Crear campos de entrada modernos
        self.create_connection_fields()
        
        # Botones de acción
        buttons_frame = ctk.CTkFrame(parent)
        buttons_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        self.test_btn = ctk.CTkButton(
            buttons_frame,
            text="🔍 Probar Conexión",
            command=self.test_connection,
            height=35,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.test_btn.pack(side='left', padx=(10, 5), pady=10)
        
        self.connect_btn = ctk.CTkButton(
            buttons_frame,
            text="🔗 Conectar",
            command=self.connect,
            height=35,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.connect_btn.pack(side='left', padx=5, pady=10)
        
        # Lista de esquemas
        schemas_frame = ctk.CTkFrame(parent)
        schemas_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        ctk.CTkLabel(
            schemas_frame,
            text="📋 Esquemas Disponibles:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor='w', padx=10, pady=(10, 5))
        
        # Scrollable frame para esquemas
        self.schemas_scroll = ctk.CTkScrollableFrame(schemas_frame, height=200)
        self.schemas_scroll.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Variable para esquema seleccionado
        self.selected_schema_var = ctk.StringVar()
        self.schema_buttons = []
        
    def create_connection_fields(self):
        """Crea los campos de conexión modernos"""
        
        # Limpiar campos existentes
        for widget in self.fields_container.winfo_children():
            widget.destroy()
        
        self.entries = {}
        
        # Campos según el tipo de BD
        db_type = self.db_type_var.get()
        
        if db_type == "sqlite":
            fields = [("📁 Archivo de BD", "database", True)]
        else:
            fields = [
                ("🌐 Servidor", "host", False),
                ("🔌 Puerto", "port", False),
                ("🗄️ Base de Datos", "database", False),
                ("👤 Usuario", "user", False),
                ("🔒 Contraseña", "password", True)
            ]
        
        # Crear campos en grid
        for i, (label_text, field_name, is_password) in enumerate(fields):
            # Label
            label = ctk.CTkLabel(
                self.fields_container,
                text=label_text,
                font=ctk.CTkFont(size=11)
            )
            label.grid(row=i, column=0, sticky='w', padx=(10, 5), pady=5)
            
            # Entry
            if is_password and field_name == "password":
                entry = ctk.CTkEntry(
                    self.fields_container,
                    show="*",
                    height=30
                )
            elif field_name == "database" and db_type == "sqlite":
                # Frame para SQLite con botón browse
                sqlite_frame = ctk.CTkFrame(self.fields_container)
                sqlite_frame.grid(row=i, column=1, sticky='ew', padx=5, pady=5)
                
                entry = ctk.CTkEntry(sqlite_frame, height=30)
                entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
                
                browse_btn = ctk.CTkButton(
                    sqlite_frame,
                    text="📂",
                    width=40,
                    height=30,
                    command=lambda: self.browse_sqlite_file(entry)
                )
                browse_btn.pack(side='right')
            else:
                entry = ctk.CTkEntry(
                    self.fields_container,
                    height=30
                )
                entry.grid(row=i, column=1, sticky='ew', padx=5, pady=5)
            
            # Valores por defecto
            default_values = {
                "oracle": {"host": "localhost", "port": "1521"},
                "postgresql": {"host": "localhost", "port": "5432"},
                "mysql": {"host": "localhost", "port": "3306"},
                "sqlserver": {"host": "localhost", "port": "1433"}
            }
            
            if db_type in default_values and field_name in default_values[db_type]:
                entry.insert(0, default_values[db_type][field_name])
            
            self.entries[field_name] = entry
        
        # Configurar grid weights
        self.fields_container.grid_columnconfigure(1, weight=1)
    
    def browse_sqlite_file(self, entry):
        """Abre diálogo para seleccionar archivo SQLite"""
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo SQLite",
            filetypes=[("SQLite files", "*.db *.sqlite *.sqlite3"), ("All files", "*.*")]
        )
        if filename:
            entry.delete(0, 'end')
            entry.insert(0, filename)
    
    def on_db_type_change(self):
        """Maneja cambio de tipo de BD"""
        self.create_connection_fields()
    
    def test_connection(self):
        """Prueba la conexión a la BD"""
        try:
            config = self.get_connection_config()
            if not config:
                return
            
            # Cambiar botón mientras prueba
            self.test_btn.configure(text="⏳ Probando...", state="disabled")
            
            def test_thread():
                try:
                    from database_manager import DatabaseManager
                    db_manager = DatabaseManager()
                    engine = db_manager.get_engine("test", config['db_type'], config)
                    
                    # Probar conexión
                    with engine.connect() as conn:
                        from sqlalchemy import text
                        conn.execute(text("SELECT 1"))
                    
                    # Actualizar UI en hilo principal
                    self.after(0, lambda: self.on_test_success())
                    
                except Exception as e:
                    self.after(0, lambda: self.on_test_error(str(e)))
            
            threading.Thread(target=test_thread, daemon=True).start()
            
        except Exception as e:
            self.on_test_error(str(e))
    
    def on_test_success(self):
        """Maneja prueba de conexión exitosa"""
        self.test_btn.configure(text="✅ Conexión OK", fg_color="green")
        
        # Restaurar botón después de un delay
        def restore_button():
            self.test_btn.configure(
                text="🔍 Probar Conexión", 
                state="normal",
                fg_color=None  # Usar color por defecto
            )
        
        self.after(2000, restore_button)
        messagebox.showinfo("Conexión Exitosa", "La conexión se estableció correctamente")
    
    def on_test_error(self, error):
        """Maneja error en prueba de conexión"""
        self.test_btn.configure(text="❌ Error", fg_color="red", state="normal")
        
        # Restaurar botón después de un delay
        def restore_button():
            self.test_btn.configure(
                text="🔍 Probar Conexión",
                fg_color=None  # Usar color por defecto
            )
        
        self.after(2000, restore_button)
        messagebox.showerror("Error de Conexión", f"No se pudo conectar:\n{error}")
    
    def connect(self):
        """Establece conexión y carga esquemas"""
        try:
            config = self.get_connection_config()
            if not config:
                return
            
            self.connection_config = config
            
            # Cambiar botón mientras conecta
            self.connect_btn.configure(text="⏳ Conectando...", state="disabled")
            
            def connect_thread():
                try:
                    from database_manager import DatabaseManager
                    db_manager = DatabaseManager()
                    engine = db_manager.get_engine(self.connection_type, config['db_type'], config)
                    
                    # Obtener esquemas
                    schemas = db_manager.get_schemas(engine, config['db_type'])
                    
                    # Actualizar UI en hilo principal
                    self.after(0, lambda: self.on_connect_success(schemas))
                    
                except Exception as e:
                    self.after(0, lambda: self.on_connect_error(str(e)))
            
            threading.Thread(target=connect_thread, daemon=True).start()
            
        except Exception as e:
            self.on_connect_error(str(e))
    
    def on_connect_success(self, schemas):
        """Maneja conexión exitosa y carga esquemas"""
        self.connect_btn.configure(text="✅ Conectado", fg_color="green", state="normal")
        
        # Limpiar esquemas anteriores
        for btn in self.schema_buttons:
            btn.destroy()
        self.schema_buttons.clear()
        
        # Agregar nuevos esquemas como botones radio modernos
        if schemas:
            for schema in sorted(schemas):
                btn = ctk.CTkRadioButton(
                    self.schemas_scroll,
                    text=f"📋 {schema}",
                    variable=self.selected_schema_var,
                    value=schema,
                    font=ctk.CTkFont(size=11)
                )
                btn.pack(anchor='w', padx=10, pady=2)
                self.schema_buttons.append(btn)
        else:
            no_schemas_label = ctk.CTkLabel(
                self.schemas_scroll,
                text="❌ No se encontraron esquemas accesibles",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            no_schemas_label.pack(padx=10, pady=10)
    
    def on_connect_error(self, error):
        """Maneja error de conexión"""
        self.connect_btn.configure(text="❌ Error", fg_color="red", state="normal")
        
        # Restaurar botón después de un delay
        def restore_button():
            self.connect_btn.configure(
                text="🔗 Conectar",
                fg_color=None  # Usar color por defecto
            )
        
        self.after(3000, restore_button)
        messagebox.showerror("Error de Conexión", f"No se pudo conectar:\n{error}")
    
    def get_connection_config(self) -> Optional[Dict]:
        """Obtiene configuración de conexión desde el formulario"""
        db_type = self.db_type_var.get()
        
        config = {"db_type": db_type}
        
        for field_name, entry in self.entries.items():
            value = entry.get().strip()
            if not value and field_name != "password":
                messagebox.showerror("Campo Requerido", f"El campo {field_name} es requerido")
                return None
            config[field_name] = value
        
        return config
    
    def get_selected_schema(self) -> Optional[str]:
        """Obtiene el esquema seleccionado"""
        return self.selected_schema_var.get() or None


class ModernSchemaVisualizationFrame(ctk.CTkFrame):
    """Frame moderno para visualización de esquemas"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.schema_info = None
        
        # Configurar UI
        self.setup_ui()
        
        # Dependency resolver
        from dependency_resolver import DependencyResolver
        self.dependency_resolver = DependencyResolver()
    
    def setup_ui(self):
        """Configura la interfaz moderna de visualización"""
        
        # Título
        title_label = ctk.CTkLabel(
            self,
            text="📊 Análisis de Esquema",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(10, 20))
        
        # Tabview moderno para diferentes vistas
        self.tabview = ctk.CTkTabview(self, width=400, height=300)
        self.tabview.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Pestañas modernas
        self.tabview.add("📈 Resumen")
        self.tabview.add("🔗 Dependencias") 
        self.tabview.add("📋 Orden")
        self.tabview.add("🗂️ Objetos")
        self.tabview.add("⚠️ Problemas")
        
        self.setup_summary_tab()
        self.setup_dependencies_tab()
        self.setup_order_tab()
        self.setup_objects_tab()
        self.setup_problems_tab()
    
    def setup_summary_tab(self):
        """Configura pestaña de resumen moderna"""
        tab = self.tabview.tab("📈 Resumen")
        
        # Frame de estadísticas
        stats_frame = ctk.CTkFrame(tab)
        stats_frame.pack(fill='x', padx=10, pady=10)
        
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="💤 Analiza un esquema para ver estadísticas",
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        self.stats_label.pack(padx=20, pady=20)
        
        # Frame de tablas con scrollbar moderno
        tables_frame = ctk.CTkFrame(tab)
        tables_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        ctk.CTkLabel(
            tables_frame,
            text="📊 Tablas del Esquema",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        # Crear textbox scrollable para tablas
        self.tables_textbox = ctk.CTkTextbox(tables_frame, height=200)
        self.tables_textbox.pack(fill='both', expand=True, padx=10, pady=(0, 10))
    
    def setup_dependencies_tab(self):
        """Configura pestaña de dependencias moderna"""
        tab = self.tabview.tab("🔗 Dependencias")
        
        # Frame de árbol de dependencias
        tree_frame = ctk.CTkFrame(tab)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            tree_frame,
            text="🌳 Árbol de Dependencias",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        self.deps_textbox = ctk.CTkTextbox(tree_frame)
        self.deps_textbox.pack(fill='both', expand=True, padx=10, pady=(0, 10))
    
    def setup_order_tab(self):
        """Configura pestaña de orden moderna"""
        tab = self.tabview.tab("📋 Orden")
        
        order_frame = ctk.CTkFrame(tab)
        order_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            order_frame,
            text="🎯 Orden de Transferencia",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        self.order_textbox = ctk.CTkTextbox(order_frame)
        self.order_textbox.pack(fill='both', expand=True, padx=10, pady=(0, 10))
    
    def setup_objects_tab(self):
        """Configura pestaña de objetos moderna"""
        tab = self.tabview.tab("🗂️ Objetos")
        
        # Sub-tabview para tipos de objetos
        self.objects_tabview = ctk.CTkTabview(tab, width=300, height=250)
        self.objects_tabview.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Sub-pestañas para cada tipo
        object_types = [
            ("📊 Tablas", "tables"),
            ("👁 Vistas", "views"), 
            ("🔢 Secuencias", "sequences"),
            ("⚙️ Procedimientos", "procedures"),
            ("🎯 Triggers", "triggers"),
            ("📇 Índices", "indexes")
        ]
        
        self.object_textboxes = {}
        
        for tab_name, obj_type in object_types:
            self.objects_tabview.add(tab_name)
            
            textbox = ctk.CTkTextbox(self.objects_tabview.tab(tab_name))
            textbox.pack(fill='both', expand=True, padx=5, pady=5)
            
            self.object_textboxes[obj_type] = textbox
    
    def setup_problems_tab(self):
        """Configura pestaña de problemas moderna"""
        tab = self.tabview.tab("⚠️ Problemas")
        
        problems_frame = ctk.CTkFrame(tab)
        problems_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            problems_frame,
            text="🔍 Problemas Detectados",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        self.problems_textbox = ctk.CTkTextbox(problems_frame)
        self.problems_textbox.pack(fill='both', expand=True, padx=10, pady=(0, 10))
    
    def update_schema_info(self, schema_info: SchemaInfo):
        """Actualiza la visualización con nueva información del esquema"""
        self.schema_info = schema_info
        
        self.update_summary_tab()
        self.update_dependencies_tab()
        self.update_order_tab()
        self.update_objects_tab()
        self.update_problems_tab()
    
    def update_summary_tab(self):
        """Actualiza pestaña de resumen"""
        if not self.schema_info:
            return
        
        # Estadísticas modernas con iconos
        stats_text = f"""🎯 ESQUEMA: {self.schema_info.schema_name}

📊 OBJETOS:
   📋 Tablas: {len(self.schema_info.objects.tables)}
   👁 Vistas: {len(self.schema_info.objects.views)}  
   🔢 Secuencias: {len(self.schema_info.objects.sequences)}
   ⚙️ Procedimientos: {len(self.schema_info.objects.procedures)}
   🎯 Triggers: {len(self.schema_info.objects.triggers)}
   📇 Índices: {len(self.schema_info.objects.indexes)}

💾 DATOS:
   📊 Filas totales: {sum(t.row_count for t in self.schema_info.objects.tables.values()):,}
   🔗 Llaves foráneas: {sum(len(t.foreign_keys) for t in self.schema_info.objects.tables.values())}
   📚 Niveles dependencia: {len(set(self.dependency_resolver.create_dependency_graph(self.schema_info).levels.values()))}"""
        
        self.stats_label.configure(text=stats_text)
        
        # Lista de tablas
        self.tables_textbox.delete("0.0", "end")
        
        if self.schema_info.objects.tables:
            tables_info = "TABLA                      FILAS      COLS  FKs  DEPS\n"
            tables_info += "─" * 55 + "\n"
            
            for name, table in self.schema_info.objects.tables.items():
                tables_info += f"{name:<25} {table.row_count:>8,} {len(table.columns):>4} {len(table.foreign_keys):>3} {len(table.dependencies):>4}\n"
        else:
            tables_info = "❌ No se encontraron tablas en el esquema"
        
        self.tables_textbox.insert("0.0", tables_info)
    
    def update_dependencies_tab(self):
        """Actualiza pestaña de dependencias"""
        if not self.schema_info:
            return
        
        self.deps_textbox.delete("0.0", "end")
        
        try:
            # Crear grafo de dependencias
            dep_graph = self.dependency_resolver.create_dependency_graph(self.schema_info)
            
            deps_text = "🌳 ÁRBOL DE DEPENDENCIAS\n"
            deps_text += "═" * 40 + "\n\n"
            
            # Mostrar por niveles
            for level in sorted(set(dep_graph.levels.values())):
                tables_in_level = [name for name, lvl in dep_graph.levels.items() if lvl == level]
                if tables_in_level:
                    deps_text += f"📊 NIVEL {level}:\n"
                    for table in sorted(tables_in_level):
                        deps_text += f"   └─ {table}\n"
                    deps_text += "\n"
            
            # Mostrar ciclos si existen
            if dep_graph.cycles:
                deps_text += "⚠️  CICLOS DETECTADOS:\n"
                for i, cycle in enumerate(dep_graph.cycles, 1):
                    deps_text += f"   🔄 Ciclo {i}: {' → '.join(cycle)}\n"
            
        except Exception as e:
            deps_text = f"❌ Error generando árbol de dependencias:\n{str(e)}"
        
        self.deps_textbox.insert("0.0", deps_text)
    
    def update_order_tab(self):
        """Actualiza pestaña de orden"""
        if not self.schema_info:
            return
        
        self.order_textbox.delete("0.0", "end")
        
        order_text = "🎯 ORDEN DE TRANSFERENCIA\n"
        order_text += "═" * 40 + "\n\n"
        
        for i, table_name in enumerate(self.schema_info.dependency_order, 1):
            if table_name in self.schema_info.objects.tables:
                table_info = self.schema_info.objects.tables[table_name]
                order_text += f"{i:>3}. 📋 {table_name:<25} ({table_info.row_count:,} filas)\n"
        
        self.order_textbox.insert("0.0", order_text)
    
    def update_objects_tab(self):
        """Actualiza pestaña de objetos"""
        if not self.schema_info:
            return
        
        # Tablas
        tables_text = "📊 TABLAS\n" + "═" * 30 + "\n\n"
        for name, table in self.schema_info.objects.tables.items():
            tables_text += f"📋 {name}\n"
            tables_text += f"   📊 Filas: {table.row_count:,}\n"
            tables_text += f"   📄 Columnas: {len(table.columns)}\n"
            tables_text += f"   🔗 FKs: {len(table.foreign_keys)}\n"
            tables_text += f"   📚 Deps: {len(table.dependencies)}\n\n"
        
        self.object_textboxes["tables"].delete("0.0", "end")
        self.object_textboxes["tables"].insert("0.0", tables_text)
        
        # Vistas
        views_text = "👁 VISTAS\n" + "═" * 30 + "\n\n"
        for name, view in self.schema_info.objects.views.items():
            views_text += f"👁 {name}\n"
            views_text += f"   ✏️  Actualizable: {'Sí' if view.is_updatable else 'No'}\n"
            views_text += f"   📄 Columnas: {len(view.columns)}\n"
            views_text += f"   📚 Deps: {len(view.dependencies)}\n\n"
        
        self.object_textboxes["views"].delete("0.0", "end")
        self.object_textboxes["views"].insert("0.0", views_text)
        
        # Secuencias
        sequences_text = "🔢 SECUENCIAS\n" + "═" * 30 + "\n\n"
        for name, seq in self.schema_info.objects.sequences.items():
            sequences_text += f"🔢 {name}\n"
            sequences_text += f"   🎯 Inicio: {seq.start_value}\n"
            sequences_text += f"   ⬆️  Incremento: {seq.increment_by}\n"
            sequences_text += f"   🔄 Ciclo: {'Sí' if seq.cycle_flag else 'No'}\n\n"
        
        self.object_textboxes["sequences"].delete("0.0", "end")
        self.object_textboxes["sequences"].insert("0.0", sequences_text)
        
        # Procedimientos
        procedures_text = "⚙️ PROCEDIMIENTOS\n" + "═" * 30 + "\n\n"
        for name, proc in self.schema_info.objects.procedures.items():
            procedures_text += f"⚙️ {name}\n"
            procedures_text += f"   🏷️  Tipo: {proc.procedure_type}\n"
            procedures_text += f"   🗣️  Lenguaje: {proc.language}\n"
            procedures_text += f"   📋 Parámetros: {len(proc.parameters)}\n\n"
        
        self.object_textboxes["procedures"].delete("0.0", "end")
        self.object_textboxes["procedures"].insert("0.0", procedures_text)
        
        # Triggers
        triggers_text = "🎯 TRIGGERS\n" + "═" * 30 + "\n\n"
        for name, trigger in self.schema_info.objects.triggers.items():
            triggers_text += f"🎯 {name}\n"
            triggers_text += f"   📋 Tabla: {trigger.table_name}\n"
            triggers_text += f"   🏷️  Tipo: {trigger.trigger_type}\n"
            triggers_text += f"   ⚡ Evento: {trigger.triggering_event}\n"
            triggers_text += f"   🔘 Estado: {trigger.status}\n\n"
        
        self.object_textboxes["triggers"].delete("0.0", "end")
        self.object_textboxes["triggers"].insert("0.0", triggers_text)
        
        # Índices
        indexes_text = "📇 ÍNDICES\n" + "═" * 30 + "\n\n"
        for name, index in self.schema_info.objects.indexes.items():
            if not self._is_system_index(index):
                indexes_text += f"📇 {name}\n"
                indexes_text += f"   📋 Tabla: {index.table_name}\n"
                indexes_text += f"   🏷️  Tipo: {index.index_type}\n"
                indexes_text += f"   🔒 Único: {'Sí' if index.is_unique else 'No'}\n"
                indexes_text += f"   📄 Columnas: {', '.join(index.columns)}\n\n"
        
        self.object_textboxes["indexes"].delete("0.0", "end")
        self.object_textboxes["indexes"].insert("0.0", indexes_text)
    
    def update_problems_tab(self):
        """Actualiza pestaña de problemas"""
        if not self.schema_info:
            return
        
        self.problems_textbox.delete("0.0", "end")
        
        # Validar integridad del esquema
        from schema_analyzer import SchemaAnalyzer
        analyzer = SchemaAnalyzer(None)
        issues = analyzer.validate_schema_integrity(self.schema_info)
        
        problems_text = "🔍 PROBLEMAS DETECTADOS\n"
        problems_text += "═" * 40 + "\n\n"
        
        if issues:
            for issue in issues:
                icon = "⚠️" if issue["type"] == "no_primary_key" else "❌"
                problems_text += f"{icon} {issue['type'].upper()}\n"
                problems_text += f"   📋 Tabla: {issue['table']}\n"
                problems_text += f"   📝 Descripción: {issue['description']}\n\n"
        else:
            problems_text += "✅ No se detectaron problemas en el esquema\n"
            problems_text += "🎉 El esquema tiene una estructura válida"
        
        self.problems_textbox.insert("0.0", problems_text)
    
    def _is_system_index(self, index_info) -> bool:
        """Determina si un índice es del sistema"""
        index_name = index_info.index_name.upper()
        return (index_name.startswith('PK_') or 
                index_name.startswith('FK_') or
                index_name.startswith('SYS_'))


class ModernMainGUI:
    """Ventana principal moderna de la aplicación"""
    
    def __init__(self):
        # Crear ventana principal moderna
        self.root = ctk.CTk()
        self.root.title("🚀 Pasador de Esquemas de BD - Versión Moderna")
        self.root.geometry("1400x900")
        
        # Configurar grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Componentes del negocio
        self.db_manager = DatabaseManager()
        self.schema_analyzer = SchemaAnalyzer(self.db_manager)
        self.dependency_resolver = DependencyResolver()
        self.schema_exporter = SchemaExporter()
        
        # Variables de estado
        self.source_schema_info: Optional[SchemaInfo] = None
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        
        # Variables para opciones de análisis (ANTES de configurar UI)
        self.include_views_var = ctk.BooleanVar(value=True)
        self.include_sequences_var = ctk.BooleanVar(value=True)
        self.include_procedures_var = ctk.BooleanVar(value=True)
        self.include_triggers_var = ctk.BooleanVar(value=True)
        self.include_indexes_var = ctk.BooleanVar(value=True)
        
        # Configurar interfaz
        self.setup_ui()
        self.setup_menu()
    
    def setup_ui(self):
        """Configura la interfaz moderna"""
        
        # Frame principal
        main_frame = ctk.CTkFrame(self.root)
        main_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=2)
        
        # Panel izquierdo - Conexiones y controles
        left_panel = ctk.CTkFrame(main_frame)
        left_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        left_panel.grid_rowconfigure(1, weight=1)
        
        # Panel derecho - Visualización
        right_panel = ctk.CTkFrame(main_frame)
        right_panel.grid(row=0, column=1, sticky='nsew')
        right_panel.grid_rowconfigure(0, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)
        
        self.setup_left_panel(left_panel)
        self.setup_right_panel(right_panel)
    
    def setup_left_panel(self, parent):
        """Configura panel izquierdo moderno"""
        
        # Conexión origen
        self.source_frame = ModernConnectionFrame(parent, "Base de Datos Origen", "source")
        self.source_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        
        # Frame de análisis y opciones
        analysis_frame = ctk.CTkFrame(parent)
        analysis_frame.grid(row=1, column=0, sticky='ew', pady=(0, 10))
        
        # Título de análisis
        ctk.CTkLabel(
            analysis_frame,
            text="🔍 Análisis de Esquema",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(15, 10))
        
        # Opciones de objetos a analizar
        options_frame = ctk.CTkFrame(analysis_frame)
        options_frame.pack(fill='x', padx=15, pady=(0, 10))
        
        ctk.CTkLabel(
            options_frame,
            text="Objetos a Incluir:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor='w', padx=10, pady=(10, 5))
        
        # Checkboxes modernos
        options = [
            ("📊 Tablas (siempre)", None, True, False),
            ("👁 Vistas", self.include_views_var, True, True),
            ("🔢 Secuencias", self.include_sequences_var, True, True),
            ("⚙️ Procedimientos", self.include_procedures_var, True, True), 
            ("🎯 Triggers", self.include_triggers_var, True, True),
            ("📇 Índices", self.include_indexes_var, True, True)
        ]
        
        for text, var, default, enabled in options:
            if var:
                checkbox = ctk.CTkCheckBox(
                    options_frame,
                    text=text,
                    variable=var,
                    font=ctk.CTkFont(size=11)
                )
                if not enabled:
                    checkbox.configure(state="disabled")
            else:
                checkbox = ctk.CTkCheckBox(
                    options_frame,
                    text=text,
                    font=ctk.CTkFont(size=11),
                    state="disabled"
                )
                checkbox.select()  # Siempre seleccionado para tablas
            
            checkbox.pack(anchor='w', padx=15, pady=2)
        
        # Botón de análisis moderno
        self.analyze_btn = ctk.CTkButton(
            analysis_frame,
            text="🚀 Analizar Esquema",
            command=self.analyze_schema,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.analyze_btn.pack(fill='x', padx=15, pady=(10, 15))
        
        # Conexión destino
        self.target_frame = ModernConnectionFrame(parent, "Base de Datos Destino", "target")
        self.target_frame.grid(row=2, column=0, sticky='ew', pady=(0, 10))
        
        # Botones de acción modernos
        actions_frame = ctk.CTkFrame(parent)
        actions_frame.grid(row=3, column=0, sticky='ew')
        
        ctk.CTkLabel(
            actions_frame,
            text="🎯 Acciones",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(15, 10))
        
        # Botones de transferencia y exportar
        buttons_frame = ctk.CTkFrame(actions_frame)
        buttons_frame.pack(fill='x', padx=15, pady=(0, 10))
        
        self.select_tables_btn = ctk.CTkButton(
            buttons_frame,
            text="📋 Seleccionar Tablas",
            command=self.select_tables,
            state="disabled",
            height=35
        )
        self.select_tables_btn.pack(fill='x', pady=2)
        
        self.transfer_btn = ctk.CTkButton(
            buttons_frame,
            text="🚀 Iniciar Transferencia",
            command=self.start_transfer,
            state="disabled",
            height=35
        )
        self.transfer_btn.pack(fill='x', pady=2)
        
        self.export_btn = ctk.CTkButton(
            buttons_frame,
            text="📤 Exportar Esquema",
            command=self.show_export_dialog,
            state="disabled",
            height=35
        )
        self.export_btn.pack(fill='x', pady=2)
        
        # Barra de progreso moderna
        self.progress_var = ctk.StringVar(value="🔮 Listo para analizar esquema")
        self.progress_label = ctk.CTkLabel(actions_frame, textvariable=self.progress_var)
        self.progress_label.pack(padx=15, pady=(10, 5))
        
        self.progress_bar = ctk.CTkProgressBar(actions_frame)
        self.progress_bar.pack(fill='x', padx=15, pady=(0, 15))
        self.progress_bar.set(0)
    
    def setup_right_panel(self, parent):
        """Configura panel derecho moderno"""
        
        # Frame de visualización moderno
        self.viz_frame = ModernSchemaVisualizationFrame(parent)
        self.viz_frame.grid(row=0, column=0, sticky='nsew')
    
    def setup_menu(self):
        """Configura menú moderno (usando tkinter tradicional para menús)"""
        # CustomTkinter no tiene menús nativos, usar tkinter
        menubar = tk.Menu(self.root)
        self.root.configure(menu=menubar)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="📁 Archivo", menu=file_menu)
        file_menu.add_command(label="💾 Guardar Config", command=self.save_config)
        file_menu.add_command(label="📂 Cargar Config", command=self.load_config)
        file_menu.add_separator()
        file_menu.add_command(label="🔶 Config Oracle", command=self.load_oracle_config)
        file_menu.add_separator()
        file_menu.add_command(label="🚪 Salir", command=self.root.quit)
        
        # Menú Tema
        theme_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="🎨 Tema", menu=theme_menu)
        theme_menu.add_command(label="🌙 Modo Oscuro", command=lambda: self.change_theme("dark"))
        theme_menu.add_command(label="☀️ Modo Claro", command=lambda: self.change_theme("light"))
        theme_menu.add_command(label="💻 Sistema", command=lambda: self.change_theme("system"))
        
        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="❓ Ayuda", menu=help_menu)
        help_menu.add_command(label="📖 Acerca de", command=self.show_about)
    
    def change_theme(self, theme: str):
        """Cambia el tema de la aplicación"""
        ctk.set_appearance_mode(theme)
        messagebox.showinfo("Tema Cambiado", f"Tema cambiado a: {theme}")
    
    def show_about(self):
        """Muestra información sobre la aplicación"""
        about_text = """🚀 Pasador de Esquemas de BD - Versión Moderna

Una herramienta profesional para migración de esquemas de bases de datos
con interfaz moderna usando CustomTkinter.

✨ Características:
• Interfaz moderna con temas dark/light
• Soporte para múltiples tipos de BD
• Análisis completo de dependencias
• Exportación a múltiples formatos
• Transferencia inteligente de datos

🔧 Tecnologías:
• Python 3.7+
• CustomTkinter (GUI moderna)
• SQLAlchemy (Abstracción de BD)
• Pandas (Manipulación de datos)

© 2025 - Herramienta de migración de esquemas"""
        
        messagebox.showinfo("Acerca de", about_text)
    
    def analyze_schema(self):
        """Analiza el esquema seleccionado con interfaz moderna"""
        selected_schema = self.source_frame.get_selected_schema()
        if not selected_schema:
            messagebox.showerror("Error", "🔍 Selecciona un esquema para analizar")
            return
        
        if not self.source_frame.connection_config:
            messagebox.showerror("Error", "🔌 Conecta primero a la base de datos origen")
            return
        
        # Actualizar UI para mostrar progreso
        self.progress_var.set("🔍 Analizando esquema...")
        self.progress_bar.start()
        self.analyze_btn.configure(text="⏳ Analizando...", state="disabled")
        
        def analyze_thread():
            try:
                config = self.source_frame.connection_config
                engine = self.db_manager.get_engine("source", config['db_type'], config)
                
                # Analizar esquema con opciones seleccionadas
                self.source_schema_info = self.schema_analyzer.analyze_schema(
                    engine, config['db_type'], selected_schema,
                    selected_tables=None,
                    include_views=self.include_views_var.get(),
                    include_procedures=self.include_procedures_var.get(),
                    include_sequences=self.include_sequences_var.get(),
                    include_triggers=self.include_triggers_var.get(),
                    include_indexes=self.include_indexes_var.get()
                )
                
                # Actualizar UI en hilo principal
                self.root.after(0, self.on_analysis_complete)
                
            except Exception as e:
                error_msg = f"Error analizando esquema: {str(e)}"
                self.root.after(0, lambda: self.on_analysis_error(error_msg))
        
        threading.Thread(target=analyze_thread, daemon=True).start()
    
    def on_analysis_complete(self):
        """Maneja la finalización del análisis con estilo moderno"""
        self.progress_bar.stop()
        self.progress_bar.set(1.0)
        self.progress_var.set("✅ Análisis completado")
        self.analyze_btn.configure(text="🚀 Analizar Esquema", state="normal")
        
        if self.source_schema_info:
            # Actualizar visualización
            self.viz_frame.update_schema_info(self.source_schema_info)
            
            # Habilitar botones de acción
            self.select_tables_btn.configure(state="normal")
            self.transfer_btn.configure(state="normal") 
            self.export_btn.configure(state="normal")
            
            # Mostrar resumen moderno
            total_objects = (
                len(self.source_schema_info.objects.tables) +
                len(self.source_schema_info.objects.views) +
                len(self.source_schema_info.objects.sequences) +
                len(self.source_schema_info.objects.procedures) +
                len(self.source_schema_info.objects.triggers) +
                len(self.source_schema_info.objects.indexes)
            )
            
            total_rows = sum(t.row_count for t in self.source_schema_info.objects.tables.values())
            
            messagebox.showinfo("🎉 Análisis Completo", 
                              f"Esquema analizado exitosamente:\n\n"
                              f"📊 Objetos totales: {total_objects}\n"
                              f"📋 Tablas: {len(self.source_schema_info.objects.tables)}\n"
                              f"💾 Filas totales: {total_rows:,}")
    
    def on_analysis_error(self, error_msg: str):
        """Maneja errores en el análisis con estilo moderno"""
        self.progress_bar.stop()
        self.progress_bar.set(0)
        self.progress_var.set("❌ Error en análisis")
        self.analyze_btn.configure(text="🚀 Analizar Esquema", state="normal")
        messagebox.showerror("💥 Error de Análisis", error_msg)
    
    # Métodos placeholder para funcionalidades existentes
    def select_tables(self):
        """Placeholder para selección de tablas"""
        messagebox.showinfo("🚧 En Desarrollo", 
                          "Funcionalidad de selección de tablas\n"
                          "será implementada próximamente")
    
    def start_transfer(self):
        """Placeholder para transferencia"""
        messagebox.showinfo("🚧 En Desarrollo",
                          "Funcionalidad de transferencia\n" 
                          "será implementada próximamente")
    
    def show_export_dialog(self):
        """Placeholder para diálogo de exportar"""
        messagebox.showinfo("🚧 En Desarrollo",
                          "Funcionalidad de exportación\n"
                          "será implementada próximamente")
    
    def save_config(self):
        """Placeholder para guardar config"""
        messagebox.showinfo("💾 Guardar Config", "Funcionalidad próximamente")
    
    def load_config(self):
        """Placeholder para cargar config"""  
        messagebox.showinfo("📂 Cargar Config", "Funcionalidad próximamente")
    
    def load_oracle_config(self):
        """Placeholder para config Oracle"""
        messagebox.showinfo("🔶 Config Oracle", "Funcionalidad próximamente")
    
    def run(self):
        """Ejecuta la aplicación moderna"""
        try:
            self.root.mainloop()
        finally:
            # Limpiar recursos
            self.db_manager.close_all_connections()


# Alias para compatibilidad
MainGUI = ModernMainGUI


if __name__ == "__main__":
    app = ModernMainGUI()
    app.run()