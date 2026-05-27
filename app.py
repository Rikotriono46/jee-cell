from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_wtf.csrf import CSRFProtect
from functools import wraps
from database import *
from datetime import datetime
import os
import urllib.parse

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB upload limit
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

# CSRF Protection
csrf = CSRFProtect(app)

# WhatsApp order link filter
def wa_order_link(product_name, price_label, wa_number):
    text = f'Halo, saya mau pesan {product_name} seharga {price_label}. Masih tersedia?'
    return f'https://wa.me/{wa_number}?text={urllib.parse.quote(text)}'

app.jinja_env.filters['wa_order'] = wa_order_link

# === Auth decorator ===
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# === Main routes ===
@app.route('/')
def index():
    settings = get_all_settings()
    categories = get_categories()
    featured_products = get_products(featured_only=True)
    all_products = get_products()
    announcements = get_announcements()

    # Group products by category
    products_by_cat = {}
    for cat in categories:
        cat_products = [p for p in all_products if p['category_id'] == cat['id']]
        if cat_products:
            products_by_cat[cat['name']] = {
                'icon': cat['icon'],
                'description': cat['description'],
                'products': cat_products
            }

    return render_template('index.html',
                           settings=settings,
                           categories=categories,
                           featured=featured_products,
                           products_by_cat=products_by_cat,
                           announcements=announcements)

@app.route('/produk')
def products_page():
    settings = get_all_settings()
    categories = get_categories()
    cat_id = request.args.get('category', type=int)
    search_query = request.args.get('q', '').strip()
    if search_query:
        products = search_products(search_query)
        active_cat = None
    elif cat_id:
        products = get_products(category_id=cat_id)
        active_cat = cat_id
    else:
        products = get_products()
        active_cat = None
    return render_template('products.html',
                           settings=settings,
                           categories=categories,
                           products=products,
                           active_cat=active_cat,
                           search_query=search_query)

@app.route('/produk/<int:product_id>')
def product_detail(product_id):
    settings = get_all_settings()
    product = get_product(product_id)
    if not product:
        return redirect(url_for('products_page'))
    return render_template('product_detail.html',
                           settings=settings,
                           product=product)

# === Admin routes ===
@app.route('/admin')
def admin_redirect():
    return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = verify_admin(username, password)
        if user:
            session['admin_logged_in'] = True
            session['admin_user'] = username
            flash('Login berhasil!', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Username atau password salah!', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Logout berhasil.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    settings = get_all_settings()
    pcount = get_product_count()
    ccount = get_category_count()
    announcements = get_announcements(active_only=False)
    categories = get_categories(active_only=False)
    sales_today = get_total_sales_today()
    transaction_count_today = get_transaction_count_today()
    recent_transactions = get_recent_transactions(limit=5)
    sales_weekly = get_sales_summary(days=7)
    return render_template('admin/dashboard.html',
                           settings=settings,
                           product_count=pcount,
                           category_count=ccount,
                           announcements=announcements,
                           categories=categories,
                           sales_today=sales_today,
                           transaction_count_today=transaction_count_today,
                           recent_transactions=recent_transactions,
                           sales_weekly=sales_weekly)

# === Products CRUD ===
@app.route('/admin/products')
@admin_required
def admin_products():
    products = get_products(active_only=False)
    categories = get_categories(active_only=False)
    return render_template('admin/products.html', products=products, categories=categories)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def admin_product_add():
    categories = get_categories(active_only=False)
    if request.method == 'POST':
        add_product(
            name=request.form['name'],
            category_id=int(request.form['category_id']),
            price=float(request.form.get('price', 0)),
            price_label=request.form.get('price_label', ''),
            description=request.form.get('description', ''),
            image_url=request.form.get('image_url', ''),
            stock=int(request.form.get('stock', 0)),
            is_active=1 if request.form.get('is_active') else 0,
            is_featured=1 if request.form.get('is_featured') else 0,
        )
        flash('Produk berhasil ditambahkan!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/product_form.html', categories=categories, product=None, action='add')

@app.route('/admin/products/edit/<int:pid>', methods=['GET', 'POST'])
@admin_required
def admin_product_edit(pid):
    product = get_product(pid)
    if not product:
        flash('Produk tidak ditemukan!', 'error')
        return redirect(url_for('admin_products'))
    categories = get_categories(active_only=False)
    if request.method == 'POST':
        update_product(
            product_id=pid,
            name=request.form['name'],
            category_id=int(request.form['category_id']),
            price=float(request.form.get('price', 0)),
            price_label=request.form.get('price_label', ''),
            description=request.form.get('description', ''),
            image_url=request.form.get('image_url', ''),
            stock=int(request.form.get('stock', 0)),
            is_active=1 if request.form.get('is_active') else 0,
            is_featured=1 if request.form.get('is_featured') else 0,
        )
        flash('Produk berhasil diupdate!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/product_form.html', categories=categories, product=product, action='edit')

@app.route('/admin/products/delete/<int:pid>', methods=['POST'])
@admin_required
def admin_product_delete(pid):
    delete_product(pid)
    flash('Produk berhasil dihapus!', 'success')
    return redirect(url_for('admin_products'))

# === Announcements CRUD ===
@app.route('/admin/announcements/add', methods=['POST'])
@admin_required
def admin_announcement_add():
    conn = get_db()
    conn.execute('''INSERT INTO announcements (title, content, icon, is_active, sort_order) VALUES (?,?,?,?,?)''',
                 (request.form['title'], request.form.get('content', ''), request.form.get('icon', 'fas fa-bullhorn'),
                  1 if request.form.get('is_active') else 0, int(request.form.get('sort_order', 0))))
    conn.commit()
    conn.close()
    flash('Pengumuman berhasil ditambahkan!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/announcements/delete/<int:aid>', methods=['POST'])
@admin_required
def admin_announcement_delete(aid):
    conn = get_db()
    conn.execute("DELETE FROM announcements WHERE id=?", (aid,))
    conn.commit()
    conn.close()
    flash('Pengumuman dihapus!', 'success')
    return redirect(url_for('admin_dashboard'))

# === Settings ===
@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    if request.method == 'POST':
        for key in request.form:
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                set_setting(setting_key, request.form[key])
        flash('Pengaturan berhasil disimpan!', 'success')
        return redirect(url_for('admin_settings'))
    settings = get_all_settings()
    return render_template('admin/settings.html', settings=settings)

# === Category CRUD ===
@app.route('/admin/categories/add', methods=['POST'])
@admin_required
def admin_category_add():
    conn = get_db()
    conn.execute('''INSERT INTO categories (name, icon, description, sort_order, is_active) VALUES (?,?,?,?,?)''',
                 (request.form['name'], request.form.get('icon', 'fas fa-box'),
                  request.form.get('description', ''), int(request.form.get('sort_order', 0)),
                  1 if request.form.get('is_active') else 0))
    conn.commit()
    conn.close()
    flash('Kategori berhasil ditambahkan!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/categories/delete/<int:cid>', methods=['POST'])
@admin_required
def admin_category_delete(cid):
    conn = get_db()
    conn.execute("DELETE FROM categories WHERE id=?", (cid,))
    conn.commit()
    conn.close()
    flash('Kategori dihapus!', 'success')
    return redirect(url_for('admin_dashboard'))

# === API for AJAX ===

# === Transactions ===
@app.route('/admin/transactions')
@admin_required
def admin_transactions():
    transactions = get_recent_transactions(limit=100)
    sales_today = get_total_sales_today()
    transaction_count_today = get_transaction_count_today()
    return render_template('admin/transactions.html',
                           transactions=transactions,
                           sales_today=sales_today,
                           transaction_count_today=transaction_count_today)

@app.route('/admin/transactions/add', methods=['POST'])
@admin_required
def admin_transaction_add():
    add_transaction(
        type=request.form['type'],
        description=request.form.get('description', ''),
        amount=float(request.form.get('amount', 0)),
        customer_name=request.form.get('customer_name', ''),
        customer_phone=request.form.get('customer_phone', ''),
        notes=request.form.get('notes', ''),
        status=request.form.get('status', 'completed'),
    )
    flash('Transaksi berhasil ditambahkan!', 'success')
    return redirect(url_for('admin_transactions'))
@app.route('/admin/transactions/<int:tid>/invoice')
@admin_required
def admin_transaction_invoice(tid):
    transaction = get_transaction(tid)
    if not transaction:
        flash('Transaksi tidak ditemukan!', 'error')
        return redirect(url_for('admin_transactions'))
    settings = get_all_settings()
    return render_template('admin/invoice.html',
                           transaction=transaction,
                           settings=settings)

# === Tabungan / Savings ===
@app.route('/admin/savings')
@admin_required
def admin_savings():
    search = request.args.get('q', '').strip()
    if search:
        customers = search_savings_customers(search)
    else:
        customers = get_savings_customers()
    total_savings = get_savings_total()
    return render_template('admin/savings.html',
                           customers=customers,
                           total_savings=total_savings,
                           search=search)

@app.route('/admin/savings/add', methods=['POST'])
@admin_required
def admin_savings_add():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Nama nasabah wajib diisi!', 'error')
        return redirect(url_for('admin_savings'))
    cid = add_savings_customer(
        name=name,
        phone=request.form.get('phone', ''),
        address=request.form.get('address', ''),
        notes=request.form.get('notes', ''),
    )
    flash(f'Nasabah "{name}" berhasil ditambahkan!', 'success')
    return redirect(url_for('admin_savings_detail', cid=cid))

@app.route('/admin/savings/<int:cid>')
@admin_required
def admin_savings_detail(cid):
    customer = get_savings_customer(cid)
    if not customer:
        flash('Nasabah tidak ditemukan!', 'error')
        return redirect(url_for('admin_savings'))
    transactions = get_savings_transactions(cid)
    return render_template('admin/savings_detail.html',
                           customer=customer,
                           transactions=transactions)

@app.route('/admin/savings/<int:cid>/edit', methods=['POST'])
@admin_required
def admin_savings_edit(cid):
    customer = get_savings_customer(cid)
    if not customer:
        flash('Nasabah tidak ditemukan!', 'error')
        return redirect(url_for('admin_savings'))
    update_savings_customer(
        customer_id=cid,
        name=request.form.get('name', customer['name']).strip() or customer['name'],
        phone=request.form.get('phone', ''),
        address=request.form.get('address', ''),
        notes=request.form.get('notes', ''),
    )
    flash('Data nasabah berhasil diupdate!', 'success')
    return redirect(url_for('admin_savings_detail', cid=cid))

@app.route('/admin/savings/<int:cid>/delete', methods=['POST'])
@admin_required
def admin_savings_delete(cid):
    delete_savings_customer(cid)
    flash('Nasabah berhasil dihapus!', 'success')
    return redirect(url_for('admin_savings'))

@app.route('/admin/savings/<int:cid>/transaction', methods=['POST'])
@admin_required
def admin_savings_transaction(cid):
    customer = get_savings_customer(cid)
    if not customer:
        flash('Nasabah tidak ditemukan!', 'error')
        return redirect(url_for('admin_savings'))
    trans_type = request.form.get('type', 'deposit')
    amount = float(request.form.get('amount', 0))
    if amount <= 0:
        flash('Jumlah harus lebih dari 0!', 'error')
        return redirect(url_for('admin_savings_detail', cid=cid))
    tx_id, error = add_savings_transaction(
        customer_id=cid,
        trans_type=trans_type,
        amount=amount,
        notes=request.form.get('notes', ''),
    )
    if error:
        flash(error, 'error')
    else:
        label = 'Setor tunai' if trans_type == 'deposit' else 'Penarikan'
        flash(f'{label} Rp {amount:,.0f} berhasil!', 'success')
    return redirect(url_for('admin_savings_detail', cid=cid))

@app.route('/admin/savings/<int:cid>/receipt')
@admin_required
def admin_savings_receipt(cid):
    customer = get_savings_customer(cid)
    if not customer:
        flash('Nasabah tidak ditemukan!', 'error')
        return redirect(url_for('admin_savings'))
    date_from = request.args.get('from', '')
    date_to = request.args.get('to', '')
    if not date_from:
        date_from = datetime.now().strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.now().strftime('%Y-%m-%d')
    transactions = get_savings_transactions_range(cid, date_from, date_to)
    settings = get_all_settings()
    return render_template('admin/savings_receipt.html',
                           customer=customer,
                           transactions=transactions,
                           date_from=date_from,
                           date_to=date_to,
                           settings=settings,
                           now=datetime.now())

@app.route('/admin/savings/<int:cid>/receipt/<int:tx_id>')
@admin_required
def admin_savings_receipt_single(cid, tx_id):
    customer = get_savings_customer(cid)
    if not customer:
        flash('Nasabah tidak ditemukan!', 'error')
        return redirect(url_for('admin_savings'))
    tx = get_savings_transaction(tx_id)
    if not tx:
        flash('Transaksi tidak ditemukan!', 'error')
        return redirect(url_for('admin_savings_detail', cid=cid))
    settings = get_all_settings()
    return render_template('admin/savings_receipt.html',
                           customer=customer,
                           transactions=[tx],
                           date_from=tx['created_at'][:10] if tx['created_at'] else '',
                           date_to=tx['created_at'][:10] if tx['created_at'] else '',
                           settings=settings,
                           single_receipt=True,
                           now=datetime.now())

# === API for AJAX ===
@app.route('/api/search')
@csrf.exempt
def api_search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    results = search_products(q)
    return jsonify([dict(p) for p in results])


@csrf.exempt
@app.route('/api/sales/today')
def api_sales_today():
    return jsonify({
        'total': get_total_sales_today(),
        'count': get_transaction_count_today(),
        'transactions': [dict(t) for t in get_transactions_today()]
    })

@csrf.exempt
@app.route('/api/sales/weekly')
def api_sales_weekly():
    summary = get_sales_summary(days=7)
    return jsonify([dict(row) for row in summary])

@csrf.exempt
@app.route('/api/products')
def api_products():
    products = get_products()
    return jsonify([dict(p) for p in products])

@csrf.exempt
@app.route('/api/products/featured')
def api_featured():
    products = get_products(featured_only=True)
    return jsonify([dict(p) for p in products])

# === Init DB on startup ===
init_db()

# === Init & Run ===
if __name__ == '__main__':
    import socket

    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    port = int(os.environ.get('PORT', 5000))

    print()
    print("=" * 45)
    print("   🏪  Jee Cell - Agen BRILink")
    print("=" * 45)
    print()
    print("  Pilih mode menjalankan server:")
    print()
    print("  [1] Localhost (hanya PC ini)")
    print("      → http://127.0.0.1:{}".format(port))
    print()
    print("  [2] Network (satu WiFi bisa akses)")
    local_ip = get_local_ip()
    print("      → http://{}:{}".format(local_ip, port))
    print()

    while True:
        choice = input("  Pilih (1/2): ").strip()
        if choice == '1':
            host = '127.0.0.1'
            print(f"\n  ✅ Server berjalan di http://127.0.0.1:{port}")
            print(f"  🔐 Admin: http://127.0.0.1:{port}/admin/login")
            break
        elif choice == '2':
            host = '0.0.0.0'
            print(f"\n  ✅ Server berjalan di http://{local_ip}:{port}")
            print(f"  📱 Dari HP/device: http://{local_ip}:{port}")
            print(f"  🔐 Admin: http://{local_ip}:{port}/admin/login")
            break
        else:
            print("  ⚠️  Pilih 1 atau 2!")

    print("  Tekan Ctrl+C untuk berhenti")
    print("=" * 45)
    print()

    app.run(debug=False, host=host, port=port)
