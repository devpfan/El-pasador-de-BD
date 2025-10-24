#!/bin/bash

# Script de inicio completo para Oracle
# Activa el entorno y abre la aplicación con configuración Oracle preestablecida

echo "🔧 PASADOR DE ESQUEMAS - MODO ORACLE"
echo "===================================="

# Verificar entorno virtual
if [ ! -d ".venv" ]; then
    echo "❌ Entorno virtual no encontrado. Ejecuta ./install.sh primero"
    exit 1
fi

# Activar entorno virtual
source .venv/bin/activate

# Verificar configuración Oracle
echo "🔍 Verificando configuración Oracle..."
python test/test_oracle.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🚀 Abriendo aplicación con configuración Oracle..."
    echo "   - Se cargarán automáticamente las conexiones configuradas"
    echo "   - Origen: SICOFCONFIG@conexionmul (10.1.20.42)"
    echo "   - Destino: FISCA@db110 (10.1.140.101)"
    echo ""
    
    # Ejecutar aplicación
    python app.py
else
    echo ""
    echo "❌ La configuración Oracle tiene problemas"
    echo "   Revisa la conectividad y credenciales"
    exit 1
fi