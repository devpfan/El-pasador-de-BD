"""
Main GUI - Interfaz gráfica principal para la transferencia de esquemas de BD
Incluye conexiones, análisis, visualización de dependencias y configuración de transferencia
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
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


class ConnectionFrame(ttk.LabelFrame):
    """Frame para configurar conexiones de base de datos"""
    
    def __init__(self, parent, title: str, connection_id: str):
        super().__init__(parent, text=title, padding="10")
        self.connection_id = connection_id
        self.connection_config = {}
        self.schemas = []
        self.selected_schema = tk.StringVar()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz de conexión"""
        
        # Tipo de base de datos
        ttk.Label(self, text="Tipo de BD:").grid(row=0, column=0, sticky='w', padx=(0, 5))
        self.db_type = ttk.Combobox(self, values=['PostgreSQL', 'MySQL', 'SQL Server', 'Oracle', 'SQLite'], 
                                   state='readonly', width=15)
        self.db_type.grid(row=0, column=1, sticky='ew', padx=(0, 10))
        self.db_type.bind('<<ComboboxSelected>>', self.on_db_type_changed)
        
        # Host
        ttk.Label(self, text="Host:").grid(row=1, column=0, sticky='w', padx=(0, 5))
        self.host_entry = ttk.Entry(self, width=20)
        self.host_entry.grid(row=1, column=1, sticky='ew', padx=(0, 10))
        self.host_entry.insert(0, "localhost")
        
        # Puerto
        ttk.Label(self, text="Puerto:").grid(row=2, column=0, sticky='w', padx=(0, 5))
        self.port_entry = ttk.Entry(self, width=20)
        self.port_entry.grid(row=2, column=1, sticky='ew', padx=(0, 10))
        
        # Base de datos
        ttk.Label(self, text="Base de datos:").grid(row=3, column=0, sticky='w', padx=(0, 5))
        self.database_frame = ttk.Frame(self)
        self.database_frame.grid(row=3, column=1, sticky='ew', padx=(0, 10))
        
        self.database_entry = ttk.Entry(self.database_frame, width=15)
        self.database_entry.pack(side='left', fill='x', expand=True)
        
        self.browse_btn = ttk.Button(self.database_frame, text="...", width=3,
                                    command=self.browse_database)
        self.browse_btn.pack(side='right', padx=(5, 0))
        
        # Usuario
        ttk.Label(self, text="Usuario:").grid(row=4, column=0, sticky='w', padx=(0, 5))
        self.user_entry = ttk.Entry(self, width=20)
        self.user_entry.grid(row=4, column=1, sticky='ew', padx=(0, 10))
        
        # Contraseña
        ttk.Label(self, text="Contraseña:").grid(row=5, column=0, sticky='w', padx=(0, 5))
        self.password_entry = ttk.Entry(self, show="*", width=20)
        self.password_entry.grid(row=5, column=1, sticky='ew', padx=(0, 10))
        
        # Botones
        button_frame = ttk.Frame(self)
        button_frame.grid(row=6, column=0, columnspan=2, pady=(10, 0))
        
        self.test_btn = ttk.Button(button_frame, text="Probar Conexión", 
                                  command=self.test_connection)
        self.test_btn.pack(side='left', padx=(0, 5))
        
        self.connect_btn = ttk.Button(button_frame, text="Conectar", 
                                     command=self.connect)
        self.connect_btn.pack(side='left')
        
        # Esquemas disponibles
        ttk.Label(self, text="Esquemas:").grid(row=7, column=0, sticky='nw', padx=(0, 5), pady=(10, 0))
        
        schema_frame = ttk.Frame(self)
        schema_frame.grid(row=7, column=1, sticky='ew', padx=(0, 10), pady=(10, 0))
        
        self.schema_listbox = tk.Listbox(schema_frame, height=4, selectmode='single')
        self.schema_listbox.pack(side='left', fill='both', expand=True)
        
        schema_scroll = ttk.Scrollbar(schema_frame, orient='vertical', 
                                     command=self.schema_listbox.yview)
        schema_scroll.pack(side='right', fill='y')
        self.schema_listbox.config(yscrollcommand=schema_scroll.set)
        
        # Status
        self.status_label = ttk.Label(self, text="No conectado", foreground='red')
        self.status_label.grid(row=8, column=0, columnspan=2, pady=(5, 0))
        
        # Configurar expansión de columnas
        self.columnconfigure(1, weight=1)
        
        self.on_db_type_changed()
    
    def on_db_type_changed(self, event=None):
        """Maneja cambios en el tipo de base de datos"""
        db_type = self.db_type.get().lower()
        
        # Configurar puerto por defecto
        default_ports = {
            'postgresql': '5432',
            'mysql': '3306',
            'sql server': '1433',
            'oracle': '1521',
            'sqlite': ''
        }
        
        self.port_entry.delete(0, tk.END)
        if db_type in default_ports:
            self.port_entry.insert(0, default_ports[db_type])
        
        # Habilitar/deshabilitar campos según el tipo
        if db_type == 'sqlite':
            self.host_entry.config(state='disabled')
            self.port_entry.config(state='disabled')
            self.user_entry.config(state='disabled')
            self.password_entry.config(state='disabled')
            self.browse_btn.config(state='normal')
        else:
            self.host_entry.config(state='normal')
            self.port_entry.config(state='normal')
            self.user_entry.config(state='normal')
            self.password_entry.config(state='normal')
            self.browse_btn.config(state='disabled')
    
    def browse_database(self):
        """Busca archivo de base de datos SQLite"""
        filename = filedialog.askopenfilename(
            title="Seleccionar base de datos SQLite",
            filetypes=[("SQLite files", "*.db *.sqlite *.sqlite3"), ("All files", "*.*")]
        )
        if filename:
            self.database_entry.delete(0, tk.END)
            self.database_entry.insert(0, filename)
    
    def get_connection_config(self) -> Dict[str, str]:
        """Obtiene la configuración de conexión"""
        config = {
            'db_type': self.db_type.get(),
            'host': self.host_entry.get(),
            'port': self.port_entry.get(),
            'database': self.database_entry.get(),
            'user': self.user_entry.get(),
            'password': self.password_entry.get()
        }
        return config
    
    def test_connection(self):
        """Prueba la conexión a la base de datos"""
        config = self.get_connection_config()
        
        if not config['db_type']:
            messagebox.showerror("Error", "Selecciona el tipo de base de datos")
            return
        
        if not config['database']:
            messagebox.showerror("Error", "Ingresa el nombre de la base de datos")
            return
        
        try:
            from main_gui import MainGUI
            app = self.winfo_toplevel().app
            success, message = app.db_manager.test_connection(config['db_type'], config)
            
            if success:
                messagebox.showinfo("Éxito", message)
                self.status_label.config(text="Conexión exitosa", foreground='green')
            else:
                messagebox.showerror("Error", message)
                self.status_label.config(text="Error de conexión", foreground='red')
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al probar conexión: {str(e)}")
    
    def connect(self):
        """Conecta y carga esquemas disponibles"""
        config = self.get_connection_config()
        
        try:
            from main_gui import MainGUI
            app = self.winfo_toplevel().app
            engine = app.db_manager.get_engine(self.connection_id, config['db_type'], config)
            schemas = app.db_manager.get_schemas(engine, config['db_type'])
            
            # Actualizar lista de esquemas
            self.schema_listbox.delete(0, tk.END)
            for schema in schemas:
                self.schema_listbox.insert(tk.END, schema)
            
            self.connection_config = config
            self.schemas = schemas
            self.status_label.config(text=f"Conectado - {len(schemas)} esquemas", foreground='green')
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al conectar: {str(e)}")
            self.status_label.config(text="Error de conexión", foreground='red')
    
    def get_selected_schema(self) -> Optional[str]:
        """Obtiene el esquema seleccionado"""
        selection = self.schema_listbox.curselection()
        if selection:
            return self.schema_listbox.get(selection[0])
        return None


class TableSelectionDialog:
    """Diálogo para seleccionar tablas específicas"""
    
    def __init__(self, parent, tables: List[str], title: str = "Seleccionar Tablas"):
        self.parent = parent
        self.tables = tables
        self.selected_tables = []
        self.result = None
        
        self.setup_dialog(title)
    
    def setup_dialog(self, title: str):
        """Configura el diálogo de selección"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(title)
        self.dialog.geometry("400x500")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Frame principal
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Lista de tablas con checkboxes
        ttk.Label(main_frame, text="Selecciona las tablas a transferir:").pack(anchor='w')
        
        # Frame para la lista con scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill='both', expand=True, pady=(10, 0))
        
        # Canvas y scrollbar para manejar muchas tablas
        canvas = tk.Canvas(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Variables para checkboxes
        self.table_vars = {}
        for table in self.tables:
            var = tk.BooleanVar()
            checkbox = ttk.Checkbutton(scrollable_frame, text=table, variable=var)
            checkbox.pack(anchor='w', padx=5, pady=2)
            self.table_vars[table] = var
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Botones de selección
        select_frame = ttk.Frame(main_frame)
        select_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(select_frame, text="Seleccionar Todo", 
                  command=self.select_all).pack(side='left', padx=(0, 5))
        ttk.Button(select_frame, text="Deseleccionar Todo", 
                  command=self.deselect_all).pack(side='left')
        
        # Botones de acción
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(button_frame, text="Aceptar", 
                  command=self.accept).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="Cancelar", 
                  command=self.cancel).pack(side='right')
        
        # Centrar diálogo
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def select_all(self):
        """Selecciona todas las tablas"""
        for var in self.table_vars.values():
            var.set(True)
    
    def deselect_all(self):
        """Deselecciona todas las tablas"""
        for var in self.table_vars.values():
            var.set(False)
    
    def accept(self):
        """Acepta la selección"""
        self.selected_tables = [
            table for table, var in self.table_vars.items() 
            if var.get()
        ]
        self.result = 'accepted'
        self.dialog.destroy()
    
    def cancel(self):
        """Cancela la selección"""
        self.result = 'cancelled'
        self.dialog.destroy()
    
    def show(self) -> Optional[List[str]]:
        """Muestra el diálogo y retorna las tablas seleccionadas"""
        self.dialog.wait_window()
        if self.result == 'accepted':
            return self.selected_tables
        return None


class SchemaVisualizationFrame(ttk.LabelFrame):
    """Frame para visualizar información del esquema y dependencias"""
    
    def __init__(self, parent):
        super().__init__(parent, text="Análisis del Esquema", padding="10")
        self.schema_info: Optional[SchemaInfo] = None
        self.dependency_resolver = DependencyResolver()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz de visualización"""
        
        # Notebook para diferentes vistas
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)
        
        # Pestaña de resumen
        self.summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_frame, text="Resumen")
        self.setup_summary_tab()
        
        # Pestaña de dependencias
        self.deps_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.deps_frame, text="Dependencias")
        self.setup_dependencies_tab()
        
        # Pestaña de orden de transferencia
        self.order_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.order_frame, text="Orden de Transferencia")
        self.setup_order_tab()
        
        # Pestaña de todos los objetos
        self.objects_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.objects_frame, text="Todos los Objetos")
        self.setup_objects_tab()
        
        # Pestaña de problemas
        self.issues_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.issues_frame, text="Problemas")
        self.setup_issues_tab()
    
    def setup_summary_tab(self):
        """Configura la pestaña de resumen"""
        
        # Información general
        info_frame = ttk.LabelFrame(self.summary_frame, text="Información General", padding="5")
        info_frame.pack(fill='x', pady=(0, 10))
        
        self.info_text = tk.Text(info_frame, height=6, wrap='word')
        self.info_text.pack(fill='x')
        
        # Lista de tablas
        tables_frame = ttk.LabelFrame(self.summary_frame, text="Tablas", padding="5")
        tables_frame.pack(fill='both', expand=True)
        
        # Treeview para mostrar tablas con información
        columns = ('Tabla', 'Filas', 'Columnas', 'FK', 'Dependencias')
        self.tables_tree = ttk.Treeview(tables_frame, columns=columns, show='headings')
        
        for col in columns:
            self.tables_tree.heading(col, text=col)
            self.tables_tree.column(col, width=100)
        
        # Scrollbars para el treeview
        v_scroll = ttk.Scrollbar(tables_frame, orient='vertical', command=self.tables_tree.yview)
        h_scroll = ttk.Scrollbar(tables_frame, orient='horizontal', command=self.tables_tree.xview)
        self.tables_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.tables_tree.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')
        
        tables_frame.grid_rowconfigure(0, weight=1)
        tables_frame.grid_columnconfigure(0, weight=1)
    
    def setup_dependencies_tab(self):
        """Configura la pestaña de dependencias"""
        
        # Árbol de dependencias
        tree_frame = ttk.LabelFrame(self.deps_frame, text="Árbol de Dependencias", padding="5")
        tree_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        self.deps_tree = ttk.Treeview(tree_frame, show='tree')
        
        deps_scroll = ttk.Scrollbar(tree_frame, orient='vertical', command=self.deps_tree.yview)
        self.deps_tree.configure(yscrollcommand=deps_scroll.set)
        
        self.deps_tree.pack(side='left', fill='both', expand=True)
        deps_scroll.pack(side='right', fill='y')
        
        # Información de dependencias seleccionadas
        detail_frame = ttk.LabelFrame(self.deps_frame, text="Detalles", padding="5")
        detail_frame.pack(fill='x')
        
        self.deps_detail = tk.Text(detail_frame, height=6, wrap='word')
        self.deps_detail.pack(fill='x')
        
        # Bind para mostrar detalles
        self.deps_tree.bind('<<TreeviewSelect>>', self.on_dependency_select)
    
    def setup_order_tab(self):
        """Configura la pestaña de orden de transferencia"""
        
        # Lista ordenada
        order_frame = ttk.LabelFrame(self.order_frame, text="Orden de Inserción", padding="5")
        order_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Treeview para mostrar orden con niveles
        columns = ('Orden', 'Nivel', 'Tabla', 'Filas', 'Tiempo Est.')
        self.order_tree = ttk.Treeview(order_frame, columns=columns, show='headings')
        
        for col in columns:
            self.order_tree.heading(col, text=col)
            self.order_tree.column(col, width=80)
        
        order_scroll = ttk.Scrollbar(order_frame, orient='vertical', command=self.order_tree.yview)
        self.order_tree.configure(yscrollcommand=order_scroll.set)
        
        self.order_tree.pack(side='left', fill='both', expand=True)
        order_scroll.pack(side='right', fill='y')
        
        # Botones de optimización
        opt_frame = ttk.Frame(self.order_frame)
        opt_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(opt_frame, text="Optimizar Orden", 
                  command=self.optimize_order).pack(side='left', padx=(0, 5))
        ttk.Button(opt_frame, text="Exportar Plan", 
                  command=self.export_plan).pack(side='left')
    
    def setup_objects_tab(self):
        """Configura la pestaña de todos los objetos"""
        
        # Crear notebook interno para categorizar objetos
        objects_notebook = ttk.Notebook(self.objects_frame)
        objects_notebook.pack(fill='both', expand=True)
        
        # Pestaña de tablas
        tables_frame = ttk.Frame(objects_notebook)
        objects_notebook.add(tables_frame, text="📊 Tablas")
        
        columns = ('Tabla', 'Filas', 'Columnas', 'FK', 'Dependencias')
        self.objects_tables_tree = ttk.Treeview(tables_frame, columns=columns, show='headings')
        
        for col in columns:
            self.objects_tables_tree.heading(col, text=col)
            self.objects_tables_tree.column(col, width=100)
        
        tables_scroll = ttk.Scrollbar(tables_frame, orient='vertical', command=self.objects_tables_tree.yview)
        self.objects_tables_tree.configure(yscrollcommand=tables_scroll.set)
        self.objects_tables_tree.pack(side='left', fill='both', expand=True)
        tables_scroll.pack(side='right', fill='y')
        
        # Pestaña de vistas
        views_frame = ttk.Frame(objects_notebook)
        objects_notebook.add(views_frame, text="👁 Vistas")
        
        columns = ('Vista', 'Actualizable', 'Dependencias', 'Columnas')
        self.objects_views_tree = ttk.Treeview(views_frame, columns=columns, show='headings')
        
        for col in columns:
            self.objects_views_tree.heading(col, text=col)
            self.objects_views_tree.column(col, width=150)
        
        views_scroll = ttk.Scrollbar(views_frame, orient='vertical', command=self.objects_views_tree.yview)
        self.objects_views_tree.configure(yscrollcommand=views_scroll.set)
        self.objects_views_tree.pack(side='left', fill='both', expand=True)
        views_scroll.pack(side='right', fill='y')
        
        # Pestaña de secuencias
        sequences_frame = ttk.Frame(objects_notebook)
        objects_notebook.add(sequences_frame, text="🔢 Secuencias")
        
        columns = ('Secuencia', 'Inicio', 'Incremento', 'Min', 'Max', 'Ciclo')
        self.objects_sequences_tree = ttk.Treeview(sequences_frame, columns=columns, show='headings')
        
        for col in columns:
            self.objects_sequences_tree.heading(col, text=col)
            self.objects_sequences_tree.column(col, width=100)
        
        sequences_scroll = ttk.Scrollbar(sequences_frame, orient='vertical', command=self.objects_sequences_tree.yview)
        self.objects_sequences_tree.configure(yscrollcommand=sequences_scroll.set)
        self.objects_sequences_tree.pack(side='left', fill='both', expand=True)
        sequences_scroll.pack(side='right', fill='y')
        
        # Pestaña de procedimientos
        procedures_frame = ttk.Frame(objects_notebook)
        objects_notebook.add(procedures_frame, text="⚙️ Procedimientos")
        
        columns = ('Nombre', 'Tipo', 'Lenguaje', 'Parámetros', 'Dependencias')
        self.objects_procedures_tree = ttk.Treeview(procedures_frame, columns=columns, show='headings')
        
        for col in columns:
            self.objects_procedures_tree.heading(col, text=col)
            self.objects_procedures_tree.column(col, width=120)
        
        procedures_scroll = ttk.Scrollbar(procedures_frame, orient='vertical', command=self.objects_procedures_tree.yview)
        self.objects_procedures_tree.configure(yscrollcommand=procedures_scroll.set)
        self.objects_procedures_tree.pack(side='left', fill='both', expand=True)
        procedures_scroll.pack(side='right', fill='y')
        
        # Pestaña de triggers
        triggers_frame = ttk.Frame(objects_notebook)
        objects_notebook.add(triggers_frame, text="🎯 Triggers")
        
        columns = ('Trigger', 'Tabla', 'Tipo', 'Evento', 'Estado')
        self.objects_triggers_tree = ttk.Treeview(triggers_frame, columns=columns, show='headings')
        
        for col in columns:
            self.objects_triggers_tree.heading(col, text=col)
            self.objects_triggers_tree.column(col, width=120)
        
        triggers_scroll = ttk.Scrollbar(triggers_frame, orient='vertical', command=self.objects_triggers_tree.yview)
        self.objects_triggers_tree.configure(yscrollcommand=triggers_scroll.set)
        self.objects_triggers_tree.pack(side='left', fill='both', expand=True)
        triggers_scroll.pack(side='right', fill='y')
        
        # Pestaña de índices
        indexes_frame = ttk.Frame(objects_notebook)
        objects_notebook.add(indexes_frame, text="📇 Índices")
        
        columns = ('Índice', 'Tabla', 'Tipo', 'Único', 'Columnas')
        self.objects_indexes_tree = ttk.Treeview(indexes_frame, columns=columns, show='headings')
        
        for col in columns:
            self.objects_indexes_tree.heading(col, text=col)
            if col == 'Columnas':
                self.objects_indexes_tree.column(col, width=200)
            else:
                self.objects_indexes_tree.column(col, width=120)
        
        indexes_scroll = ttk.Scrollbar(indexes_frame, orient='vertical', command=self.objects_indexes_tree.yview)
        self.objects_indexes_tree.configure(yscrollcommand=indexes_scroll.set)
        self.objects_indexes_tree.pack(side='left', fill='both', expand=True)
        indexes_scroll.pack(side='right', fill='y')

    def setup_issues_tab(self):
        """Configura la pestaña de problemas"""
        
        issues_frame = ttk.LabelFrame(self.issues_frame, text="Problemas Detectados", padding="5")
        issues_frame.pack(fill='both', expand=True)
        
        # Treeview para mostrar problemas
        columns = ('Tipo', 'Tabla', 'Descripción')
        self.issues_tree = ttk.Treeview(issues_frame, columns=columns, show='headings')
        
        for col in columns:
            self.issues_tree.heading(col, text=col)
            if col == 'Descripción':
                self.issues_tree.column(col, width=300)
            else:
                self.issues_tree.column(col, width=100)
        
        issues_scroll = ttk.Scrollbar(issues_frame, orient='vertical', command=self.issues_tree.yview)
        self.issues_tree.configure(yscrollcommand=issues_scroll.set)
        
        self.issues_tree.pack(side='left', fill='both', expand=True)
        issues_scroll.pack(side='right', fill='y')
    
    def update_schema_info(self, schema_info: SchemaInfo):
        """Actualiza la visualización con nueva información del esquema"""
        self.schema_info = schema_info
        
        self.update_summary_tab()
        self.update_dependencies_tab()
        self.update_order_tab()
        self.update_objects_tab()
        self.update_issues_tab()
    
    def update_summary_tab(self):
        """Actualiza la pestaña de resumen"""
        if not self.schema_info:
            return
        
        # Información general - todos los objetos
        total_tables = len(self.schema_info.objects.tables)
        total_views = len(self.schema_info.objects.views)
        total_sequences = len(self.schema_info.objects.sequences)
        total_procedures = len(self.schema_info.objects.procedures)
        total_triggers = len(self.schema_info.objects.triggers)
        total_indexes = len(self.schema_info.objects.indexes)
        
        total_rows = sum(table.row_count for table in self.schema_info.objects.tables.values())
        total_fks = sum(len(table.foreign_keys) for table in self.schema_info.objects.tables.values())
        
        info_text = f"""Esquema: {self.schema_info.schema_name}

=== OBJETOS DEL ESQUEMA ===
📊 Tablas: {total_tables}
👁 Vistas: {total_views}
🔢 Secuencias: {total_sequences}
⚙️ Procedimientos/Funciones: {total_procedures}
🎯 Triggers: {total_triggers}
📇 Índices: {total_indexes}

=== ESTADÍSTICAS DE DATOS ===
Filas totales: {total_rows:,}
Llaves foráneas: {total_fks}
Niveles de dependencia: {len(set(self.dependency_resolver.create_dependency_graph(self.schema_info).levels.values()))}
"""
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info_text)
        
        # Lista de tablas
        for item in self.tables_tree.get_children():
            self.tables_tree.delete(item)
        
        for table_name, table_info in self.schema_info.objects.tables.items():
            self.tables_tree.insert('', 'end', values=(
                table_name,
                f"{table_info.row_count:,}",
                len(table_info.columns),
                len(table_info.foreign_keys),
                len(table_info.dependencies)
            ))
    
    def update_dependencies_tab(self):
        """Actualiza la pestaña de dependencias"""
        if not self.schema_info:
            return
        
        # Limpiar árbol existente
        for item in self.deps_tree.get_children():
            self.deps_tree.delete(item)
        
        try:
            # Crear árbol de dependencias
            dep_tree = self.dependency_resolver.create_dependency_tree(self.schema_info)
            
            # Agregar nodos al treeview de forma recursiva
            def add_tree_nodes(node_id, parent_id=''):
                node = dep_tree.get_node(node_id)
                item_id = self.deps_tree.insert(parent_id, 'end', text=node.tag)
                
                # Obtener hijos usando el método correcto de treelib
                children = dep_tree.children(node_id)
                for child in children:
                    add_tree_nodes(child.identifier, item_id)
            
            # Agregar raíz y sus hijos si el árbol no está vacío
            if dep_tree.root is not None:
                add_tree_nodes(dep_tree.root)
            else:
                self.deps_tree.insert('', 'end', text="📋 Sin dependencias detectadas")
            
        except Exception as e:
            # Log del error para debug
            import logging
            logging.getLogger(__name__).error(f"Error en árbol de dependencias: {e}", exc_info=True)
            
            # Mostrar información básica de dependencias como fallback
            try:
                self.deps_tree.insert('', 'end', text="📊 Vista Simplificada de Dependencias")
                
                # Agrupar tablas por número de dependencias
                dependency_graph = self.dependency_resolver.create_dependency_graph(self.schema_info)
                
                # Tablas sin dependencias (raíces)
                root_tables = [table for table, deps in dependency_graph.nodes.items() if not deps]
                if root_tables:
                    root_item = self.deps_tree.insert('', 'end', text="🌱 Tablas Raíz (sin dependencias)")
                    for table in sorted(root_tables):
                        self.deps_tree.insert(root_item, 'end', text=f"📋 {table}")
                
                # Tablas con dependencias
                dep_tables = [table for table, deps in dependency_graph.nodes.items() if deps]
                if dep_tables:
                    dep_item = self.deps_tree.insert('', 'end', text="🔗 Tablas con Dependencias")
                    for table in sorted(dep_tables):
                        dep_count = len(dependency_graph.nodes[table])
                        self.deps_tree.insert(dep_item, 'end', text=f"📋 {table} ({dep_count} deps)")
                
                # Ciclos detectados
                if dependency_graph.cycles:
                    cycles_item = self.deps_tree.insert('', 'end', text="🔄 Dependencias Circulares")
                    for i, cycle in enumerate(dependency_graph.cycles, 1):
                        cycle_text = " → ".join(cycle[:3]) + ("..." if len(cycle) > 3 else "")
                        self.deps_tree.insert(cycles_item, 'end', text=f"⚠️ Ciclo {i}: {cycle_text}")
                
            except Exception as fallback_error:
                self.deps_tree.insert('', 'end', text=f"❌ Error: {str(e)}")
                self.deps_tree.insert('', 'end', text="💡 Usa la pestaña 'Orden' para ver dependencias básicas")
    
    def update_order_tab(self):
        """Actualiza la pestaña de orden"""
        if not self.schema_info:
            return
        
        # Limpiar orden existente
        for item in self.order_tree.get_children():
            self.order_tree.delete(item)
        
        # Crear grafo de dependencias y obtener niveles
        dep_graph = self.dependency_resolver.create_dependency_graph(self.schema_info)
        
        # Agregar tablas en orden
        for i, table_name in enumerate(self.schema_info.dependency_order):
            if table_name in self.schema_info.objects.tables:
                table_info = self.schema_info.objects.tables[table_name]
                level = dep_graph.levels.get(table_name, 0)
                
                # Estimar tiempo (muy básico)
                est_time = table_info.row_count * 0.001  # 1ms por fila
                
                self.order_tree.insert('', 'end', values=(
                    i + 1,
                    level,
                    table_name,
                    f"{table_info.row_count:,}",
                    f"{est_time:.1f}s"
                ))
    
    def update_objects_tab(self):
        """Actualiza la pestaña de todos los objetos"""
        if not self.schema_info:
            return
        
        # Actualizar tablas
        for item in self.objects_tables_tree.get_children():
            self.objects_tables_tree.delete(item)
        
        for table_name, table_info in self.schema_info.objects.tables.items():
            self.objects_tables_tree.insert('', 'end', values=(
                table_name,
                f"{table_info.row_count:,}",
                len(table_info.columns),
                len(table_info.foreign_keys),
                len(table_info.dependencies)
            ))
        
        # Actualizar vistas
        for item in self.objects_views_tree.get_children():
            self.objects_views_tree.delete(item)
        
        for view_name, view_info in self.schema_info.objects.views.items():
            self.objects_views_tree.insert('', 'end', values=(
                view_name,
                "Sí" if view_info.is_updatable else "No",
                len(view_info.dependencies),
                len(view_info.columns)
            ))
        
        # Actualizar secuencias
        for item in self.objects_sequences_tree.get_children():
            self.objects_sequences_tree.delete(item)
        
        for seq_name, seq_info in self.schema_info.objects.sequences.items():
            self.objects_sequences_tree.insert('', 'end', values=(
                seq_name,
                seq_info.start_value,
                seq_info.increment_by,
                seq_info.min_value or "N/A",
                seq_info.max_value or "N/A",
                "Sí" if seq_info.cycle_flag else "No"
            ))
        
        # Actualizar procedimientos
        for item in self.objects_procedures_tree.get_children():
            self.objects_procedures_tree.delete(item)
        
        for proc_name, proc_info in self.schema_info.objects.procedures.items():
            self.objects_procedures_tree.insert('', 'end', values=(
                proc_name,
                proc_info.procedure_type,
                proc_info.language,
                len(proc_info.parameters),
                len(proc_info.dependencies)
            ))
        
        # Actualizar triggers
        for item in self.objects_triggers_tree.get_children():
            self.objects_triggers_tree.delete(item)
        
        for trigger_name, trigger_info in self.schema_info.objects.triggers.items():
            self.objects_triggers_tree.insert('', 'end', values=(
                trigger_name,
                trigger_info.table_name,
                trigger_info.trigger_type,
                trigger_info.triggering_event,
                trigger_info.status
            ))
        
        # Actualizar índices (solo los no automáticos)
        for item in self.objects_indexes_tree.get_children():
            self.objects_indexes_tree.delete(item)
        
        for index_name, index_info in self.schema_info.objects.indexes.items():
            # Filtrar índices del sistema
            if not self._is_system_index(index_info):
                self.objects_indexes_tree.insert('', 'end', values=(
                    index_name,
                    index_info.table_name,
                    index_info.index_type,
                    "Sí" if index_info.is_unique else "No",
                    ", ".join(index_info.columns)
                ))
    
    def _is_system_index(self, index_info) -> bool:
        """Determina si un índice es del sistema"""
        index_name = index_info.index_name.upper()
        return (index_name.startswith('PK_') or 
                index_name.startswith('FK_') or
                index_name.startswith('SYS_'))

    def update_issues_tab(self):
        """Actualiza la pestaña de problemas"""
        if not self.schema_info:
            return
        
        # Limpiar problemas existentes
        for item in self.issues_tree.get_children():
            self.issues_tree.delete(item)
        
        # Validar integridad del esquema
        analyzer = SchemaAnalyzer(None)  # No necesitamos db_manager para validación
        issues = analyzer.validate_schema_integrity(self.schema_info)
        
        for issue in issues:
            self.issues_tree.insert('', 'end', values=(
                issue['type'],
                issue.get('table', 'N/A'),
                issue['description']
            ))
        
        # Detectar ciclos
        dep_graph = self.dependency_resolver.create_dependency_graph(self.schema_info)
        for i, cycle in enumerate(dep_graph.cycles):
            self.issues_tree.insert('', 'end', values=(
                'circular_dependency',
                ' -> '.join(cycle),
                f'Dependencia circular detectada: {" -> ".join(cycle)}'
            ))
    
    def on_dependency_select(self, event):
        """Maneja la selección en el árbol de dependencias"""
        selection = self.deps_tree.selection()
        if not selection or not self.schema_info:
            return
        
        table_name = self.deps_tree.item(selection[0], 'text')
        
        if table_name in self.schema_info.objects.tables:
            table_info = self.schema_info.objects.tables[table_name]
            
            # Mostrar detalles de la tabla
            deps = self.dependency_resolver.get_table_dependencies(self.schema_info, table_name)
            
            detail_text = f"""Tabla: {table_name}
Filas: {table_info.row_count:,}
Columnas: {len(table_info.columns)}

Dependencias directas: {', '.join(deps['direct']) if deps['direct'] else 'Ninguna'}
Dependencias indirectas: {', '.join(deps['indirect']) if deps['indirect'] else 'Ninguna'}

Llaves foráneas:
"""
            for fk in table_info.foreign_keys:
                detail_text += f"  {fk.column_name} -> {fk.referenced_table}.{fk.referenced_column}\n"
            
            self.deps_detail.delete(1.0, tk.END)
            self.deps_detail.insert(1.0, detail_text)
    
    def optimize_order(self):
        """Optimiza el orden de transferencia"""
        if not self.schema_info:
            return
        
        try:
            # Obtener sugerencias de optimización
            suggestions = self.dependency_resolver.suggest_optimizations(self.schema_info)
            
            # Mostrar sugerencias
            if suggestions:
                suggestion_text = "Sugerencias de optimización:\n\n"
                for suggestion in suggestions:
                    suggestion_text += f"• {suggestion['message']}\n"
                
                messagebox.showinfo("Optimizaciones Sugeridas", suggestion_text)
            else:
                messagebox.showinfo("Optimización", "No se encontraron optimizaciones adicionales.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al optimizar: {str(e)}")
    
    def export_plan(self):
        """Exporta el plan de transferencia"""
        if not self.schema_info:
            return
        
        filename = filedialog.asksavename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Exportar Plan de Transferencia"
        )
        
        if filename:
            try:
                # Crear plan de transferencia
                plan = {
                    'schema_name': self.schema_info.schema_name,
                    'transfer_order': self.schema_info.dependency_order,
                    'tables': {},
                    'created_at': datetime.now().isoformat()
                }
                
                for table_name, table_info in self.schema_info.objects.tables.items():
                    plan['tables'][table_name] = {
                        'row_count': table_info.row_count,
                        'columns': len(table_info.columns),
                        'foreign_keys': len(table_info.foreign_keys),
                        'dependencies': list(table_info.dependencies)
                    }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(plan, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Éxito", f"Plan exportado a: {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al exportar: {str(e)}")


class MainGUI:
    """Ventana principal de la aplicación"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Pasador de Esquemas de BD")
        self.root.geometry("1200x800")
        
        # Componentes del negocio
        self.db_manager = DatabaseManager()
        self.schema_analyzer = SchemaAnalyzer(self.db_manager)
        self.dependency_resolver = DependencyResolver()
        self.schema_exporter = SchemaExporter()
        
        # Variables de estado
        self.source_schema_info: Optional[SchemaInfo] = None
        self.target_connection_config = {}
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO,
                          format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Referencia para que los frames puedan acceder a la app principal
        self.root.app = self
        
        self.setup_ui()
        self.setup_menu()
    
    def setup_ui(self):
        """Configura la interfaz principal"""
        
        # Frame principal con PanedWindow
        main_paned = ttk.PanedWindow(self.root, orient='horizontal')
        main_paned.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Panel izquierdo - Conexiones
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # Conexión origen
        self.source_frame = ConnectionFrame(left_frame, "Base de Datos Origen", "source")
        self.source_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Botones de análisis
        analysis_frame = ttk.Frame(left_frame)
        analysis_frame.pack(fill='x', pady=(0, 10))
        
        self.analyze_btn = ttk.Button(analysis_frame, text="Analizar Esquema", 
                                     command=self.analyze_schema)
        self.analyze_btn.pack(fill='x')
        
        # Opciones de análisis
        options_frame = ttk.LabelFrame(left_frame, text="Objetos a Analizar", padding="5")
        options_frame.pack(fill='x', pady=(0, 10))
        
        # Variables para controlar qué objetos analizar
        self.include_views_var = tk.BooleanVar(value=True)
        self.include_sequences_var = tk.BooleanVar(value=True)
        self.include_procedures_var = tk.BooleanVar(value=True)
        self.include_triggers_var = tk.BooleanVar(value=True)
        self.include_indexes_var = tk.BooleanVar(value=True)
        
        # Checkboxes para cada tipo de objeto
        ttk.Checkbutton(options_frame, text="📊 Tablas (siempre incluidas)", 
                       state='disabled', variable=tk.BooleanVar(value=True)).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="👁 Vistas", 
                       variable=self.include_views_var).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="🔢 Secuencias", 
                       variable=self.include_sequences_var).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="⚙️ Procedimientos/Funciones", 
                       variable=self.include_procedures_var).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="🎯 Triggers", 
                       variable=self.include_triggers_var).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="📇 Índices", 
                       variable=self.include_indexes_var).pack(anchor='w')
        
        # Conexión destino
        self.target_frame = ConnectionFrame(left_frame, "Base de Datos Destino", "target")
        self.target_frame.pack(fill='both', expand=True)
        
        # Panel derecho - Visualización y transferencia
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)
        
        # Frame de visualización
        self.viz_frame = SchemaVisualizationFrame(right_frame)
        self.viz_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Botones de transferencia
        transfer_frame = ttk.LabelFrame(right_frame, text="Transferencia", padding="10")
        transfer_frame.pack(fill='x')
        
        button_frame = ttk.Frame(transfer_frame)
        button_frame.pack(fill='x')
        
        self.select_tables_btn = ttk.Button(button_frame, text="Seleccionar Tablas",
                                           command=self.select_tables, state='disabled')
        self.select_tables_btn.pack(side='left', padx=(0, 10))
        
        self.transfer_btn = ttk.Button(button_frame, text="Iniciar Transferencia",
                                      command=self.start_transfer, state='disabled')
        self.transfer_btn.pack(side='left')
        
        # Botones de exportar
        self.export_btn = ttk.Button(button_frame, text="Exportar Esquema",
                                    command=self.show_export_dialog, state='disabled')
        self.export_btn.pack(side='left', padx=(10, 0))
        
        # Barra de progreso
        self.progress_var = tk.StringVar(value="Listo para analizar esquema")
        self.progress_label = ttk.Label(transfer_frame, textvariable=self.progress_var)
        self.progress_label.pack(anchor='w', pady=(10, 0))
        
        self.progress_bar = ttk.Progressbar(transfer_frame, mode='indeterminate')
        self.progress_bar.pack(fill='x', pady=(5, 0))
    
    def setup_menu(self):
        """Configura el menú principal"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Guardar Configuración", command=self.save_config)
        file_menu.add_command(label="Cargar Configuración", command=self.load_config)
        file_menu.add_separator()
        file_menu.add_command(label="Cargar Config Oracle", command=self.load_oracle_config)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)
        
        # Menú Herramientas
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Herramientas", menu=tools_menu)
        tools_menu.add_command(label="Validar Conexiones", command=self.validate_connections)
        tools_menu.add_command(label="Limpiar Cache", command=self.clear_cache)
        
        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Acerca de", command=self.show_about)
    
    def analyze_schema(self):
        """Analiza el esquema seleccionado"""
        selected_schema = self.source_frame.get_selected_schema()
        if not selected_schema:
            messagebox.showerror("Error", "Selecciona un esquema para analizar")
            return
        
        if not self.source_frame.connection_config:
            messagebox.showerror("Error", "Conecta primero a la base de datos origen")
            return
        
        # Ejecutar análisis en hilo separado
        self.progress_var.set("Analizando esquema...")
        self.progress_bar.start()
        self.analyze_btn.config(state='disabled')
        
        def analyze_thread():
            try:
                config = self.source_frame.connection_config
                engine = self.db_manager.get_engine("source", config['db_type'], config)
                
                # Obtener lista de tablas para selección opcional
                all_tables = self.db_manager.get_tables(engine, config['db_type'], selected_schema)
                
                # Analizar esquema con opciones seleccionadas
                self.source_schema_info = self.schema_analyzer.analyze_schema(
                    engine, config['db_type'], selected_schema,
                    selected_tables=None,  # Todas las tablas por ahora
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
        """Maneja la finalización del análisis"""
        self.progress_bar.stop()
        self.progress_var.set("Análisis completado")
        self.analyze_btn.config(state='normal')
        
        if self.source_schema_info:
            # Actualizar visualización
            self.viz_frame.update_schema_info(self.source_schema_info)
            
            # Habilitar botones de transferencia y exportar
            self.select_tables_btn.config(state='normal')
            self.transfer_btn.config(state='normal')
            self.export_btn.config(state='normal')
            
            # Mostrar resumen
            total_tables = len(self.source_schema_info.objects.tables)
            total_rows = sum(t.row_count for t in self.source_schema_info.objects.tables.values())
            
            messagebox.showinfo("Análisis Completo", 
                              f"Esquema analizado exitosamente:\n"
                              f"Tablas: {total_tables}\n"
                              f"Filas totales: {total_rows:,}")
    
    def on_analysis_error(self, error_msg: str):
        """Maneja errores en el análisis"""
        self.progress_bar.stop()
        self.progress_var.set("Error en análisis")
        self.analyze_btn.config(state='normal')
        messagebox.showerror("Error de Análisis", error_msg)
    
    def select_tables(self):
        """Permite seleccionar tablas específicas para transferir"""
        if not self.source_schema_info:
            return
        
        all_tables = list(self.source_schema_info.objects.tables.keys())
        dialog = TableSelectionDialog(self.root, all_tables, "Seleccionar Tablas a Transferir")
        selected_tables = dialog.show()
        
        if selected_tables:
            # Crear nueva instancia de schema_info solo con las tablas seleccionadas
            filtered_tables = {name: info for name, info in self.source_schema_info.objects.tables.items() 
                             if name in selected_tables}
            
            if filtered_tables:
                # Crear nuevo schema_info con tablas filtradas
                filtered_schema = SchemaInfo(
                    schema_name=self.source_schema_info.schema_name,
                    tables=filtered_tables,
                    dependency_order=[]
                )
                
                # Recalcular dependencias y orden
                analyzer = SchemaAnalyzer(self.db_manager)
                analyzer._calculate_dependencies(filtered_schema)
                filtered_schema.dependency_order = analyzer._calculate_insertion_order(filtered_schema)
                
                # Actualizar schema_info y visualización
                self.source_schema_info = filtered_schema
                self.viz_frame.update_schema_info(self.source_schema_info)
                
                self.progress_var.set(f"{len(selected_tables)} tablas seleccionadas para transferencia")
    
    def start_transfer(self):
        """Inicia la transferencia de datos"""
        if not self.source_schema_info:
            messagebox.showerror("Error", "Primero analiza el esquema origen")
            return
        
        target_schema = self.target_frame.get_selected_schema()
        if not target_schema:
            messagebox.showerror("Error", "Selecciona el esquema destino")
            return
        
        if not self.target_frame.connection_config:
            messagebox.showerror("Error", "Conecta primero a la base de datos destino")
            return
        
        # Confirmación
        total_tables = len(self.source_schema_info.objects.tables)
        total_rows = sum(t.row_count for t in self.source_schema_info.objects.tables.values())
        
        result = messagebox.askyesno(
            "Confirmar Transferencia",
            f"¿Iniciar transferencia de {total_tables} tablas ({total_rows:,} filas)?\n\n"
            f"Origen: {self.source_schema_info.schema_name}\n"
            f"Destino: {target_schema}\n\n"
            f"Esta operación puede tomar tiempo y modificar datos."
        )
        
        if result:
            # Abrir diálogo de configuración de transferencia
            from data_transfer import TransferDialog
            
            try:
                dialog = TransferDialog(self.root, self.source_schema_info)
                dialog.show()
            except Exception as e:
                messagebox.showerror("Error", f"Error abriendo diálogo de transferencia: {str(e)}")
    
    def save_config(self):
        """Guarda la configuración de conexiones"""
        filename = filedialog.asksavename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Guardar Configuración"
        )
        
        if filename:
            try:
                config = {
                    'source': self.source_frame.get_connection_config(),
                    'target': self.target_frame.get_connection_config(),
                    'saved_at': datetime.now().isoformat()
                }
                
                # Remover contraseñas por seguridad
                for conn in ['source', 'target']:
                    if 'password' in config[conn]:
                        config[conn]['password'] = ''
                
                with open(filename, 'w') as f:
                    json.dump(config, f, indent=2)
                
                messagebox.showinfo("Éxito", f"Configuración guardada en: {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {str(e)}")
    
    def load_config(self):
        """Carga configuración de conexiones"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Cargar Configuración",
            initialdir="config"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Si es la nueva estructura con 'connections'
                if 'connections' in config:
                    connections = config['connections']
                    
                    # Mostrar diálogo para seleccionar conexiones
                    self.show_connection_selector(connections)
                    
                # Formato antiguo de configuración  
                elif 'source' in config and 'target' in config:
                    self.load_legacy_config(config)
                
                messagebox.showinfo("Éxito", "Configuración cargada correctamente")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar: {str(e)}")
    
    def show_connection_selector(self, connections):
        """Muestra diálogo para seleccionar conexiones origen y destino"""
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Seleccionar Conexiones")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Frame principal
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Conexión origen
        ttk.Label(main_frame, text="Conexión Origen:").pack(anchor='w')
        source_var = tk.StringVar()
        source_combo = ttk.Combobox(main_frame, textvariable=source_var, 
                                   values=list(connections.keys()), state='readonly')
        source_combo.pack(fill='x', pady=(5, 10))
        
        # Conexión destino
        ttk.Label(main_frame, text="Conexión Destino:").pack(anchor='w')
        target_var = tk.StringVar()
        target_combo = ttk.Combobox(main_frame, textvariable=target_var,
                                   values=list(connections.keys()), state='readonly')
        target_combo.pack(fill='x', pady=(5, 10))
        
        # Preview de la conexión seleccionada
        preview_frame = ttk.LabelFrame(main_frame, text="Vista Previa", padding="5")
        preview_frame.pack(fill='both', expand=True, pady=(10, 0))
        
        preview_text = tk.Text(preview_frame, height=8, wrap='word')
        preview_text.pack(fill='both', expand=True)
        
        def update_preview(event=None):
            selected = source_combo.get() or target_combo.get()
            if selected and selected in connections:
                conn = connections[selected]
                preview = f"""Nombre: {conn.get('name', 'N/A')}
Tipo: {conn.get('type', 'N/A')}
Host: {conn.get('host', 'N/A')}
Puerto: {conn.get('port', 'N/A')}
Base de datos: {conn.get('database', 'N/A')}
Usuario: {conn.get('user', 'N/A')}
Esquema por defecto: {conn.get('schema_default', 'N/A')}
Descripción: {conn.get('description', 'N/A')}"""
                preview_text.delete(1.0, tk.END)
                preview_text.insert(1.0, preview)
        
        source_combo.bind('<<ComboboxSelected>>', update_preview)
        target_combo.bind('<<ComboboxSelected>>', update_preview)
        
        # Preseleccionar conexiones Oracle si están disponibles
        oracle_connections = [k for k, v in connections.items() if v.get('type', '').lower() == 'oracle']
        if len(oracle_connections) >= 2:
            source_combo.set(oracle_connections[0])
            target_combo.set(oracle_connections[1])
            update_preview()
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        def apply_connections():
            source_conn = source_var.get()
            target_conn = target_var.get()
            
            if not source_conn or not target_conn:
                messagebox.showerror("Error", "Selecciona ambas conexiones")
                return
            
            # Cargar conexión origen
            if source_conn in connections:
                self.load_connection_to_frame(self.source_frame, connections[source_conn])
            
            # Cargar conexión destino  
            if target_conn in connections:
                self.load_connection_to_frame(self.target_frame, connections[target_conn])
            
            dialog.destroy()
        
        ttk.Button(button_frame, text="Aplicar", command=apply_connections).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(side='right')
    
    def load_connection_to_frame(self, frame: ConnectionFrame, conn_config: Dict):
        """Carga configuración en un frame de conexión"""
        
        # Limpiar campos existentes
        frame.db_type.set(conn_config.get('type', ''))
        frame.on_db_type_changed()  # Actualizar campos habilitados
        
        frame.host_entry.delete(0, tk.END)
        frame.host_entry.insert(0, conn_config.get('host', ''))
        
        frame.port_entry.delete(0, tk.END)
        frame.port_entry.insert(0, str(conn_config.get('port', '')))
        
        frame.database_entry.delete(0, tk.END)
        frame.database_entry.insert(0, conn_config.get('database', ''))
        
        frame.user_entry.delete(0, tk.END)
        frame.user_entry.insert(0, conn_config.get('user', ''))
        
        frame.password_entry.delete(0, tk.END)
        frame.password_entry.insert(0, conn_config.get('password', ''))
    
    def load_legacy_config(self, config):
        """Carga configuración en formato antiguo"""
        # Cargar configuración origen
        if 'source' in config:
            src_config = config['source']
            self.source_frame.db_type.set(src_config.get('db_type', ''))
            self.source_frame.host_entry.delete(0, tk.END)
            self.source_frame.host_entry.insert(0, src_config.get('host', ''))
            # ... otros campos
        
        # Cargar configuración destino
        if 'target' in config:
            tgt_config = config['target']
            self.target_frame.db_type.set(tgt_config.get('db_type', ''))
            # ... otros campos
    
    def validate_connections(self):
        """Valida todas las conexiones configuradas"""
        results = []
        
        # Validar origen
        if self.source_frame.connection_config:
            config = self.source_frame.connection_config
            success, message = self.db_manager.test_connection(config['db_type'], config)
            results.append(f"Origen: {'✓' if success else '✗'} {message}")
        
        # Validar destino
        if self.target_frame.connection_config:
            config = self.target_frame.connection_config
            success, message = self.db_manager.test_connection(config['db_type'], config)
            results.append(f"Destino: {'✓' if success else '✗'} {message}")
        
        if results:
            messagebox.showinfo("Validación de Conexiones", "\n".join(results))
        else:
            messagebox.showwarning("Validación", "No hay conexiones configuradas para validar")
    
    def clear_cache(self):
        """Limpia el cache y conexiones"""
        self.db_manager.close_all_connections()
        self.source_schema_info = None
        messagebox.showinfo("Cache", "Cache limpiado correctamente")
    
    def show_about(self):
        """Muestra información sobre la aplicación"""
        messagebox.showinfo("Acerca de", 
                          "Pasador de Esquemas de BD v1.0\n\n"
                          "Herramienta para transferir esquemas entre bases de datos\n"
                          "con análisis automático de dependencias.\n\n"
                          "Soporta: PostgreSQL, MySQL, SQL Server, Oracle, SQLite")
    
    def load_oracle_config(self):
        """Carga rápidamente la configuración Oracle predefinida"""
        try:
            config_file = Path(__file__).parent / "config" / "oracle_config.json"
            
            if not config_file.exists():
                messagebox.showerror("Error", f"Archivo de configuración no encontrado:\n{config_file}")
                return
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if 'connections' in config:
                connections = config['connections']
                
                # Buscar conexiones Oracle
                oracle_connections = {k: v for k, v in connections.items() 
                                    if v.get('type', '').lower() == 'oracle'}
                
                if len(oracle_connections) >= 2:
                    conn_keys = list(oracle_connections.keys())
                    
                    # Cargar primera como origen
                    self.load_connection_to_frame(self.source_frame, oracle_connections[conn_keys[0]])
                    
                    # Cargar segunda como destino
                    self.load_connection_to_frame(self.target_frame, oracle_connections[conn_keys[1]])
                    
                    messagebox.showinfo("Éxito", 
                                      f"Configuración Oracle cargada:\n"
                                      f"Origen: {oracle_connections[conn_keys[0]].get('name')}\n"
                                      f"Destino: {oracle_connections[conn_keys[1]].get('name')}")
                else:
                    messagebox.showwarning("Advertencia", 
                                         "Se necesitan al menos 2 conexiones Oracle en la configuración")
            else:
                messagebox.showerror("Error", "Formato de configuración no válido")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando configuración Oracle: {str(e)}")
    def show_export_dialog(self):
        """Muestra el diálogo de opciones de exportar"""
        if not self.source_schema_info:
            messagebox.showerror("Error", "Primero analiza un esquema")
            return
        
        # Crear ventana de diálogo
        dialog = tk.Toplevel(self.root)
        dialog.title("Exportar Esquema")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrar ventana
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        # Frame principal
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Título
        ttk.Label(main_frame, text=f"Exportar Esquema: {self.source_schema_info.schema_name}", 
                 font=('Arial', 12, 'bold')).pack(pady=(0, 20))
        
        # Opciones de exportación
        export_frame = ttk.LabelFrame(main_frame, text="Formato de Exportación", padding="10")
        export_frame.pack(fill='x', pady=(0, 20))
        
        export_var = tk.StringVar(value="sql")
        
        ttk.Radiobutton(export_frame, text="📄 SQL DDL (Crear scripts de estructura)", 
                       variable=export_var, value="sql").pack(anchor='w', pady=2)
        ttk.Radiobutton(export_frame, text="📋 JSON (Metadatos completos)", 
                       variable=export_var, value="json").pack(anchor='w', pady=2)
        ttk.Radiobutton(export_frame, text="🌐 HTML (Reporte visual)", 
                       variable=export_var, value="html").pack(anchor='w', pady=2)
        ttk.Radiobutton(export_frame, text="📊 CSV (Resúmenes por tipo)", 
                       variable=export_var, value="csv").pack(anchor='w', pady=2)
        
        # Opciones adicionales para SQL
        sql_frame = ttk.LabelFrame(main_frame, text="Opciones para SQL DDL", padding="10")
        sql_frame.pack(fill='x', pady=(0, 20))
        
        target_db_var = tk.StringVar(value="oracle")
        ttk.Label(sql_frame, text="Base de datos destino:").pack(anchor='w')
        
        db_frame = ttk.Frame(sql_frame)
        db_frame.pack(fill='x', pady=(5, 0))
        
        ttk.Radiobutton(db_frame, text="Oracle", variable=target_db_var, value="oracle").pack(side='left', padx=(0, 10))
        ttk.Radiobutton(db_frame, text="PostgreSQL", variable=target_db_var, value="postgresql").pack(side='left', padx=(0, 10))
        ttk.Radiobutton(db_frame, text="SQL Server", variable=target_db_var, value="sqlserver").pack(side='left')
        
        # Información del esquema
        info_frame = ttk.LabelFrame(main_frame, text="Información del Esquema", padding="10")
        info_frame.pack(fill='x', pady=(0, 20))
        
        stats_text = f"""📊 Tablas: {len(self.source_schema_info.objects.tables)}
👁 Vistas: {len(self.source_schema_info.objects.views)}
🔢 Secuencias: {len(self.source_schema_info.objects.sequences)}
⚙️ Procedimientos: {len(self.source_schema_info.objects.procedures)}
🎯 Triggers: {len(self.source_schema_info.objects.triggers)}
📇 Índices: {len(self.source_schema_info.objects.indexes)}"""
        
        ttk.Label(info_frame, text=stats_text, justify='left').pack(anchor='w')
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(20, 0))
        
        def do_export():
            export_type = export_var.get()
            target_db = target_db_var.get()
            
            # Seleccionar archivo de destino
            if export_type == "sql":
                filename = filedialog.asksaveasfilename(
                    title="Guardar DDL SQL",
                    defaultextension=".sql",
                    filetypes=[("SQL files", "*.sql"), ("All files", "*.*")]
                )
            elif export_type == "json":
                filename = filedialog.asksaveasfilename(
                    title="Guardar JSON",
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
                )
            elif export_type == "html":
                filename = filedialog.asksaveasfilename(
                    title="Guardar Reporte HTML",
                    defaultextension=".html",
                    filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
                )
            elif export_type == "csv":
                filename = filedialog.askdirectory(
                    title="Seleccionar directorio para CSVs"
                )
            
            if filename:
                self.perform_export(export_type, filename, target_db, dialog)
        
        ttk.Button(button_frame, text="Exportar", command=do_export).pack(side='right', padx=(10, 0))
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(side='right')
    
    def perform_export(self, export_type: str, filename: str, target_db: str, dialog: tk.Toplevel):
        """Realiza la exportación en un hilo separado"""
        
        def export_thread():
            try:
                success = False
                
                if export_type == "sql":
                    success = self.schema_exporter.export_to_sql_ddl(
                        self.source_schema_info, filename, target_db
                    )
                elif export_type == "json":
                    success = self.schema_exporter.export_to_json(
                        self.source_schema_info, filename
                    )
                elif export_type == "html":
                    success = self.schema_exporter.export_to_html_report(
                        self.source_schema_info, filename
                    )
                elif export_type == "csv":
                    success = self.schema_exporter.export_to_csv_summary(
                        self.source_schema_info, filename
                    )
                
                # Notificar resultado en el hilo principal
                self.root.after(0, lambda: self.on_export_complete(success, filename, dialog))
                
            except Exception as e:
                error_msg = f"Error durante la exportación: {str(e)}"
                self.root.after(0, lambda: self.on_export_error(error_msg, dialog))
        
        # Cambiar cursor y deshabilitar botones
        try:
            dialog.config(cursor="watch")  # Usar "watch" en lugar de "wait"
        except:
            pass  # Ignorar si el cursor no es compatible
        
        # Ejecutar en hilo separado
        threading.Thread(target=export_thread, daemon=True).start()
    
    def on_export_complete(self, success: bool, filename: str, dialog: tk.Toplevel):
        """Maneja la finalización de la exportación"""
        dialog.config(cursor="")
        
        if success:
            messagebox.showinfo("Exportación Completa", 
                              f"Esquema exportado exitosamente a:\n{filename}")
            dialog.destroy()
        else:
            messagebox.showerror("Error de Exportación", 
                               "Hubo un problema durante la exportación. Revisa los logs.")
    
    def on_export_error(self, error_msg: str, dialog: tk.Toplevel):
        """Maneja errores en la exportación"""
        dialog.config(cursor="")
        messagebox.showerror("Error de Exportación", error_msg)
    
    def run(self):
        """Ejecuta la aplicación"""
        try:
            self.root.mainloop()
        finally:
            # Limpiar recursos
            self.db_manager.close_all_connections()


if __name__ == "__main__":
    app = MainGUI()
    app.run()