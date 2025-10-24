#!/bin/bash

# Script de instalación para Pasador de Esquemas de BD
# Configura el entorno y las dependencias necesarias

set -e  # Salir si hay errores

echo "🚀 Configurando Pasador de Esquemas de BD..."
echo "============================================"

# Verificar Python
echo "📋 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado"
    echo "Por favor instala Python 3.7 o superior"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION detectado"

# Verificar pip
echo "📦 Verificando pip..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 no está instalado"
    echo "Instalando pip..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py
    rm get-pip.py
fi

# Crear entorno virtual
echo "🔧 Creando entorno virtual..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ Entorno virtual creado"
else
    echo "ℹ️  Entorno virtual ya existe"
fi

# Activar entorno virtual
echo "🔌 Activando entorno virtual..."
source .venv/bin/activate

# Actualizar pip en el entorno virtual
echo "⬆️  Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias básicas
echo "📚 Instalando dependencias básicas..."
pip install wheel setuptools

# Instalar dependencias del proyecto
echo "🔗 Instalando dependencias del proyecto..."
pip install -r requirements.txt

# Verificar tkinter
echo "🖥️  Verificando tkinter..."
python3 -c "import tkinter; print('✅ tkinter disponible')" || {
    echo "❌ tkinter no está disponible"
    echo "En Ubuntu/Debian: sudo apt-get install python3-tk"
    echo "En CentOS/RHEL: sudo yum install tkinter"
    echo "En Arch: sudo pacman -S tk"
}

# Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p logs
mkdir -p config
mkdir -p exports

# Hacer el script principal ejecutable
echo "🔑 Configurando permisos..."
chmod +x app.py

# Mensaje final
echo ""
echo "✅ ¡Instalación completada!"
echo ""
echo "Para ejecutar la aplicación:"
echo "  1. Activa el entorno virtual: source .venv/bin/activate"
echo "  2. Ejecuta la aplicación: python app.py"
echo ""
echo "O simplemente ejecuta: ./run.sh"
echo ""