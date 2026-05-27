from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from database import *
import os

app = Flask(__name__)
app.secret_key = 'jeecell-secret-key-2024-brilink'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB upload limit

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
    if cat_id:
        products = get_products(category_id=cat_id)
        active_cat = cat_id
    else:
        products = get_products()
        active_cat = None
    return render_template('products.html',
                           settings=settings,
                           categories=categories,
                           products=products,
                           active_cat=active_cat)

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
    return render_template('admin/dashboard.html',
                           settings=settings,
                           product_count=pcount,
                           category_count=ccount,
                           announcements=announcements,
                           categories=categories)

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
@app.route('/api/products')
def api_products():
    products = get_products()
    return jsonify([dict(p) for p in products])

@app.route('/api/products/featured')
def api_featured():
    products = get_products(featured_only=True)
    return jsonify([dict(p) for p in products])

# === Init & Run ===
if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=5000)
