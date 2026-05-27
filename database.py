import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'jee_cell.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Admin table
    c.execute('''CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Categories
    c.execute('''CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        icon TEXT DEFAULT 'fas fa-box',
        description TEXT,
        sort_order INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Products
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category_id INTEGER,
        price REAL DEFAULT 0,
        price_label TEXT,
        description TEXT,
        image_url TEXT,
        stock INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        is_featured INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
    )''')

    # Settings (key-value store)
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        value TEXT
    )''')

    # Announcements / Promo
    c.execute('''CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT,
        icon TEXT DEFAULT 'fas fa-bullhorn',
        is_active INTEGER DEFAULT 1,
        sort_order INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Transactions log (simple)
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        description TEXT,
        amount REAL DEFAULT 0,
        customer_name TEXT,
        customer_phone TEXT,
        notes TEXT,
        status TEXT DEFAULT 'completed',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()

    # Seed default data if empty
    c.execute("SELECT COUNT(*) FROM admin")
    if c.fetchone()[0] == 0:
        seed_data(conn)

    conn.close()

def seed_data(conn):
    c = conn.cursor()

    # Default admin: admin / jeecell2024
    c.execute("INSERT INTO admin (username, password_hash) VALUES (?, ?)",
              ('admin', generate_password_hash('jeecell2024')))

    # Default settings
    settings = {
        'store_name': 'Jee Cell',
        'tagline': 'Agen BRILink Terpercaya & Pusat Voucher, ATK, Jajanan',
        'whatsapp': '6282125955744',
        'address': 'Karangtengah, Jawa Barat',
        'open_hours': '07.00 - 22.00 WIB',
        'open_hour': '7',
        'close_hour': '22',
        'gmaps_embed': 'https://www.google.com/maps/search/agen+brilink+Jee+Cell+Karangtengah',
        'gmaps_link': 'https://www.google.com/maps/search/agen+brilink+Jee+Cell+Karangtengah',
        'about_text': 'Jee Cell adalah agen BRILink resmi yang melayani berbagai transaksi perbankan, penjualan voucher, alat tulis, jajanan, dan layanan cetak foto/print.',
    }
    for k, v in settings.items():
        c.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (k, v))

    # Categories
    categories = [
        ('BRILink', 'fas fa-university', 'Layanan perbankan BRI', 1),
        ('Pulsa & Data', 'fas fa-mobile-alt', 'Pulsa dan paket data semua operator', 2),
        ('Voucher Game', 'fas fa-gamepad', 'Voucher game online', 3),
        ('Token Listrik', 'fas fa-bolt', 'Token PLN prabayar', 4),
        ('Alat Tulis', 'fas fa-pencil-ruler', 'Buku, pulpen, dan ATK', 5),
        ('Jajanan & Minuman', 'fas fa-ice-cream', 'Snack, es, dan minuman', 6),
        ('Foto & Print', 'fas fa-camera', 'Cetak foto, print, fotokopi', 7),
    ]
    for name, icon, desc, order in categories:
        c.execute("INSERT INTO categories (name, icon, description, sort_order) VALUES (?,?,?,?)",
                  (name, icon, desc, order))

    # Sample products
    products = [
        # BRILink services
        ('Transfer Sesama BRI', 1, 0, 'Gratis', 'Transfer uang ke sesama rekening BRI', None, 999, 1, 1),
        ('Transfer Antar Bank', 1, 6500, 'Rp 6.500', 'Transfer ke bank lain (BCA, Mandiri, BNI, dll)', None, 999, 1, 1),
        ('Tarik Tunai', 1, 5000, 'Rp 5.000', 'Tarik tunai tanpa ke ATM', None, 999, 1, 1),
        ('Setor Tunai', 1, 0, 'Gratis', 'Setor tunai ke rekening BRI', None, 999, 1, 0),
        ('Pembayaran Tagihan', 1, 2500, 'Rp 2.500', 'Bayar listrik, air, BPJS, dll', None, 999, 1, 0),

        # Pulsa & Data
        ('Pulsa Telkomsel 5K', 2, 6000, 'Rp 6.000', 'Pulsa Telkomsel Rp 5.000', None, 50, 1, 0),
        ('Pulsa Telkomsel 10K', 2, 11000, 'Rp 11.000', 'Pulsa Telkomsel Rp 10.000', None, 50, 1, 0),
        ('Pulsa XL 5K', 2, 6000, 'Rp 6.000', 'Pulsa XL Rp 5.000', None, 50, 1, 0),
        ('Pulsa Indosat 10K', 2, 11000, 'Rp 11.000', 'Pulsa Indosat Rp 10.000', None, 50, 1, 0),
        ('Paket Data 1GB', 2, 10000, 'Rp 10.000', 'Paket data 1GB semua operator', None, 30, 1, 1),

        # Voucher Game
        ('Diamond ML 56', 3, 15000, 'Rp 15.000', '56 Diamond Mobile Legends', None, 100, 1, 1),
        ('Diamond ML 172', 3, 45000, 'Rp 45.000', '172 Diamond Mobile Legends', None, 100, 1, 0),
        ('Diamond FF 70', 3, 10000, 'Rp 10.000', '70 Diamond Free Fire', None, 100, 1, 0),
        ('UC PUBG 60', 3, 15000, 'Rp 15.000', '60 UC PUBG Mobile', None, 50, 1, 0),

        # Token Listrik
        ('Token PLN 20K', 4, 21000, 'Rp 21.000', 'Token listrik Rp 20.000', None, 30, 1, 0),
        ('Token PLN 50K', 4, 52000, 'Rp 52.000', 'Token listrik Rp 50.000', None, 30, 1, 0),
        ('Token PLN 100K', 4, 102000, 'Rp 102.000', 'Token listrik Rp 100.000', None, 20, 1, 0),

        # Alat Tulis
        ('Buku Tulis 38 Lbr', 5, 4000, 'Rp 4.000', 'Buku tulis 38 lembar', None, 100, 1, 0),
        ('Pulpen Standar', 5, 2500, 'Rp 2.500', 'Pulpen tinta hitam/biru', None, 200, 1, 0),
        ('Pensil 2B', 5, 3000, 'Rp 3.000', 'Pensil 2B untuk ujian', None, 100, 1, 0),
        ('Penghapus', 5, 2000, 'Rp 2.000', 'Penghapus karet', None, 150, 1, 0),
        ('Paket Sekolah', 5, 15000, 'Rp 15.000', 'Buku + pulpen + pensil + penghapus', None, 50, 1, 1),

        # Jajanan & Minuman
        ('Es Teh Manis', 6, 3000, 'Rp 3.000', 'Es teh manis segar', None, 999, 1, 0),
        ('Es Jeruk', 6, 4000, 'Rp 4.000', 'Es jeruk peras segar', None, 999, 1, 0),
        ('Kopi Sachet', 6, 3000, 'Rp 3.000', 'Kopi instan (Good Day, Kapal Api, dll)', None, 50, 1, 0),
        ('Chitato', 6, 8000, 'Rp 8.000', 'Chitato rasa original/sapi panggang', None, 30, 1, 0),
        ('Indomie Goreng', 6, 4000, 'Rp 4.000', 'Indomie goreng + telur', None, 50, 1, 1),
        ('Roti Coklat', 6, 5000, 'Rp 5.000', 'Roti isi coklat', None, 30, 1, 0),

        # Foto & Print
        ('Print Hitam Putih', 7, 1000, 'Rp 1.000/lembar', 'Print dokumen hitam putih', None, 999, 1, 0),
        ('Print Warna', 7, 2500, 'Rp 2.500/lembar', 'Print dokumen berwarna', None, 999, 1, 0),
        ('Cetak Foto 4R', 7, 3000, 'Rp 3.000/lembar', 'Cetak foto ukuran 4R', None, 999, 1, 0),
        ('Cetak Foto 3x4', 7, 2000, 'Rp 2.000/lembar', 'Cetak foto ukuran 3x4 (6 lembar)', None, 999, 1, 0),
        ('Fotokopi', 7, 500, 'Rp 500/lembar', 'Fotokopi hitam putih', None, 999, 1, 0),
        ('Scan Dokumen', 7, 2000, 'Rp 2.000', 'Scan dokumen ke PDF/JPG', None, 999, 1, 0),
    ]
    for p in products:
        c.execute('''INSERT INTO products (name, category_id, price, price_label, description, image_url, stock, is_active, is_featured)
                     VALUES (?,?,?,?,?,?,?,?,?)''', p)

    # Sample announcements
    announcements = [
        ('Promo Transfer!', 'Transfer antar bank cuma Rp 5.000 (hemat Rp 1.500)! Berlaku setiap hari.', 'fas fa-tag', 1, 1),
        ('Es Teh Rp 2.000', 'Promo es teh manis Rp 2.000 setiap jam 13.00-15.00!', 'fas fa-glass-whiskey', 1, 2),
    ]
    for a in announcements:
        c.execute("INSERT INTO announcements (title, content, icon, is_active, sort_order) VALUES (?,?,?,?,?)", a)

    conn.commit()


# === Helper functions ===

def get_setting(key, default=None):
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row['value'] if row else default

def set_setting(key, value):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def get_all_settings():
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {r['key']: r['value'] for r in rows}

def get_categories(active_only=True):
    conn = get_db()
    q = "SELECT * FROM categories"
    if active_only:
        q += " WHERE is_active=1"
    q += " ORDER BY sort_order"
    rows = conn.execute(q).fetchall()
    conn.close()
    return rows

def get_products(category_id=None, active_only=True, featured_only=False):
    conn = get_db()
    q = "SELECT p.*, c.name as category_name, c.icon as category_icon FROM products p LEFT JOIN categories c ON p.category_id=c.id WHERE 1=1"
    params = []
    if active_only:
        q += " AND p.is_active=1"
    if category_id:
        q += " AND p.category_id=?"
        params.append(category_id)
    if featured_only:
        q += " AND p.is_featured=1"
    q += " ORDER BY p.category_id, p.id"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return rows

def get_product(product_id):
    conn = get_db()
    row = conn.execute("SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id=c.id WHERE p.id=?", (product_id,)).fetchone()
    conn.close()
    return row

def add_product(name, category_id, price, price_label, description, image_url, stock, is_active, is_featured):
    conn = get_db()
    conn.execute('''INSERT INTO products (name, category_id, price, price_label, description, image_url, stock, is_active, is_featured)
                    VALUES (?,?,?,?,?,?,?,?,?)''',
                 (name, category_id, price, price_label, description, image_url, stock, is_active, is_featured))
    conn.commit()
    conn.close()

def update_product(product_id, name, category_id, price, price_label, description, image_url, stock, is_active, is_featured):
    conn = get_db()
    conn.execute('''UPDATE products SET name=?, category_id=?, price=?, price_label=?, description=?, image_url=?, stock=?, is_active=?, is_featured=?
                    WHERE id=?''',
                 (name, category_id, price, price_label, description, image_url, stock, is_active, is_featured, product_id))
    conn.commit()
    conn.close()

def delete_product(product_id):
    conn = get_db()
    conn.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()

def get_announcements(active_only=True):
    conn = get_db()
    q = "SELECT * FROM announcements"
    if active_only:
        q += " WHERE is_active=1"
    q += " ORDER BY sort_order"
    rows = conn.execute(q).fetchall()
    conn.close()
    return rows

def verify_admin(username, password):
    conn = get_db()
    row = conn.execute("SELECT * FROM admin WHERE username=?", (username,)).fetchone()
    conn.close()
    if row and check_password_hash(row['password_hash'], password):
        return dict(row)
    return None

def get_product_count():
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM products WHERE is_active=1").fetchone()[0]
    conn.close()
    return count

def get_category_count():
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM categories WHERE is_active=1").fetchone()[0]
    conn.close()
    return count
