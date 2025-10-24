#!/bin/bash

# Script para ejecutar Pasador de Esquemas de BD
# Activa el entorno virtual y ejecuta la aplicación

set -e

echo "🚀 Iniciando Pasador de Esquemas de BD..."

# Verificar que existe el entorno virtual
if [ ! -d ".venv" ]; then
    echo "❌ Entorno virtual no encontrado"
    echo "Ejecuta primero: ./install.sh"
    exit 1
fi

# Activar entorno virtual
echo "🔌 Activando entorno virtual..."
source .venv/bin/activate

# Verificar que app.py existe
if [ ! -f "app.py" ]; then
    echo "❌ app.py no encontrado"
    exit 1
fi

# Ejecutar aplicación
echo "▶️  Ejecutando aplicación..."
python app.py

echo "👋 Aplicación cerrada"