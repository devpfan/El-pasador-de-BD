# 🚀 El Pasador de BD

**Herramienta profesional para migración y análisis de esquemas de bases de datos**

Una aplicación completa para transferir esquemas entre diferentes tipos de bases de datos con análisis automático de dependencias y exportación a múltiples formatos.

## ✨ Características principales

- 🔗 **Soporte multi-BD**: PostgreSQL, MySQL, Oracle, SQL Server, SQLite
- 🧠 **Análisis inteligente**: Detección automática de dependencias y ciclos
- 📊 **Objetos completos**: Tablas, vistas, secuencias, procedimientos, triggers, índices
- 📤 **Exportación múltiple**: SQL DDL, JSON, HTML, CSV
- 🎯 **Orden inteligente**: Resolución automática del orden de creación/inserción
- 🖥️ **Interfaz gráfica**: GUI profesional con pestañas organizadas
- ⚡ **Transferencia optimizada**: Procesamiento por lotes y paralelo
- 🔍 **Visualización de dependencias**: Árbol jerárquico y niveles de procesamiento

## 📋 Requisitos

- Python 3.7+
- Tkinter (incluido en la mayoría de distribuciones Python)
- Bibliotecas específicas según la BD que uses:
  - PostgreSQL: `psycopg2-binary`
  - MySQL: `mysql-connector-python`
  - SQL Server: `pymssql`
  - Oracle: `cx_Oracle` + Oracle Instant Client
  - SQLite: Incluido en Python

## 🛠️ Instalación

1. **Clonar o descargar el proyecto**:
   ```bash
   git clone <repositorio> pasador_db
   cd pasador_db
   ```

2. **Crear entorno virtual** (recomendado):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # o en Windows: .venv\Scripts\activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar aplicación**:
   ```bash
   python app.py
   ```

## 💡 Uso Rápido

### Paso 1: Configurar Conexiones
1. Abre la aplicación
2. En "Base de Datos Origen", configura la conexión a tu BD fuente
3. En "Base de Datos Destino", configura la conexión a tu BD destino
4. Usa "Probar Conexión" para verificar que las configuraciones son correctas

### Paso 2: Analizar Esquema
1. Selecciona el esquema origen en la lista
2. Haz clic en "Analizar Esquema"
3. Revisa la información en las pestañas de análisis:
   - **Resumen**: Información general del esquema
   - **Dependencias**: Árbol de dependencias entre tablas
   - **Orden de Transferencia**: Secuencia calculada para inserción
   - **Problemas**: Issues detectados (FK faltantes, ciclos, etc.)

### Paso 3: Transferir Datos
1. Opcionalmente, usa "Seleccionar Tablas" para elegir tablas específicas
2. Haz clic en "Iniciar Transferencia"
3. Configura las opciones de transferencia en el diálogo
4. Monitorea el progreso en tiempo real

## 🔧 Características Avanzadas

### Resolución de Dependencias Circulares
La aplicación detecta automáticamente dependencias circulares y sugiere estrategias:
- **FK Nullable**: Insertar con valores nulos y actualizar después
- **Deshabilitar Constraints**: Temporalmente desactivar validaciones FK

### Optimizaciones de Rendimiento
- **Transferencia por Lotes**: Procesa datos en chunks configurables
- **Procesamiento Paralelo**: Transfiere múltiples tablas independientes simultáneamente
- **Índices Inteligentes**: Sugiere índices para mejorar rendimiento

### Validación de Integridad
- **Verificación de Conteos**: Compara número de filas origen vs destino
- **Validación de Constraints**: Verifica que todas las FK sean válidas
- **Reporte de Errores**: Log detallado de cualquier problema encontrado

## 📁 Estructura del Proyecto

```
pasador_db/
├── app.py                 # Punto de entrada principal
├── main_gui.py           # Interfaz gráfica principal
├── database_manager.py   # Manejo de conexiones BD
├── schema_analyzer.py    # Análisis de esquemas y metadata
├── dependency_resolver.py # Resolución de dependencias
├── data_transfer.py      # Motor de transferencia de datos
├── requirements.txt      # Dependencias Python
├── README.md            # Este archivo
├── logs/                # Directorio de logs (se crea automáticamente)
└── config/              # Configuraciones de ejemplo
    └── config_ejemplo.json
```

## ⚙️ Configuración

### Archivo de Configuración
La aplicación puede cargar configuraciones desde archivos JSON:

```json
{
  "connections": {
    "mi_postgresql": {
      "type": "postgresql",
      "host": "localhost",
      "port": 5432,
      "database": "mi_bd",
      "user": "usuario",
      "password": ""
    }
  },
  "transfer_defaults": {
    "batch_size": 1000,
    "max_workers": 4,
    "verify_data": true
  }
}
```

### Variables de Entorno
Puedes usar variables de entorno para configuraciones sensibles:
- `DB_PASSWORD_SOURCE`: Contraseña BD origen
- `DB_PASSWORD_TARGET`: Contraseña BD destino

## 🐛 Solución de Problemas

### Error: "tkinter no está disponible"
En sistemas Linux, instala el paquete tkinter:
```bash
sudo apt-get install python3-tk  # Ubuntu/Debian
sudo yum install tkinter         # CentOS/RHEL
```

### Error de Conexión a BD
1. Verifica que el servidor de BD esté ejecutándose
2. Confirma credenciales y permisos de usuario
3. Revisa configuración de firewall/red
4. Para PostgreSQL, verifica `pg_hba.conf`
5. Para MySQL, verifica que el usuario tenga permisos remotos

### Problemas de Rendimiento
1. Ajusta `batch_size` según tu hardware
2. Usa `max_workers` apropiado para tu CPU
3. Considera deshabilitar constraints temporalmente
4. Para tablas muy grandes, usa transferencia paralela

### Dependencias Circulares
1. Revisa la pestaña "Problemas" para ver ciclos detectados
2. Identifica FK que pueden ser nullable
3. Considera reestructurar el esquema si es posible
4. Usa la opción "Deshabilitar constraints" como último recurso

## 📊 Casos de Uso Típicos

### Migración Entre Tipos de BD
```
PostgreSQL → MySQL
- Mapeo automático de tipos de datos
- Conversión de secuencias a AUTO_INCREMENT
- Adaptación de sintaxis específica
```

### Copia de Esquema para Testing
```
Producción → Desarrollo
- Transferir estructura y datos de referencia
- Mantener integridad referencial
- Verificar que todo funciona correctamente
```

### Backup Selectivo
```
Esquema Específico → Archivo SQLite
- Respaldar solo tablas relacionadas
- Formato portable y compacto
- Fácil de restaurar
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver archivo [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- SQLAlchemy por la abstracción de bases de datos
- Pandas por el manejo eficiente de datos
- Tkinter por la interfaz gráfica multiplataforma
- Comunidad Python por las excelentes librerías