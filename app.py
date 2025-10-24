#!/usr/bin/env python3
"""
Aplicación de Pasador de Esquemas de BD
Punto de entrada principal con interfaz moderna usando CustomTkinter
"""

import sys
import os
import logging
from pathlib import Path

# Agregar el directorio actual al path para importaciones
sys.path.insert(0, str(Path(__file__).parent))

try:
    import tkinter as tk
    from tkinter import messagebox
    # CustomTkinter disponible pero usando tkinter por compatibilidad
    
except ImportError:
    print("Error: Tkinter no está disponible.")
    sys.exit(1)

try:
    from main_gui import MainGUI  # Usar la versión original estable
except ImportError as e:
    print(f"Error importando módulos: {e}")
    print("Asegúrate de que todas las dependencias están instaladas:")
    print("pip install -r requirements.txt")
    sys.exit(1)


def setup_logging():
    """Configura el sistema de logging"""
    
    # Crear directorio de logs si no existe
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Configurar logging
    log_file = log_dir / "pasador_db.log"
    
    # Formato de logs
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Configurar logger raíz
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Configurar nivel de logs para librerías externas
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("Sistema de logging configurado")
    logger.info(f"Logs guardándose en: {log_file}")
    
    return logger


def check_dependencies():
    """Verifica que todas las dependencias estén disponibles"""
    
    required_modules = [
        ('psycopg2', 'PostgreSQL support'),
        ('mysql.connector', 'MySQL support'),
        ('pymssql', 'SQL Server support'),
        ('sqlalchemy', 'Database abstraction'),
        ('pandas', 'Data manipulation'),
        ('treelib', 'Dependency visualization'),
        ('customtkinter', 'Modern GUI framework'),
    ]
    
    missing_modules = []
    
    for module, description in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append((module, description))
    
    if missing_modules:
        print("⚠️  Módulos faltantes detectados:")
        for module, description in missing_modules:
            print(f"  - {module}: {description}")
        print("\nPuedes continuar, pero algunas funcionalidades pueden no estar disponibles.")
        print("Para instalar todas las dependencias:")
        print("pip install -r requirements.txt")
        print()
    
    return len(missing_modules) == 0


def check_system_requirements():
    """Verifica los requisitos del sistema"""
    
    # Verificar versión de Python
    if sys.version_info < (3, 7):
        print("❌ Error: Python 3.7 o superior es requerido")
        print(f"Versión actual: {sys.version}")
        return False
    
    # Verificar Tkinter
    try:
        root = tk.Tk()
        root.withdraw()  # Ocultar ventana
        root.destroy()
    except Exception as e:
        print(f"❌ Error: Tkinter no funciona correctamente: {e}")
        return False
    
    return True


def show_welcome_message(logger):
    """Muestra mensaje de bienvenida"""
    
    welcome_msg = """
╔══════════════════════════════════════════════════════════════════╗
║                    PASADOR DE ESQUEMAS DE BD                     ║
║                                                                  ║
║  Herramienta profesional para transferir esquemas entre BD      ║
║  con análisis automático de dependencias                        ║
║                                                                  ║
║  Características:                                                ║
║  • Soporta PostgreSQL, MySQL, SQL Server, SQLite               ║
║  • Análisis de todos los objetos de BD                          ║
║  • Exportación a múltiples formatos                             ║
║  • Resolución inteligente de dependencias                       ║
║  • Interfaz gráfica profesional                                 ║
║  • Transferencia con validación de integridad                   ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """
    
    print(welcome_msg)
    logger.info("Aplicación iniciada")


def handle_exception(exc_type, exc_value, exc_traceback):
    """Maneja excepciones no capturadas"""
    
    if issubclass(exc_type, KeyboardInterrupt):
        # Permitir Ctrl+C
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger = logging.getLogger(__name__)
    logger.error("Excepción no manejada:", exc_info=(exc_type, exc_value, exc_traceback))
    
    # Mostrar error al usuario si hay GUI
    try:
        # Usar tk para messagebox ya que CTk puede no estar disponible
        if hasattr(tk, '_default_root') and tk._default_root:
            error_msg = f"Error inesperado: {exc_type.__name__}: {exc_value}"
            messagebox.showerror("Error Fatal", error_msg)
    except:
        pass


def main():
    """Función principal moderna"""
    
    # Configurar manejo de excepciones
    sys.excepthook = handle_exception
    
    # Verificar requisitos del sistema
    if not check_system_requirements():
        return 1
    
    # Configurar logging
    logger = setup_logging()
    
    # Mostrar mensaje de bienvenida
    show_welcome_message(logger)
    
    # Verificar dependencias
    all_deps_available = check_dependencies()
    
    if not all_deps_available:
        # Preguntar al usuario si quiere continuar
        root = tk.Tk()
        root.withdraw()
        
        result = messagebox.askyesno(
            "Dependencias Faltantes",
            "Algunas dependencias no están instaladas.\n\n"
            "¿Deseas continuar de todos modos?\n"
            "(Algunas funcionalidades pueden no estar disponibles)"
        )
        
        root.destroy()
        
        if not result:
            logger.info("Usuario canceló debido a dependencias faltantes")
            return 1
    
    # Iniciar aplicación principal
    try:
        logger.info("Iniciando interfaz gráfica...")
        app = MainGUI()
        app.run()
        
        logger.info("Aplicación cerrada normalmente")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Aplicación interrumpida por el usuario")
        return 0
        
    except Exception as e:
        logger.error(f"Error fatal en aplicación: {e}", exc_info=True)
        
        # Mostrar error al usuario
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Error Fatal",
                f"La aplicación ha encontrado un error fatal:\n\n{str(e)}\n\n"
                f"Revisa el archivo de log para más detalles."
            )
            root.destroy()
        except:
            pass
        
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)