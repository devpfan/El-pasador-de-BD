"""
Guía de Inicio Rápido - Pasador de Esquemas de BD
================================================

¡Felicidades! Has instalado exitosamente el Pasador de Esquemas de BD.

## 🚀 Primer Uso

### Opción 1: Usar Bases de Datos de Ejemplo
1. Ejecuta la aplicación:
   ```
   python app.py
   ```

2. Configura la conexión ORIGEN:
   - Tipo de BD: SQLite
   - Base de datos: [Navegar] → examples/tienda_origen.db
   - Clic en "Conectar"

3. Configura la conexión DESTINO:
   - Tipo de BD: SQLite  
   - Base de datos: [Navegar] → examples/tienda_destino.db
   - Clic en "Conectar"

4. Selecciona el esquema "main" en ORIGEN

5. Clic en "Analizar Esquema"

6. Revisa las pestañas de análisis para ver:
   - Resumen del esquema
   - Árbol de dependencias
   - Orden de transferencia calculado

7. Clic en "Iniciar Transferencia"

### Opción 2: Usar Tus Propias Bases de Datos

#### Para PostgreSQL:
- Host: tu_servidor
- Puerto: 5432 (por defecto)
- Base de datos: nombre_de_tu_bd
- Usuario/Contraseña: tus credenciales

#### Para MySQL:
- Host: tu_servidor  
- Puerto: 3306 (por defecto)
- Base de datos: nombre_de_tu_bd
- Usuario/Contraseña: tus credenciales

#### Para SQL Server:
- Host: tu_servidor
- Puerto: 1433 (por defecto)
- Base de datos: nombre_de_tu_bd
- Usuario/Contraseña: tus credenciales

## ⚡ Funciones Principales

### Análisis de Esquemas
- **Resumen**: Estadísticas generales del esquema
- **Dependencias**: Visualización del árbol de dependencias entre tablas
- **Orden**: Secuencia calculada para transferencia respetando FK
- **Problemas**: Issues detectados como dependencias circulares

### Transferencia de Datos
- **Selección de Tablas**: Elige qué tablas transferir
- **Configuración**: Opciones de transferencia y optimización  
- **Progreso**: Monitor en tiempo real del progreso
- **Validación**: Verificación automática de integridad

### Opciones Avanzadas
- **Lotes**: Configurar tamaño de lotes para mejor rendimiento
- **Paralelo**: Transferir múltiples tablas independientes simultáneamente
- **Constraints**: Deshabilitar temporalmente para resolver ciclos
- **Errores**: Continuar transferencia aunque algunas tablas fallen

## 🔧 Casos de Uso Comunes

### Migración Completa
1. Conecta a BD origen y destino
2. Analiza esquema completo
3. Revisa orden de dependencias
4. Transfiere todos los datos

### Copia Selectiva
1. Conecta a ambas BD
2. Analiza esquema origen
3. Usa "Seleccionar Tablas" para elegir subconjunto
4. Transfiere solo las tablas seleccionadas

### Manejo de Problemas
- **Dependencias Circulares**: Usa opciones avanzadas para resolver
- **Tablas Grandes**: Ajusta tamaño de lotes
- **Errores de Red**: Habilita "Continuar en caso de error"

## 🐛 Solución de Problemas

### "No se puede conectar"
- Verifica credenciales y permisos
- Confirma que el servidor esté ejecutándose
- Revisa configuración de firewall

### "Error de dependencias"
- Revisa la pestaña "Problemas"
- Considera usar "Deshabilitar constraints"
- Verifica que todas las tablas referenciadas estén incluidas

### "Rendimiento lento"
- Reduce el tamaño de lotes
- Deshabilita la verificación de datos para pruebas
- Usa transferencia paralela si no hay dependencias críticas

## 📝 Archivos de Log

Los logs se guardan automáticamente en:
```
logs/pasador_db.log
```

Incluyen información detallada sobre:
- Conexiones de BD
- Análisis de esquemas  
- Progreso de transferencia
- Errores y warnings

## 🆘 Soporte

Si encuentras problemas:

1. Revisa los logs en `logs/pasador_db.log`
2. Verifica que todas las dependencias estén instaladas
3. Prueba con las bases de datos de ejemplo primero
4. Asegúrate de tener permisos adecuados en ambas BD

¡Disfruta transfiriendo esquemas de manera inteligente! 🎉
"""