from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

app = Flask(__name__)
app.secret_key = "super_secret_campus_key" 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///marketplace.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False) 

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    seller = db.Column(db.String(50), nullable=False)
    seller_rating = db.Column(db.Float, default=0.0)
    reviews = db.Column(db.Integer, default=0)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    condition = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date_added = db.Column(db.String(20), nullable=False)

with app.app_context():
    db.create_all()
    if not Product.query.first():
        starter_items = [
            Product(title="Funkadelic Maggot Brain Vinyl", seller="VinylCollector99", seller_rating=4.9, reviews=12, description="Classic funk rock album. Sleeve is in near-mint condition.", price=25.00, condition="Used - Good", category="Music", date_added="2026-03-10"),
            Product(title="Corsair 32GB DDR5 RAM", seller="HardwareSteve", seller_rating=5.0, reviews=54, description="Upgraded my rig recently, these work perfectly. Great for a new build.", price=80.00, condition="Like New", category="Electronics", date_added="2026-03-12"),
            Product(title="Python Toolchains & Refactoring", seller="GradStudentBob", seller_rating=3.8, reviews=4, description="Lightly used textbook. No highlighting on the pages.", price=45.00, condition="Used - Fair", category="Books", date_added="2026-03-14")
        ]
        db.session.bulk_save_objects(starter_items)
        db.session.commit()

# --- AUTHENTICATION ROUTES (Now at the root "/") ---

@app.route('/', methods=['GET', 'POST'])
def login():
    # If they are already logged in, send them straight to the marketplace
    if 'user_id' in session:
        return redirect(url_for('marketplace'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f"Welcome back, {user.username}!")
            return redirect(url_for('marketplace')) # Redirects to marketplace upon login
        else:
            flash("Invalid username or password.")
            
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if User.query.filter_by(username=username).first():
        flash("Username already exists. Please choose another.")
        return redirect(url_for('login'))
        
    hashed_pw = generate_password_hash(password)
    new_user = User(username=username, password_hash=hashed_pw)
    
    db.session.add(new_user)
    db.session.commit()
    
    session['user_id'] = new_user.id
    session['username'] = new_user.username
    flash("Account created successfully!")
    return redirect(url_for('marketplace'))

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('login'))

# --- MARKETPLACE ROUTE (Moved from "/") ---

@app.route('/marketplace')
def marketplace():
    # KICKER: Only logged in users can see the marketplace!
    if 'user_id' not in session:
        flash("Please log in to view the marketplace.")
        return redirect(url_for('login'))

    search_query = request.args.get('search', '').lower()
    condition_query = request.args.get('condition', 'All Conditions')
    category_query = request.args.get('category', 'All Categories')
    sort_query = request.args.get('sort', 'Newest First')
    
    products = Product.query.all()
    filtered_products = []
    
    for product in products:
        matches_search = search_query in product.title.lower() or search_query in product.description.lower() or search_query == ''
        matches_condition = condition_query == 'All Conditions' or condition_query == product.condition
        matches_category = category_query == 'All Categories' or category_query == product.category
        
        if matches_search and matches_condition and matches_category:
            filtered_products.append(product)

    if sort_query == 'Price: Low to High':
        filtered_products.sort(key=lambda x: x.price)
    elif sort_query == 'Price: High to Low':
        filtered_products.sort(key=lambda x: x.price, reverse=True)
    elif sort_query == 'Newest First':
        filtered_products.sort(key=lambda x: x.date_added, reverse=True)
    elif sort_query == 'Oldest First':
        filtered_products.sort(key=lambda x: x.date_added)

    recent_items = Product.query.order_by(Product.date_added.desc()).limit(3).all()
    # Now rendering marketplace.html instead of index.html
    return render_template('marketplace.html', products=filtered_products, recent_items=recent_items)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    product = Product.query.get_or_404(product_id)
    return render_template('product.html', product=product)

@app.route('/buy/<int:product_id>', methods=['POST'])
def buy_product(product_id):
    product = Product.query.get_or_404(product_id)
    flash(f"Success! You just 'purchased' {product.title} for ${product.price:.2f}")
    return redirect(url_for('marketplace'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        flash("Please log in to view your dashboard.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title')
        price = request.form.get('price')
        category = request.form.get('category')
        condition = request.form.get('condition')
        description = request.form.get('description')
        
        new_listing = Product(
            title=title,
            seller=session['username'],
            seller_rating=5.0,
            reviews=0,
            description=description,
            price=float(price),
            condition=condition,
            category=category,
            date_added=date.today().strftime("%Y-%m-%d")
        )
        
        db.session.add(new_listing)
        db.session.commit()
        flash(f"Successfully listed: {title}!")
        return redirect(url_for('dashboard'))

    recent_items = Product.query.order_by(Product.date_added.desc()).limit(3).all()
    my_active_listings = Product.query.filter_by(seller=session['username']).all()

    return render_template('dashboard.html', my_listings=my_active_listings, recent_items=recent_items)

if __name__ == '__main__':
    app.run(debug=True)