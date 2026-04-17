from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "inventory-secret-2024")

def get_db():
    return mysql.connector.connect(
        host=os.environ.get("MYSQL_HOST", "mysql"),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ.get("MYSQL_PASSWORD", "root"),
        database=os.environ.get("MYSQL_DB", "inventory")
    )

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            category_id INT,
            quantity INT DEFAULT 0,
            threshold INT DEFAULT 10,
            price DECIMAL(10,2) DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT,
            change_amount INT NOT NULL,
            reason VARCHAR(100),
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        )
    """)
    # Seed categories
    for cat in ["Electronics", "Clothing", "Food & Beverage", "Furniture", "Stationery"]:
        cursor.execute("INSERT IGNORE INTO categories (name) VALUES (%s)", (cat,))
    conn.commit()
    cursor.close()
    conn.close()

@app.before_request
def setup():
    try:
        init_db()
    except Exception:
        pass

# ── Dashboard ────────────────────────────────────────────────
@app.route("/")
def dashboard():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM products")
    total_products = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS low FROM products WHERE quantity < threshold")
    low_stock_count = cursor.fetchone()["low"]

    cursor.execute("SELECT SUM(quantity * price) AS value FROM products")
    total_value = cursor.fetchone()["value"] or 0

    cursor.execute("""
        SELECT sl.*, p.name AS product_name
        FROM stock_logs sl
        JOIN products p ON sl.product_id = p.id
        ORDER BY sl.logged_at DESC LIMIT 8
    """)
    recent_logs = cursor.fetchall()

    cursor.execute("""
        SELECT p.*, c.name AS category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.quantity < p.threshold
        ORDER BY p.quantity ASC LIMIT 5
    """)
    low_stock_items = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template("dashboard.html",
        total_products=total_products,
        low_stock_count=low_stock_count,
        total_value=round(total_value, 2),
        recent_logs=recent_logs,
        low_stock_items=low_stock_items
    )

# ── Products ─────────────────────────────────────────────────
@app.route("/products")
def products():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    category_filter = request.args.get("category", "")
    search = request.args.get("search", "")

    query = """
        SELECT p.*, c.name AS category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE 1=1
    """
    params = []
    if category_filter:
        query += " AND c.name = %s"
        params.append(category_filter)
    if search:
        query += " AND p.name LIKE %s"
        params.append(f"%{search}%")
    query += " ORDER BY p.created_at DESC"

    cursor.execute(query, params)
    products_list = cursor.fetchall()

    cursor.execute("SELECT * FROM categories ORDER BY name")
    categories = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template("products.html",
        products=products_list,
        categories=categories,
        selected_category=category_filter,
        search=search
    )

@app.route("/products/add", methods=["GET", "POST"])
def add_product():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    if request.method == "POST":
        name = request.form["name"]
        category_id = request.form["category_id"]
        quantity = int(request.form["quantity"])
        threshold = int(request.form["threshold"])
        price = float(request.form["price"])
        cursor.execute("""
            INSERT INTO products (name, category_id, quantity, threshold, price)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, category_id, quantity, threshold, price))
        product_id = cursor.lastrowid
        if quantity > 0:
            cursor.execute("""
                INSERT INTO stock_logs (product_id, change_amount, reason)
                VALUES (%s, %s, %s)
            """, (product_id, quantity, "Initial stock"))
        conn.commit()
        flash(f'Product "{name}" added successfully!', "success")
        cursor.close()
        conn.close()
        return redirect(url_for("products"))
    cursor.execute("SELECT * FROM categories ORDER BY name")
    categories = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("add_product.html", categories=categories)

@app.route("/products/<int:id>/edit", methods=["GET", "POST"])
def edit_product(id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    if request.method == "POST":
        name = request.form["name"]
        category_id = request.form["category_id"]
        threshold = int(request.form["threshold"])
        price = float(request.form["price"])
        cursor.execute("""
            UPDATE products SET name=%s, category_id=%s, threshold=%s, price=%s
            WHERE id=%s
        """, (name, category_id, threshold, price, id))
        conn.commit()
        flash("Product updated.", "success")
        cursor.close()
        conn.close()
        return redirect(url_for("products"))
    cursor.execute("SELECT * FROM products WHERE id=%s", (id,))
    product = cursor.fetchone()
    cursor.execute("SELECT * FROM categories ORDER BY name")
    categories = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("edit_product.html", product=product, categories=categories)

@app.route("/products/<int:id>/delete", methods=["POST"])
def delete_product(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=%s", (id,))
    conn.commit()
    flash("Product deleted.", "info")
    cursor.close()
    conn.close()
    return redirect(url_for("products"))

@app.route("/products/<int:id>/stock", methods=["POST"])
def update_stock(id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    change = int(request.form["change"])
    reason = request.form.get("reason", "Manual update")
    cursor.execute("UPDATE products SET quantity = quantity + %s WHERE id=%s", (change, id))
    cursor.execute("""
        INSERT INTO stock_logs (product_id, change_amount, reason)
        VALUES (%s, %s, %s)
    """, (id, change, reason))
    conn.commit()
    cursor.execute("SELECT name FROM products WHERE id=%s", (id,))
    p = cursor.fetchone()
    action = "restocked" if change > 0 else "reduced"
    flash(f'"{p["name"]}" stock {action} by {abs(change)}.', "success")
    cursor.close()
    conn.close()
    return redirect(url_for("products"))

# ── Low Stock ─────────────────────────────────────────────────
@app.route("/low-stock")
def low_stock():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, c.name AS category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.quantity < p.threshold
        ORDER BY p.quantity ASC
    """)
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("low_stock.html", items=items)

# ── Health check ──────────────────────────────────────────────
@app.route("/health")
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
