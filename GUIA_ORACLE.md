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

#### 🔹 Origen - Conexión Múltiple DEV
- **Host**: 10.1.20.42
- **Puerto**: 1521  
- **Service Name**: conexionmul
- **Usuario**: SICOFCONFIG
- **Password**: SICOFCONFIG
- **Esquema**: SICOFCONFIG

#### 🔹 Destino - Bello 110  
- **Host**: 10.1.140.101
- **Puerto**: 1521
- **Service Name**: db110
- **Usuario**: FISCA
- **Password**: fisca
- **Esquema**: SICOFCONFIG

## 🚀 Uso Rápido

### Método 1: Cargar Configuración Automática
1. Abrir aplicación: `python app.py`
2. Menú → Archivo → "Cargar Config Oracle"
3. Las conexiones se cargarán automáticamente
4. Clic "Conectar" en ambos paneles
5. Seleccionar esquema "SICOFCONFIG" en origen

### Método 2: Configuración Manual
1. **Panel Origen**:
   - Tipo: Oracle
   - Host: 10.1.20.42
   - Puerto: 1521
   - Database: conexionmul
   - Usuario: SICOFCONFIG
   - Password: SICOFCONFIG

2. **Panel Destino**:
   - Tipo: Oracle  
   - Host: 10.1.140.101
   - Puerto: 1521
   - Database: db110
   - Usuario: FISCA
   - Password: fisca

## 📋 Flujo de Transferencia

1. **Conectar a ambas BD** y verificar que aparezcan los esquemas
2. **Seleccionar esquema SICOFCONFIG** en origen
3. **Clic "Analizar Esquema"** - El sistema:
   - Detectará todas las tablas del esquema
   - Analizará dependencias entre tablas
   - Calculará orden correcto de inserción
   - Identificará posibles problemas

4. **Revisar análisis**:
   - **Resumen**: Estadísticas generales
   - **Dependencias**: Árbol visual de relaciones
   - **Orden**: Secuencia calculada para transferencia
   - **Problemas**: Issues como dependencias circulares

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

## 🐛 Solución de Problemas Oracle

### Error: "Oracle client not found"
```bash
# Instalar cliente Oracle
sudo apt install oracle-instantclient-basic

# O descargar manualmente de Oracle y configurar:
export ORACLE_HOME=/path/to/oracle/client
export LD_LIBRARY_PATH=$ORACLE_HOME/lib
```

### Error: "TNS: could not resolve service name"
- Verificar que el service name esté correcto
- Probar conectividad: `telnet 10.1.20.42 1521`
- Verificar que el servicio Oracle esté ejecutándose

### Error: "ORA-12541: TNS:no listener"
- El puerto 1521 no está abierto o el listener no está activo
- Contactar al administrador de BD
- Verificar firewall entre servidores

### Error: "ORA-01017: invalid username/password"
- Verificar credenciales
- El usuario puede estar bloqueado
- Verificar que el usuario tenga permisos de conexión

### Performance Lento
- Reducir batch size a 500 o menos
- Verificar índices en tablas grandes
- Usar transferencia paralela solo para tablas independientes
- Considerar horarios de menor carga

### Dependencias Circulares
- Revisar pestaña "Problemas" en el análisis
- Usar "Deshabilitar constraints temporalmente"
- Identificar FK que pueden ser NULL e insertar en dos fases

## 📊 Monitoreo

### Logs Detallados
Los logs se guardan en: `logs/pasador_db.log`

Incluyen:
- Conexiones exitosas/fallidas
- Progreso tabla por tabla  
- Errores específicos de Oracle
- Tiempos de transferencia
- Validación de integridad

### Progreso en Tiempo Real
- Tabla actual siendo procesada
- Filas transferidas vs total
- Tiempo estimado restante
- Errores y warnings

## 💡 Tips para Oracle

1. **Esquemas vs Usuarios**: En Oracle, esquema = usuario propietario
2. **Service Name vs SID**: Usa service name cuando sea posible
3. **Tablespaces**: La aplicación no transfiere tablespaces, usa los por defecto
4. **Secuencias**: Se recrearán automáticamente pero sin valores actuales
5. **Sinónimos**: No se transfieren, solo tablas base
6. **Triggers**: Se pueden transferir pero verificar que no interfieran

¡La configuración está lista para usar! 🎉