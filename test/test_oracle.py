#!/usr/bin/env python3
"""
Script de prueba para conexiones Oracle
Verifica conectividad antes de usar la aplicación principal
"""

import sys
import json
from pathlib import Path

# Agregar directorio actual al path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from database_manager import DatabaseManager
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    sys.exit(1)

def test_oracle_connections():
    """Prueba las conexiones Oracle configuradas"""
    
    print("🔍 Probando conexiones Oracle...")
    print("=" * 50)
    
    # Cargar configuración
    config_file = Path(__file__).parent.parent / "config" / "oracle_config.json"
    
    if not config_file.exists():
        print(f"❌ Archivo de configuración no encontrado: {config_file}")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Error leyendo configuración: {e}")
        return False
    
    if 'connections' not in config:
        print("❌ Formato de configuración inválido")
        return False
    
    # Probar cada conexión
    db_manager = DatabaseManager()
    all_success = True
    
    for conn_id, conn_config in config['connections'].items():
        print(f"\n🔗 Probando: {conn_config.get('name', conn_id)}")
        print(f"   Host: {conn_config.get('host')}")
        print(f"   Puerto: {conn_config.get('port')}")
        print(f"   BD: {conn_config.get('database')}")
        print(f"   Usuario: {conn_config.get('user')}")
        
        # Convertir formato de configuración
        test_config = {
            'db_type': conn_config.get('type', 'oracle').lower(),
            'host': conn_config.get('host'),
            'port': conn_config.get('port', 1521),
            'database': conn_config.get('database'),
            'user': conn_config.get('user'),
            'password': conn_config.get('password')
        }
        
        try:
            success, message = db_manager.test_connection('oracle', test_config)
            
            if success:
                print(f"   ✅ {message}")
                
                # Intentar obtener esquemas
                try:
                    engine = db_manager.get_engine(conn_id, 'oracle', test_config)
                    schemas = db_manager.get_schemas(engine, 'oracle')
                    print(f"   📁 Esquemas disponibles: {len(schemas)}")
                    
                    # Mostrar algunos esquemas
                    if schemas:
                        print(f"      {', '.join(schemas[:5])}")
                        if len(schemas) > 5:
                            print(f"      ... y {len(schemas) - 5} más")
                    
                    # Probar esquema por defecto si está configurado
                    default_schema = conn_config.get('schema_default')
                    if default_schema and default_schema in schemas:
                        print(f"   🎯 Esquema por defecto encontrado: {default_schema}")
                        
                        # Obtener algunas tablas del esquema
                        try:
                            tables = db_manager.get_tables(engine, 'oracle', default_schema)
                            print(f"      📊 Tablas en {default_schema}: {len(tables)}")
                            if tables:
                                print(f"      Ejemplos: {', '.join(tables[:3])}")
                                if len(tables) > 3:
                                    print(f"      ... y {len(tables) - 3} más")
                        except Exception as e:
                            print(f"      ⚠️ No se pudieron obtener tablas: {e}")
                    
                except Exception as e:
                    print(f"   ⚠️ Error obteniendo esquemas: {e}")
                    all_success = False
                    
            else:
                print(f"   ❌ {message}")
                all_success = False
                
        except Exception as e:
            print(f"   ❌ Error de conexión: {e}")
            all_success = False
    
    print("\n" + "=" * 50)
    
    if all_success:
        print("🎉 ¡Todas las conexiones Oracle funcionan correctamente!")
        print("\n📋 Próximos pasos:")
        print("1. Ejecutar: python app.py")
        print("2. Menú → Archivo → Cargar Config Oracle")
        print("3. Conectar a ambas bases de datos")
        print("4. Analizar esquema SICOFCONFIG")
        print("5. Transferir datos")
        return True
    else:
        print("❌ Algunas conexiones fallaron")
        print("\n🔧 Posibles soluciones:")
        print("- Verificar que Oracle Instant Client esté instalado")
        print("- Comprobar conectividad de red a los servidores")
        print("- Validar credenciales de usuario")
        print("- Revisar que los servicios Oracle estén ejecutándose")
        return False

def check_oracle_client():
    """Verifica que el cliente Oracle esté disponible"""
    
    print("🔍 Verificando cliente Oracle...")
    
    try:
        import cx_Oracle
        print("✅ cx_Oracle importado correctamente")
        
        # Verificar versión
        try:
            version = cx_Oracle.version
            print(f"📋 Versión cx_Oracle: {version}")
        except:
            pass
            
        # Verificar cliente Oracle
        try:
            client_info = cx_Oracle.clientversion()
            print(f"📋 Cliente Oracle: {'.'.join(map(str, client_info))}")
        except Exception as e:
            print(f"⚠️ No se pudo determinar versión del cliente: {e}")
            print("   Asegúrate de que Oracle Instant Client esté instalado")
            
        return True
        
    except ImportError as e:
        print(f"❌ cx_Oracle no disponible: {e}")
        print("\n🔧 Para instalar:")
        print("1. Instalar Oracle Instant Client:")
        print("   https://www.oracle.com/database/technologies/instant-client.html")
        print("2. Instalar cx_Oracle:")
        print("   pip install cx_Oracle")
        print("3. Configurar variables de entorno si es necesario")
        return False

if __name__ == "__main__":
    print("🔧 VERIFICACIÓN DE ORACLE - Pasador de Esquemas de BD")
    print("=" * 60)
    
    # Verificar cliente Oracle
    if not check_oracle_client():
        print("\n❌ Cliente Oracle no disponible. Instalar antes de continuar.")
        sys.exit(1)
    
    print()
    
    # Probar conexiones
    success = test_oracle_connections()
    
    if success:
        print(f"\n🚀 ¡Listo para transferir esquemas Oracle!")
        sys.exit(0)
    else:
        print(f"\n⚠️ Revisar configuración antes de continuar")
        sys.exit(1)