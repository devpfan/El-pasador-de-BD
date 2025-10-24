#!/usr/bin/env python3
"""
Ejemplo de uso - Crea bases de datos de prueba para demostrar la funcionalidad
"""

import sqlite3
import os
from pathlib import Path

def create_sample_databases():
    """Crea bases de datos SQLite de ejemplo para pruebas"""
    
    examples_dir = Path(__file__).parent
    
    # Base de datos origen (tienda online)
    source_db = examples_dir / "tienda_origen.db"
    target_db = examples_dir / "tienda_destino.db"
    
    # Eliminar si existen
    if source_db.exists():
        os.remove(source_db)
    if target_db.exists():
        os.remove(target_db)
    
    # Crear BD origen con datos de ejemplo
    print("Creando base de datos origen...")
    
    conn = sqlite3.connect(source_db)
    cursor = conn.cursor()
    
    # Crear tablas con dependencias
    cursor.execute("""
        CREATE TABLE categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(100) NOT NULL,
            descripcion TEXT,
            activo BOOLEAN DEFAULT 1
        )
    """)
    
    cursor.execute("""
        CREATE TABLE proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(100) NOT NULL,
            email VARCHAR(100),
            telefono VARCHAR(20),
            direccion TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(200) NOT NULL,
            descripcion TEXT,
            precio DECIMAL(10,2) NOT NULL,
            stock INTEGER DEFAULT 0,
            categoria_id INTEGER,
            proveedor_id INTEGER,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id),
            FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(100) NOT NULL,
            apellido VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE,
            telefono VARCHAR(20),
            direccion TEXT,
            fecha_registro DATE DEFAULT CURRENT_DATE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            fecha DATE DEFAULT CURRENT_DATE,
            total DECIMAL(10,2) DEFAULT 0,
            estado VARCHAR(20) DEFAULT 'pendiente',
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE detalle_pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    """)
    
    # Insertar datos de ejemplo
    print("Insertando datos de ejemplo...")
    
    # Categorías
    categorias = [
        ("Electrónicos", "Dispositivos y gadgets electrónicos"),
        ("Ropa", "Prendas de vestir y accesorios"),
        ("Hogar", "Artículos para el hogar"),
        ("Deportes", "Equipos y ropa deportiva"),
        ("Libros", "Literatura y material educativo")
    ]
    
    cursor.executemany(
        "INSERT INTO categorias (nombre, descripcion) VALUES (?, ?)",
        categorias
    )
    
    # Proveedores
    proveedores = [
        ("TechCorp", "tech@techcorp.com", "555-1001", "Calle Tech 123"),
        ("FashionWorld", "info@fashion.com", "555-1002", "Av. Moda 456"),
        ("HomeGoods", "ventas@home.com", "555-1003", "Plaza Hogar 789"),
        ("SportsPro", "contacto@sports.com", "555-1004", "Estadio 321"),
        ("BookHouse", "libros@books.com", "555-1005", "Biblioteca 654")
    ]
    
    cursor.executemany(
        "INSERT INTO proveedores (nombre, email, telefono, direccion) VALUES (?, ?, ?, ?)",
        proveedores
    )
    
    # Productos
    productos = [
        ("Laptop Gaming", "Laptop para juegos de alta gama", 1299.99, 10, 1, 1),
        ("Smartphone Pro", "Teléfono inteligente premium", 899.99, 25, 1, 1),
        ("Auriculares Bluetooth", "Auriculares inalámbricos", 199.99, 50, 1, 1),
        ("Camisa Casual", "Camisa de algodón casual", 49.99, 30, 2, 2),
        ("Jeans Premium", "Jeans de mezclilla premium", 89.99, 20, 2, 2),
        ("Zapatillas Running", "Zapatillas para correr", 129.99, 15, 4, 4),
        ("Pelota Fútbol", "Pelota oficial de fútbol", 29.99, 40, 4, 4),
        ("Lámpara LED", "Lámpara LED de escritorio", 39.99, 35, 3, 3),
        ("Cojín Decorativo", "Cojín para sofá", 19.99, 60, 3, 3),
        ("Novela Bestseller", "Libro de ficción popular", 14.99, 100, 5, 5)
    ]
    
    cursor.executemany(
        "INSERT INTO productos (nombre, descripcion, precio, stock, categoria_id, proveedor_id) VALUES (?, ?, ?, ?, ?, ?)",
        productos
    )
    
    # Clientes
    clientes = [
        ("Juan", "Pérez", "juan.perez@email.com", "555-2001", "Calle Principal 123"),
        ("María", "González", "maria.g@email.com", "555-2002", "Av. Central 456"),
        ("Carlos", "Rodríguez", "carlos.r@email.com", "555-2003", "Plaza Mayor 789"),
        ("Ana", "López", "ana.lopez@email.com", "555-2004", "Calle Norte 321"),
        ("Pedro", "Martínez", "pedro.m@email.com", "555-2005", "Av. Sur 654")
    ]
    
    cursor.executemany(
        "INSERT INTO clientes (nombre, apellido, email, telefono, direccion) VALUES (?, ?, ?, ?, ?)",
        clientes
    )
    
    # Pedidos
    pedidos = [
        (1, "2024-01-15", 1499.98, "completado"),
        (2, "2024-01-16", 249.97, "completado"),
        (3, "2024-01-17", 159.98, "pendiente"),
        (1, "2024-01-18", 89.99, "enviado"),
        (4, "2024-01-19", 44.98, "completado")
    ]
    
    cursor.executemany(
        "INSERT INTO pedidos (cliente_id, fecha, total, estado) VALUES (?, ?, ?, ?)",
        pedidos
    )
    
    # Detalle de pedidos
    detalles = [
        (1, 1, 1, 1299.99),  # Pedido 1: Laptop
        (1, 3, 1, 199.99),   # Pedido 1: Auriculares
        (2, 2, 1, 899.99),   # Pedido 2: Smartphone
        (2, 4, 3, 49.99),    # Pedido 2: 3 Camisas
        (3, 6, 1, 129.99),   # Pedido 3: Zapatillas
        (3, 7, 1, 29.99),    # Pedido 3: Pelota
        (4, 5, 1, 89.99),    # Pedido 4: Jeans
        (5, 9, 2, 19.99),    # Pedido 5: 2 Cojines
        (5, 10, 1, 14.99)    # Pedido 5: Libro
    ]
    
    cursor.executemany(
        "INSERT INTO detalle_pedidos (pedido_id, producto_id, cantidad, precio_unitario) VALUES (?, ?, ?, ?)",
        detalles
    )
    
    conn.commit()
    conn.close()
    
    # Crear BD destino vacía
    print("Creando base de datos destino vacía...")
    conn_target = sqlite3.connect(target_db)
    conn_target.close()
    
    print(f"✅ Bases de datos creadas:")
    print(f"   Origen: {source_db}")
    print(f"   Destino: {target_db}")
    print()
    print("Puedes usar estas bases de datos para probar la aplicación:")
    print("1. Ejecuta: python app.py")
    print("2. Configura conexión origen con tienda_origen.db")
    print("3. Configura conexión destino con tienda_destino.db")
    print("4. Analiza el esquema 'main' de la BD origen")
    print("5. Transfiere a la BD destino")


if __name__ == "__main__":
    create_sample_databases()