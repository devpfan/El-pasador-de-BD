# Guía Oracle - Pasador de Esquemas de BD

## 🔧 Configuración Oracle

### Prerrequisitos

1. **Cliente Oracle Instant Client**:
   ```bash
   # Descargar de Oracle: https://www.oracle.com/database/technologies/instant-client.html
   # O instalar usando apt (Ubuntu):
   sudo apt-get install oracle-instantclient-basic
   sudo apt-get install oracle-instantclient-devel
   
   # Configurar variables de entorno:
   export ORACLE_HOME=/usr/lib/oracle/21/client64
   export LD_LIBRARY_PATH=$ORACLE_HOME/lib:$LD_LIBRARY_PATH
   export PATH=$ORACLE_HOME/bin:$PATH
   ```

2. **Biblioteca cx_Oracle**:
   ```bash
   pip install cx_Oracle
   ```

### Conexiones Configuradas

#### Ejemplo de Configuración Oracle
- **Host**: tu_servidor_oracle
- **Puerto**: 1521 (puerto estándar)  
- **Service Name**: nombre_servicio
- **Usuario**: tu_usuario
- **Password**: tu_password
- **Esquema**: esquema_origen

## 🚀 Uso Rápido

### Configuración de Conexión
1. **Abrir aplicación**: `python app.py`

2. **Panel Origen**:
   - Tipo: Oracle
   - Host: tu_servidor_origen
   - Puerto: 1521
   - Service Name: tu_servicio
   - Usuario: tu_usuario
   - Password: tu_password

3. **Panel Destino**:
   - Tipo: Oracle (u otro tipo de BD)
   - Configurar según tu BD destino

## 📋 Flujo de Transferencia

1. **Conectar a ambas BD** y verificar que aparezcan los esquemas
2. **Seleccionar esquema origen** en la lista desplegable
3. **Clic "Analizar Esquema"** - El sistema:
   - Detectará todas las tablas del esquema
   - Analizará dependencias entre tablas
   - Calculará orden correcto de inserción
   - Identificará la estructura y dependencias

4. **Revisar análisis**:
   - **Resumen**: Estadísticas generales
   - **Dependencias**: Árbol visual de relaciones
   - **Orden**: Secuencia calculada para transferencia
   - **Análisis**: Estructura y dependencias del esquema

5. **Opcional: Seleccionar tablas específicas**
   - Clic "Seleccionar Tablas" si no quieres transferir todo
   - Marca las tablas deseadas
   - El sistema recalculará dependencias

6. **Iniciar transferencia**:
   - Clic "Iniciar Transferencia"
   - Configurar opciones avanzadas si es necesario
   - Monitorear progreso en tiempo real

## ⚙️ Opciones Oracle Específicas

### En el Diálogo de Transferencia:

**General**:
- ✅ Crear esquema destino
- ✅ Crear tablas
- ⚠️ Eliminar tablas existentes (cuidado)

**Avanzado**:
- 🔄 Deshabilitar constraints (para dependencias circulares)
- ⚡ Transferencia paralela (si no hay dependencias críticas)
- ✅ Verificar datos al final
- 📊 Tamaño de lote: 1000 (ajustar según rendimiento)

## � Funcionalidades Oracle

### Objetos Soportados
- **Tablas**: Estructura completa con PKs y FKs
- **Vistas**: Definiciones y dependencias
- **Secuencias**: Parámetros completos (START, INCREMENT, etc.)
- **Procedimientos/Funciones**: Código PL/SQL completo
- **Triggers**: Tipos BEFORE/AFTER/INSTEAD OF
- **Índices**: Índices personalizados (excluye automáticos)

### Transferencia Optimizada
- Resolución automática de dependencias
- Orden inteligente de creación de objetos
- Manejo de dependencias circulares
- Adaptación de sintaxis entre diferentes BD

## 💡 Tips para Oracle

1. **Esquemas vs Usuarios**: En Oracle, esquema = usuario propietario
2. **Service Name vs SID**: Usa service name cuando sea posible
3. **Tablespaces**: La aplicación no transfiere tablespaces, usa los por defecto
4. **Secuencias**: Se recrearán automáticamente pero sin valores actuales
5. **Sinónimos**: No se transfieren, solo tablas base
6. **Triggers**: Se pueden transferir pero verificar que no interfieran

¡La configuración está lista para usar! 🎉