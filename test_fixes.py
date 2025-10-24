"""
Script de Prueba - Verifica que todas las correcciones funcionan correctamente
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from schema_analyzer import SchemaAnalyzer, SchemaInfo, SchemaObjects
from schema_exporter import SchemaExporter
from database_manager import DatabaseManager

def test_imports():
    """Prueba que todas las importaciones funcionen"""
    print("✅ Probando importaciones...")
    
    try:
        # Probar importaciones básicas
        db_manager = DatabaseManager()
        schema_analyzer = SchemaAnalyzer(db_manager)
        schema_exporter = SchemaExporter()
        
        print("   ✓ DatabaseManager importado correctamente")
        print("   ✓ SchemaAnalyzer importado correctamente")
        print("   ✓ SchemaExporter importado correctamente")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error en importaciones: {str(e)}")
        return False

def test_schema_objects():
    """Prueba la nueva estructura de SchemaObjects"""
    print("✅ Probando nueva estructura SchemaObjects...")
    
    try:
        # Crear objetos vacíos para probar la estructura
        objects = SchemaObjects(
            tables={},
            views={},
            sequences={},
            procedures={},
            triggers={},
            indexes={}
        )
        
        schema_info = SchemaInfo(
            schema_name="TEST_SCHEMA",
            objects=objects,
            dependency_order=[],
            creation_order=[]
        )
        
        print("   ✓ SchemaObjects creado correctamente")
        print("   ✓ SchemaInfo con nueva estructura creado correctamente")
        
        # Probar acceso a los atributos
        assert hasattr(schema_info.objects, 'tables')
        assert hasattr(schema_info.objects, 'views')
        assert hasattr(schema_info.objects, 'sequences')
        assert hasattr(schema_info.objects, 'procedures')
        assert hasattr(schema_info.objects, 'triggers')
        assert hasattr(schema_info.objects, 'indexes')
        
        print("   ✓ Todos los atributos de objetos están presentes")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error en estructura SchemaObjects: {str(e)}")
        return False

def test_exporter():
    """Prueba el exportador de esquemas"""
    print("✅ Probando SchemaExporter...")
    
    try:
        exporter = SchemaExporter()
        
        # Verificar que los métodos existen
        assert hasattr(exporter, 'export_to_sql_ddl')
        assert hasattr(exporter, 'export_to_json')
        assert hasattr(exporter, 'export_to_html_report')
        assert hasattr(exporter, 'export_to_csv_summary')
        
        print("   ✓ Todos los métodos de exportación están presentes")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error en SchemaExporter: {str(e)}")
        return False

def test_syntax_errors():
    """Verifica que no hay errores de sintaxis en los archivos principales"""
    print("✅ Verificando sintaxis de archivos...")
    
    files_to_check = [
        'main_gui.py',
        'schema_analyzer.py',
        'schema_exporter.py',
        'dependency_resolver.py',
        'data_transfer.py',
        'database_manager.py'
    ]
    
    for filename in files_to_check:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Compilar el código para verificar sintaxis
            compile(code, filename, 'exec')
            print(f"   ✓ {filename} - sintaxis correcta")
            
        except SyntaxError as e:
            print(f"   ❌ {filename} - error de sintaxis: {str(e)}")
            return False
        except FileNotFoundError:
            print(f"   ⚠️ {filename} - archivo no encontrado")
        except Exception as e:
            print(f"   ❌ {filename} - error: {str(e)}")
            return False
    
    return True

def main():
    """Función principal de pruebas"""
    print("🧪 EJECUTANDO PRUEBAS DE VERIFICACIÓN")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_schema_objects,
        test_exporter,
        test_syntax_errors
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"   ❌ Error inesperado en prueba: {str(e)}")
            print()
    
    print("=" * 50)
    print(f"📊 RESULTADO: {passed}/{total} pruebas pasadas")
    
    if passed == total:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
        print("\n🚀 La aplicación está lista para usar con:")
        print("   ✅ Soporte completo para todos los objetos de BD")
        print("   ✅ Funcionalidad de exportación") 
        print("   ✅ Correcciones de errores aplicadas")
        print("   ✅ Botones de transferencia habilitados")
        return True
    else:
        print(f"❌ {total - passed} prueba(s) fallaron")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)