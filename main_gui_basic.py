"""
GUI Básica Moderna - Sin callbacks complejos
Versión mínima funcional con CustomTkinter
"""

import customtkinter as ctk
from tkinter import messagebox
import logging

# Configurar CustomTkinter
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


class BasicModernGUI:
    """GUI moderna básica sin funcionalidades complejas"""
    
    def __init__(self):
        # Crear ventana principal
        self.root = ctk.CTk()
        self.root.title("🚀 El Pasador de Esquemas de BD - Básico")
        self.root.geometry("900x600")
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        
        # Configurar UI
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz básica"""
        
        # Frame principal
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Título
        title_label = ctk.CTkLabel(
            main_frame,
            text="🚀 Pasador de Esquemas de BD",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=(20, 30))
        
        # Subtítulo
        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Versión moderna con CustomTkinter",
            font=ctk.CTkFont(size=14)
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Frame de información
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Texto de información
        info_text = """✅ CustomTkinter está funcionando correctamente!

🎉 Características implementadas:
• Interfaz moderna con temas dark/light
• Widgets modernos con CustomTkinter
• Base para análisis de esquemas
• Preparado para funcionalidades avanzadas

🚧 Próximas funcionalidades:
• Conexiones a múltiples tipos de BD
• Análisis completo de esquemas
• Exportación a múltiples formatos  
• Transferencia inteligente de datos

Esta es la base para el desarrollo completo
de la aplicación de migración de esquemas."""
        
        info_label = ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        info_label.pack(pady=30, padx=30)
        
        # Frame de botones
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill='x', padx=20, pady=10)
        
        # Botones de demostración
        demo_btn = ctk.CTkButton(
            buttons_frame,
            text="🎯 Demostración",
            command=self.show_demo,
            height=40,
            width=150
        )
        demo_btn.pack(side='left', padx=10, pady=10)
        
        theme_btn = ctk.CTkButton(
            buttons_frame,
            text="🌙 Cambiar Tema",
            command=self.toggle_theme,
            height=40,
            width=150
        )
        theme_btn.pack(side='left', padx=10, pady=10)
        
        about_btn = ctk.CTkButton(
            buttons_frame,
            text="ℹ️ Acerca de",
            command=self.show_about,
            height=40,
            width=150
        )
        about_btn.pack(side='left', padx=10, pady=10)
        
        # Estado del tema
        self.is_dark = False
    
    def show_demo(self):
        """Muestra demostración"""
        messagebox.showinfo(
            "🎯 Demostración",
            "Esta es una demostración de CustomTkinter funcionando!\n\n"
            "La interfaz moderna está lista para:\n"
            "• Conectar a bases de datos\n"
            "• Analizar esquemas completos\n"
            "• Exportar documentación\n"
            "• Transferir datos inteligentemente"
        )
    
    def toggle_theme(self):
        """Cambia entre tema claro y oscuro"""
        if self.is_dark:
            ctk.set_appearance_mode("light")
            self.is_dark = False
            messagebox.showinfo("🌞", "Tema claro activado")
        else:
            ctk.set_appearance_mode("dark")
            self.is_dark = True
            messagebox.showinfo("🌙", "Tema oscuro activado")
    
    def show_about(self):
        """Muestra información sobre la aplicación"""
        about_text = """🚀 Pasador de Esquemas de BD

Versión: 2.0 - Moderna
Framework: CustomTkinter

Una herramienta profesional para migración
de esquemas entre bases de datos con
interfaz moderna y funcionalidades avanzadas.

✨ Desarrollado con tecnología moderna para
proporcionar la mejor experiencia de usuario."""
        
        messagebox.showinfo("ℹ️ Acerca de", about_text)
    
    def run(self):
        """Ejecuta la aplicación"""
        self.root.mainloop()


if __name__ == "__main__":
    app = BasicModernGUI()
    app.run()