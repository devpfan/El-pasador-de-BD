"""
GUI Moderna Simplificada - Versión estable
Interfaz moderna usando CustomTkinter sin funcionalidades complejas
"""

import customtkinter as ctk
from tkinter import messagebox
import logging
import threading
from typing import Optional

from database_manager import DatabaseManager
from schema_analyzer import SchemaAnalyzer, SchemaInfo
from dependency_resolver import DependencyResolver
from schema_exporter import SchemaExporter

# Configurar CustomTkinter
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


class SimpleModernGUI:
    """GUI moderna simplificada y estable"""
    
    def __init__(self):
        # Crear ventana principal
        self.root = ctk.CTk()
        self.root.title("🚀 Pasador de Esquemas de BD - Moderno")
        self.root.geometry("1200x800")
        
        # Componentes de negocio
        self.db_manager = DatabaseManager()
        self.schema_analyzer = SchemaAnalyzer(self.db_manager)
        self.dependency_resolver = DependencyResolver()
        self.schema_exporter = SchemaExporter()
        
        # Estado
        self.source_schema_info: Optional[SchemaInfo] = None
        self.source_config = {}
        self.target_config = {}
        
        # Variables de análisis
        self.include_views = ctk.BooleanVar(value=True)
        self.include_sequences = ctk.BooleanVar(value=True)
        self.include_procedures = ctk.BooleanVar(value=True)
        self.include_triggers = ctk.BooleanVar(value=True)
        self.include_indexes = ctk.BooleanVar(value=True)
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        
        # Configurar UI
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz moderna simplificada"""
        
        # Frame principal
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Título principal
        title_label = ctk.CTkLabel(
            main_frame,
            text="🚀 Pasador de Esquemas de BD",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(10, 20))
        
        # Crear notebook de pestañas
        self.notebook = ctk.CTkTabview(main_frame, width=400, height=300)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Pestañas
        self.notebook.add("🔌 Conexiones")
        self.notebook.add("🔍 Análisis")
        self.notebook.add("📊 Resultados")
        self.notebook.add("🚀 Transferir")
        
        self.setup_connections_tab()
        self.setup_analysis_tab()
        self.setup_results_tab()
        self.setup_transfer_tab()
        
        # Barra de estado
        self.status_var = ctk.StringVar(value="🔮 Listo para comenzar")
        status_label = ctk.CTkLabel(main_frame, textvariable=self.status_var)
        status_label.pack(pady=(10, 0))
    
    def setup_connections_tab(self):
        """Configura pestaña de conexiones simplificada"""
        tab = self.notebook.tab("🔌 Conexiones")
        
        # Frame de origen
        source_frame = ctk.CTkFrame(tab)
        source_frame.pack(fill='x', padx=10, pady=5)
        
        ctk.CTkLabel(
            source_frame,
            text="🗄️ Base de Datos Origen",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        # Campos básicos para origen
        self.source_host = ctk.CTkEntry(source_frame, placeholder_text="Host (ej: localhost)")
        self.source_host.pack(pady=2, padx=10, fill='x')
        
        self.source_port = ctk.CTkEntry(source_frame, placeholder_text="Puerto (ej: 5432)")
        self.source_port.pack(pady=2, padx=10, fill='x')
        
        self.source_db = ctk.CTkEntry(source_frame, placeholder_text="Base de datos")
        self.source_db.pack(pady=2, padx=10, fill='x')
        
        self.source_user = ctk.CTkEntry(source_frame, placeholder_text="Usuario")
        self.source_user.pack(pady=2, padx=10, fill='x')
        
        self.source_pass = ctk.CTkEntry(source_frame, placeholder_text="Contraseña", show="*")
        self.source_pass.pack(pady=2, padx=10, fill='x')
        
        # Esquema
        self.source_schema = ctk.CTkEntry(source_frame, placeholder_text="Esquema a analizar")
        self.source_schema.pack(pady=2, padx=10, fill='x')
        
        # Botón de prueba
        test_source_btn = ctk.CTkButton(
            source_frame,
            text="🔍 Probar Conexión Origen",
            command=self.test_source_connection
        )
        test_source_btn.pack(pady=10)
        
        # Frame de destino
        target_frame = ctk.CTkFrame(tab)
        target_frame.pack(fill='x', padx=10, pady=5)
        
        ctk.CTkLabel(
            target_frame,
            text="📊 Base de Datos Destino",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        # Campos básicos para destino
        self.target_host = ctk.CTkEntry(target_frame, placeholder_text="Host (ej: localhost)")
        self.target_host.pack(pady=2, padx=10, fill='x')
        
        self.target_port = ctk.CTkEntry(target_frame, placeholder_text="Puerto")
        self.target_port.pack(pady=2, padx=10, fill='x')
        
        self.target_db = ctk.CTkEntry(target_frame, placeholder_text="Base de datos")
        self.target_db.pack(pady=2, padx=10, fill='x')
        
        self.target_user = ctk.CTkEntry(target_frame, placeholder_text="Usuario")
        self.target_user.pack(pady=2, padx=10, fill='x')
        
        self.target_pass = ctk.CTkEntry(target_frame, placeholder_text="Contraseña", show="*")
        self.target_pass.pack(pady=2, padx=10, fill='x')
        
        # Botón de prueba
        test_target_btn = ctk.CTkButton(
            target_frame,
            text="🔍 Probar Conexión Destino",
            command=self.test_target_connection
        )
        test_target_btn.pack(pady=10)
    
    def setup_analysis_tab(self):
        """Configura pestaña de análisis"""
        tab = self.notebook.tab("🔍 Análisis")
        
        # Opciones de análisis
        options_frame = ctk.CTkFrame(tab)
        options_frame.pack(fill='x', padx=10, pady=10)
        
        ctk.CTkLabel(
            options_frame,
            text="🔍 Opciones de Análisis",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        # Checkboxes modernos
        ctk.CTkCheckBox(options_frame, text="📊 Tablas (siempre incluidas)").pack(anchor='w', padx=20, pady=2)
        ctk.CTkCheckBox(options_frame, text="👁 Vistas", variable=self.include_views).pack(anchor='w', padx=20, pady=2)
        ctk.CTkCheckBox(options_frame, text="🔢 Secuencias", variable=self.include_sequences).pack(anchor='w', padx=20, pady=2)
        ctk.CTkCheckBox(options_frame, text="⚙️ Procedimientos", variable=self.include_procedures).pack(anchor='w', padx=20, pady=2)
        ctk.CTkCheckBox(options_frame, text="🎯 Triggers", variable=self.include_triggers).pack(anchor='w', padx=20, pady=2)
        ctk.CTkCheckBox(options_frame, text="📇 Índices", variable=self.include_indexes).pack(anchor='w', padx=20, pady=2)
        
        # Botón de análisis
        analyze_btn = ctk.CTkButton(
            tab,
            text="🚀 Analizar Esquema",
            command=self.analyze_schema,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        analyze_btn.pack(pady=20)
    
    def setup_results_tab(self):
        """Configura pestaña de resultados"""
        tab = self.notebook.tab("📊 Resultados")
        
        ctk.CTkLabel(
            tab,
            text="📊 Resultados del Análisis",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        # Área de texto para resultados
        self.results_text = ctk.CTkTextbox(tab, height=400)
        self.results_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Botones de exportar
        export_frame = ctk.CTkFrame(tab)
        export_frame.pack(fill='x', padx=10, pady=5)
        
        export_sql_btn = ctk.CTkButton(
            export_frame,
            text="📄 Exportar DDL",
            command=self.export_sql_ddl
        )
        export_sql_btn.pack(side='left', padx=5, pady=5)
        
        export_json_btn = ctk.CTkButton(
            export_frame,
            text="📋 Exportar JSON",
            command=self.export_json
        )
        export_json_btn.pack(side='left', padx=5, pady=5)
        
        export_html_btn = ctk.CTkButton(
            export_frame,
            text="🌐 Reporte HTML",
            command=self.export_html
        )
        export_html_btn.pack(side='left', padx=5, pady=5)
    
    def setup_transfer_tab(self):
        """Configura pestaña de transferencia"""
        tab = self.notebook.tab("🚀 Transferir")
        
        ctk.CTkLabel(
            tab,
            text="🚀 Transferencia de Datos",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        # Información
        info_text = "Esta funcionalidad será implementada próximamente.\n"
        info_text += "Incluirá:\n"
        info_text += "• Transferencia inteligente de esquemas\n"
        info_text += "• Resolución automática de dependencias\n"
        info_text += "• Progreso en tiempo real\n"
        info_text += "• Validación de integridad"
        
        info_label = ctk.CTkLabel(tab, text=info_text, justify='left')
        info_label.pack(pady=20)
        
        # Placeholder para transferencia
        transfer_btn = ctk.CTkButton(
            tab,
            text="🚧 Transferir (Próximamente)",
            command=lambda: messagebox.showinfo("🚧", "Funcionalidad en desarrollo"),
            state="disabled"
        )
        transfer_btn.pack(pady=20)
    
    def test_source_connection(self):
        """Prueba conexión origen"""
        try:
            config = {
                'db_type': 'postgresql',  # Por ahora asumimos PostgreSQL
                'host': self.source_host.get(),
                'port': int(self.source_port.get()) if self.source_port.get() else 5432,
                'database': self.source_db.get(),
                'user': self.source_user.get(),
                'password': self.source_pass.get()
            }
            
            engine = self.db_manager.get_engine("test_source", config['db_type'], config)
            
            with engine.connect():
                pass
                
            messagebox.showinfo("✅ Éxito", "Conexión origen exitosa")
            self.source_config = config
            
        except Exception as e:
            messagebox.showerror("❌ Error", f"Error conectando origen:\n{str(e)}")
    
    def test_target_connection(self):
        """Prueba conexión destino"""
        try:
            config = {
                'db_type': 'postgresql',  # Por ahora asumimos PostgreSQL
                'host': self.target_host.get(),
                'port': int(self.target_port.get()) if self.target_port.get() else 5432,
                'database': self.target_db.get(),
                'user': self.target_user.get(),
                'password': self.target_pass.get()
            }
            
            engine = self.db_manager.get_engine("test_target", config['db_type'], config)
            
            with engine.connect():
                pass
                
            messagebox.showinfo("✅ Éxito", "Conexión destino exitosa")
            self.target_config = config
            
        except Exception as e:
            messagebox.showerror("❌ Error", f"Error conectando destino:\n{str(e)}")
    
    def analyze_schema(self):
        """Analiza el esquema seleccionado"""
        if not self.source_config:
            messagebox.showerror("❌ Error", "Prueba primero la conexión origen")
            return
        
        schema_name = self.source_schema.get().strip()
        if not schema_name:
            messagebox.showerror("❌ Error", "Especifica el nombre del esquema")
            return
        
        # Actualizar estado
        self.status_var.set("🔍 Analizando esquema...")
        
        def analyze_thread():
            try:
                engine = self.db_manager.get_engine("source", self.source_config['db_type'], self.source_config)
                
                # Analizar esquema
                self.source_schema_info = self.schema_analyzer.analyze_schema(
                    engine, self.source_config['db_type'], schema_name,
                    selected_tables=None,
                    include_views=self.include_views.get(),
                    include_procedures=self.include_procedures.get(),
                    include_sequences=self.include_sequences.get(),
                    include_triggers=self.include_triggers.get(),
                    include_indexes=self.include_indexes.get()
                )
                
                # Actualizar UI en hilo principal
                self.root.after(0, self.on_analysis_complete)
                
            except Exception as e:
                error_msg = f"Error analizando esquema: {str(e)}"
                self.root.after(0, lambda: self.on_analysis_error(error_msg))
        
        threading.Thread(target=analyze_thread, daemon=True).start()
    
    def on_analysis_complete(self):
        """Maneja análisis completado"""
        self.status_var.set("✅ Análisis completado")
        
        if self.source_schema_info:
            # Mostrar resultados
            self.display_results()
            
            # Cambiar a pestaña de resultados
            self.notebook.set("📊 Resultados")
            
            messagebox.showinfo("🎉 Análisis Completo", 
                              f"Esquema '{self.source_schema_info.schema_name}' analizado exitosamente")
    
    def on_analysis_error(self, error_msg: str):
        """Maneja error en análisis"""
        self.status_var.set("❌ Error en análisis")
        messagebox.showerror("💥 Error", error_msg)
    
    def display_results(self):
        """Muestra los resultados del análisis"""
        if not self.source_schema_info:
            return
        
        self.results_text.delete("0.0", "end")
        
        results = f"""🎯 ESQUEMA: {self.source_schema_info.schema_name}

📊 OBJETOS ANALIZADOS:
├─ 📋 Tablas: {len(self.source_schema_info.objects.tables)}
├─ 👁 Vistas: {len(self.source_schema_info.objects.views)}
├─ 🔢 Secuencias: {len(self.source_schema_info.objects.sequences)}
├─ ⚙️ Procedimientos: {len(self.source_schema_info.objects.procedures)}
├─ 🎯 Triggers: {len(self.source_schema_info.objects.triggers)}
└─ 📇 Índices: {len(self.source_schema_info.objects.indexes)}

💾 ESTADÍSTICAS:
├─ Filas totales: {sum(t.row_count for t in self.source_schema_info.objects.tables.values()):,}
├─ Llaves foráneas: {sum(len(t.foreign_keys) for t in self.source_schema_info.objects.tables.values())}
└─ Orden de dependencias: {len(self.source_schema_info.dependency_order)} tablas

📋 TABLAS PRINCIPALES:
"""
        
        for i, table_name in enumerate(self.source_schema_info.dependency_order[:10], 1):
            if table_name in self.source_schema_info.objects.tables:
                table = self.source_schema_info.objects.tables[table_name]
                results += f"{i:>3}. {table_name:<30} ({table.row_count:>8,} filas)\n"
        
        if len(self.source_schema_info.dependency_order) > 10:
            results += f"    ... y {len(self.source_schema_info.dependency_order) - 10} más\n"
        
        self.results_text.insert("0.0", results)
    
    # Métodos de exportación simplificados
    def export_sql_ddl(self):
        """Exporta DDL SQL"""
        if not self.source_schema_info:
            messagebox.showerror("❌", "Primero analiza un esquema")
            return
        messagebox.showinfo("🚧", "Exportación DDL será implementada próximamente")
    
    def export_json(self):
        """Exporta a JSON"""
        if not self.source_schema_info:
            messagebox.showerror("❌", "Primero analiza un esquema")
            return
        messagebox.showinfo("🚧", "Exportación JSON será implementada próximamente")
    
    def export_html(self):
        """Exporta reporte HTML"""
        if not self.source_schema_info:
            messagebox.showerror("❌", "Primero analiza un esquema")
            return
        messagebox.showinfo("🚧", "Reporte HTML será implementado próximamente")
    
    def run(self):
        """Ejecuta la aplicación"""
        try:
            self.root.mainloop()
        finally:
            self.db_manager.close_all_connections()


if __name__ == "__main__":
    app = SimpleModernGUI()
    app.run()