"""
Prueba básica de CustomTkinter para verificar instalación
"""

import customtkinter as ctk
from tkinter import messagebox

# Configurar CustomTkinter
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

class SimpleTestApp:
    def __init__(self):
        # Crear ventana principal
        self.root = ctk.CTk()
        self.root.title("🚀 Test CustomTkinter")
        self.root.geometry("600x400")
        
        # Configurar UI básica
        self.setup_ui()
    
    def setup_ui(self):
        """Configura interfaz básica"""
        
        # Título
        title = ctk.CTkLabel(
            self.root,
            text="🎉 CustomTkinter funcionando!",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=30)
        
        # Frame para botones
        button_frame = ctk.CTkFrame(self.root)
        button_frame.pack(pady=20)
        
        # Botón de prueba
        test_btn = ctk.CTkButton(
            button_frame,
            text="🔍 Botón de Prueba",
            command=self.test_action,
            height=40,
            width=200
        )
        test_btn.pack(pady=10)
        
        # Botón para cambiar tema
        theme_btn = ctk.CTkButton(
            button_frame,
            text="🌙 Cambiar Tema",
            command=self.toggle_theme,
            height=40,
            width=200
        )
        theme_btn.pack(pady=10)
        
        # Información
        info = ctk.CTkLabel(
            self.root,
            text="Si ves esta ventana, CustomTkinter está instalado correctamente"
        )
        info.pack(pady=20)
        
        # Variable para tema
        self.dark_mode = False
    
    def test_action(self):
        """Acción de prueba"""
        messagebox.showinfo("Prueba", "CustomTkinter funciona correctamente! 🎉")
    
    def toggle_theme(self):
        """Cambia el tema"""
        if self.dark_mode:
            ctk.set_appearance_mode("light")
            self.dark_mode = False
        else:
            ctk.set_appearance_mode("dark")
            self.dark_mode = True
    
    def run(self):
        """Ejecuta la aplicación"""
        self.root.mainloop()

if __name__ == "__main__":
    app = SimpleTestApp()
    app.run()