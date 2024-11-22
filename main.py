from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
import bcrypt

app = Flask(__name__)
app.secret_key = 'quy_huy'

DATABASE = 'products.db'

# Hàm để kết nối với cơ sở dữ liệu
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Để có thể truy cập các cột bằng tên
    return conn

# Hàm để tạo bảng users và products nếu chưa tồn tại
def init_db():
    if not os.path.exists(DATABASE):
        with get_db() as conn:
            # Tạo bảng users (email là khóa chính)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL
                )
            ''')
            # Tạo bảng products
            conn.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sr INTEGER,
                    name TEXT,
                    price REAL,
                    discount TEXT,
                    count TEXT,
                    brand TEXT,
                    image TEXT
                )
            ''')
            conn.commit()

# Khởi tạo cơ sở dữ liệu
init_db()

def get_all_products():
    with get_db() as conn:
        cur = conn.execute('SELECT * FROM products')
        return cur.fetchall()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Kiểm tra thông tin đăng nhập
        with get_db() as conn:
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
                # Lưu thông tin vào session
                session['user_id'] = user['email']
                return redirect(url_for('home'))
            else:
                flash("Invalid email or password.", "login")
                return redirect(url_for('login'))
    return render_template('login.html') 


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Kiểm tra nếu email đã tồn tại trong cơ sở dữ liệu
        with get_db() as conn:
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if user:
                flash("Email is already taken. Please choose another one.")
                return redirect(url_for('register'))

            # Mã hóa mật khẩu
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            conn.execute("INSERT INTO users (email, username, password) VALUES (?, ?, ?)", (email, username, hashed_password))
            conn.commit()
        flash("Registration successful! You can now log in.")
        return redirect(url_for('login'))   

    return render_template('register.html')


@app.route('/', methods=['GET', 'POST'])
def home():
    if 'user_id' not in session:  # Kiểm tra nếu người dùng chưa đăng nhập
        return redirect(url_for('login'))
    
    user_email = session['user_id']
    with get_db() as conn:
        user = conn.execute("SELECT username FROM users WHERE email = ?", (user_email,)).fetchone()
        username = user['username'] if user else "User"
    
    products = get_all_products()
    return render_template('home.html', username=username, products=products)

@app.route('/smartphone')
def smartphone():
    products = get_all_products()
    return render_template('smartphone.html', products=products)

@app.route('/productmanagement')
def productmanagement():        
    products = get_all_products()
    return render_template('productmanagement.html', products=products)

@app.route('/productmanagement/addproduct', methods=['GET', 'POST'])
def addproduct():
    if request.method == 'POST':
        sr = request.form['sr']
        name = request.form['name']
        price = request.form['price']
        discount = request.form['discount']
        count = request.form['count']
        brand = request.form['brand']
        image = request.form['image']
        
        # Thêm sản phẩm vào cơ sở dữ liệu
        with get_db() as conn:
            conn.execute('''
                INSERT INTO products (sr, name, price, discount, count, brand, image)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (sr, name, price, discount, count, brand, image))
            conn.commit()

        return redirect(url_for('productmanagement'))

    return render_template('addproduct.html')

@app.route('/productmanagement/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    with get_db() as conn:
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        
    if request.method == 'POST':
        sr = request.form['sr']
        name = request.form['name']
        price = request.form['price']
        discount = request.form['discount']
        count = request.form['count']
        brand = request.form['brand']
        image = request.form['image']
        
        with get_db() as conn:
            conn.execute('''
                UPDATE products SET sr = ?, name = ?, price = ?, discount = ?, count = ?, brand = ?, image = ?
                WHERE id = ?
            ''', (sr, name, price, discount, count, brand, image, product_id))
            conn.commit()
        
        flash("Product updated successfully!", "productmanagement")
        return redirect(url_for('productmanagement'))
    
    return render_template('edit_product.html', product=product)

@app.route('/productmanagement/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    with get_db() as conn:
        conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
        conn.commit()
    flash("Product deleted successfully!")
    return redirect(url_for('productmanagement'))


@app.route('/myaccount', methods=['GET', 'POST'])
def myaccount():
    user_email = session.get('user_id')
    if not user_email:
        return redirect(url_for('login'))

    # Lấy thông tin người dùng từ cơ sở dữ liệu
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (user_email,)).fetchone()

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Cập nhật thông tin người dùng
        with get_db() as conn:
            if email:
                conn.execute("UPDATE users SET email = ? WHERE email = ?", (email, user_email))
            if password:
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                conn.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_password, user_email))
            conn.commit()
        
        flash("Information updated successfully!", "myaccount")
        return redirect(url_for('myaccount'))

    return render_template('myaccount.html', user=user)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)