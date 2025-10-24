"""
# Guía de Inicio Rápido - Pasador de Esquemas de BD

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
- **Análisis**: Dependencias y estructura del esquema

### Transferencia de Datos
- **Selección de Tablas**: Elige qué tablas transferir
- **Configuración**: Opciones de transferencia y optimización  
- **Progreso**: Monitor en tiempo real del progreso
- **Validación**: Verificación automática de integridad

### Opciones Avanzadas
- **Lotes**: Configurar tamaño de lotes para mejor rendimiento
- **Paralelo**: Transferir múltiples tablas independientes simultáneamente
- **Constraints**: Deshabilitar temporalmente para resolver ciclos
- **Continuidad**: Opciones para transferencia robusta

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

### Optimización
- **Dependencias Circulares**: Usa opciones avanzadas disponibles
- **Tablas Grandes**: Ajusta tamaño de lotes según rendimiento
- **Continuidad**: Opciones para manejar interrupciones

## � Registro de Actividad

Los logs de la aplicación se guardan automáticamente en:
```
logs/pasador_db.log
```

Incluyen información sobre:
- Conexiones realizadas
- Análisis de esquemas
- Progreso de transferencias
- Estadísticas de operaciones

¡Disfruta transfiriendo esquemas de manera inteligente! 🎉