# -*- coding: utf-8 -*-
"""
PostgreSQL Database Manager สำหรับ Production
ใช้สำหรับ deploy บน cloud platforms ที่รองรับ PostgreSQL
"""

import os
import psycopg2
import psycopg2.extras
from urllib.parse import urlparse
from datetime import datetime
import pytz
import logging

class PostgreSQLManager:
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required for PostgreSQL")
        
        # Parse database URL
        self.url = urlparse(self.database_url)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_connection(self):
        """สร้างการเชื่อมต่อกับ PostgreSQL database"""
        try:
            conn = psycopg2.connect(
                database=self.url.path[1:],
                user=self.url.username,
                password=self.url.password,
                host=self.url.hostname,
                port=self.url.port,
                sslmode='require'  # Required for most cloud PostgreSQL services
            )
            return conn
        except Exception as e:
            self.logger.error(f"Database connection error: {e}")
            raise
    
    def init_database(self):
        """สร้างตารางฐานข้อมูลสำหรับ PostgreSQL"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # สร้างตาราง tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tables (
                    table_id SERIAL PRIMARY KEY,
                    table_name VARCHAR(50) NOT NULL,
                    status VARCHAR(20) DEFAULT 'available'
                )
            """)
            
            # สร้างตาราง menu_categories
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS menu_categories (
                    category_id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT
                )
            """)
            
            # สร้างตาราง menu_items
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS menu_items (
                    item_id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    price DECIMAL(10,2) NOT NULL,
                    category_id INTEGER REFERENCES menu_categories(category_id),
                    image_url VARCHAR(500),
                    available BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # สร้างตาราง orders
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id SERIAL PRIMARY KEY,
                    table_id INTEGER REFERENCES tables(table_id),
                    customer_name VARCHAR(100),
                    customer_phone VARCHAR(20),
                    total_amount DECIMAL(10,2) DEFAULT 0.00,
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                )
            """)
            
            # สร้างตาราง order_items
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    order_item_id SERIAL PRIMARY KEY,
                    order_id INTEGER REFERENCES orders(order_id) ON DELETE CASCADE,
                    item_id INTEGER REFERENCES menu_items(item_id),
                    quantity INTEGER NOT NULL DEFAULT 1,
                    unit_price DECIMAL(10,2) NOT NULL,
                    total_price DECIMAL(10,2) NOT NULL,
                    special_requests TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # สร้างตาราง food_options
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS food_options (
                    option_id SERIAL PRIMARY KEY,
                    item_id INTEGER REFERENCES menu_items(item_id) ON DELETE CASCADE,
                    option_name VARCHAR(100) NOT NULL,
                    option_type VARCHAR(50) NOT NULL,
                    additional_price DECIMAL(10,2) DEFAULT 0.00,
                    available BOOLEAN DEFAULT TRUE
                )
            """)
            
            # สร้างตาราง order_item_options
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_item_options (
                    order_item_option_id SERIAL PRIMARY KEY,
                    order_item_id INTEGER REFERENCES order_items(order_item_id) ON DELETE CASCADE,
                    option_id INTEGER REFERENCES food_options(option_id),
                    selected_value VARCHAR(100),
                    additional_price DECIMAL(10,2) DEFAULT 0.00
                )
            """)
            
            # สร้าง indexes สำหรับ performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_table_id ON orders(table_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_menu_items_category_id ON menu_items(category_id)")
            
            conn.commit()
            self.logger.info("PostgreSQL database initialized successfully")
            
            # เพิ่มข้อมูลเริ่มต้นถ้ายังไม่มี
            self._add_initial_data(cursor, conn)
            
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error initializing database: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def _add_initial_data(self, cursor, conn):
        """เพิ่มข้อมูลเริ่มต้น"""
        try:
            # ตรวจสอบว่ามีโต๊ะแล้วหรือไม่
            cursor.execute("SELECT COUNT(*) FROM tables")
            table_count = cursor.fetchone()[0]
            
            if table_count == 0:
                # เพิ่มโต๊ะ 10 โต๊ะ
                for i in range(1, 11):
                    cursor.execute(
                        "INSERT INTO tables (table_name, status) VALUES (%s, %s)",
                        (f"Table {i}", "available")
                    )
                self.logger.info("Added initial tables")
            
            # ตรวจสอบว่ามีหมวดหมู่เมนูแล้วหรือไม่
            cursor.execute("SELECT COUNT(*) FROM menu_categories")
            category_count = cursor.fetchone()[0]
            
            if category_count == 0:
                # เพิ่มหมวดหมู่เมนูเริ่มต้น
                categories = [
                    ("อาหารจานหลัก", "อาหารจานหลักและข้าว"),
                    ("เครื่องดื่ม", "เครื่องดื่มทุกประเภท"),
                    ("ของหวาน", "ของหวานและขนม"),
                    ("อาหารว่าง", "อาหารว่างและของทานเล่น")
                ]
                
                for name, desc in categories:
                    cursor.execute(
                        "INSERT INTO menu_categories (name, description) VALUES (%s, %s)",
                        (name, desc)
                    )
                self.logger.info("Added initial menu categories")
            
            conn.commit()
            
        except Exception as e:
            self.logger.error(f"Error adding initial data: {e}")
            raise
    
    def migrate_from_sqlite(self, sqlite_db_path):
        """Migration ข้อมูลจาก SQLite ไปยัง PostgreSQL"""
        import sqlite3
        
        # เชื่อมต่อ SQLite
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        # เชื่อมต่อ PostgreSQL
        pg_conn = self.get_connection()
        pg_cursor = pg_conn.cursor()
        
        try:
            # Migration tables
            sqlite_cursor.execute("SELECT table_id, table_name, status FROM tables")
            tables_data = sqlite_cursor.fetchall()
            
            for table_data in tables_data:
                pg_cursor.execute(
                    "INSERT INTO tables (table_id, table_name, status) VALUES (%s, %s, %s) ON CONFLICT (table_id) DO NOTHING",
                    table_data
                )
            
            # Migration menu_categories
            sqlite_cursor.execute("SELECT category_id, name, description FROM menu_categories")
            categories_data = sqlite_cursor.fetchall()
            
            for category_data in categories_data:
                pg_cursor.execute(
                    "INSERT INTO menu_categories (category_id, name, description) VALUES (%s, %s, %s) ON CONFLICT (category_id) DO NOTHING",
                    category_data
                )
            
            # Migration menu_items
            sqlite_cursor.execute("SELECT item_id, name, description, price, category_id, image_url, available, created_at FROM menu_items")
            items_data = sqlite_cursor.fetchall()
            
            for item_data in items_data:
                pg_cursor.execute(
                    "INSERT INTO menu_items (item_id, name, description, price, category_id, image_url, available, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (item_id) DO NOTHING",
                    item_data
                )
            
            # Migration orders
            sqlite_cursor.execute("SELECT order_id, table_id, customer_name, customer_phone, total_amount, status, created_at, updated_at, notes FROM orders")
            orders_data = sqlite_cursor.fetchall()
            
            for order_data in orders_data:
                pg_cursor.execute(
                    "INSERT INTO orders (order_id, table_id, customer_name, customer_phone, total_amount, status, created_at, updated_at, notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (order_id) DO NOTHING",
                    order_data
                )
            
            # Migration order_items
            sqlite_cursor.execute("SELECT order_item_id, order_id, item_id, quantity, unit_price, total_price, special_requests, created_at FROM order_items")
            order_items_data = sqlite_cursor.fetchall()
            
            for order_item_data in order_items_data:
                pg_cursor.execute(
                    "INSERT INTO order_items (order_item_id, order_id, item_id, quantity, unit_price, total_price, special_requests, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (order_item_id) DO NOTHING",
                    order_item_data
                )
            
            pg_conn.commit()
            self.logger.info("Migration from SQLite to PostgreSQL completed successfully")
            
        except Exception as e:
            pg_conn.rollback()
            self.logger.error(f"Error during migration: {e}")
            raise
        finally:
            sqlite_cursor.close()
            sqlite_conn.close()
            pg_cursor.close()
            pg_conn.close()
    
    def get_thai_datetime(self):
        """ได้รับเวลาปัจจุบันในโซนเวลาไทย"""
        thai_tz = pytz.timezone('Asia/Bangkok')
        return datetime.now(thai_tz)