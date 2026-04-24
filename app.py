import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import date

app = Flask(__name__)
app.secret_key = "super_secret_campus_key" 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///marketplace_v3.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- NEW: Image Upload Configuration ---
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # Restrict uploads to 16MB max
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
    image_filename = db.Column(db.String(255), nullable=True, default='default.png')
    
    # --- NEW COLUMNS FOR EARNINGS & PROFILES ---
    is_sold = db.Column(db.Boolean, default=False)
    buyer_username = db.Column(db.String(50), nullable=True)

# Initialize the database and ensure the upload folder exists
with app.app_context():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    db.create_all()
    
    # Create dummy PowerSeller if it doesn't exist
    if not User.query.filter_by(username="PowerSeller").first():
        hashed_pw = generate_password_hash("password123") # Password is password123
        power_user = User(username="PowerSeller", password_hash=hashed_pw)
        db.session.add(power_user)
        db.session.commit() # Commit user first to get an ID just in case
        
        # Add a bunch of sold dummy data for the chart
        dummy_data = [
            Product(title="Funkadelic Maggot Brain Vinyl", seller="PowerSeller", description="Classic funk rock album.", price=25.00, condition="Used - Good", category="Music", date_added="2026-01-10", image_filename="vinyl.png", is_sold=True, buyer_username="StudentA"),
            Product(title="Beats Studio Pro", seller="PowerSeller", description="Noise cancelling headphones.", price=150.00, condition="Like New", category="Music", date_added="2026-02-15", image_filename="default.png", is_sold=True, buyer_username="StudentB"),
            Product(title="Corsair 32GB DDR5 RAM", seller="PowerSeller", description="Upgraded my rig.", price=80.00, condition="Like New", category="Electronics", date_added="2026-03-12", image_filename="ram.jpg", is_sold=True, buyer_username="StudentC"),
            Product(title="Calculus Early Transcendentals", seller="PowerSeller", description="Math book.", price=45.00, condition="Used - Fair", category="Books", date_added="2026-03-20", image_filename="default.png", is_sold=True, buyer_username="StudentD"),
            Product(title="Python Crash Course", seller="PowerSeller", description="Programming book.", price=30.00, condition="Used - Good", category="Books", date_added="2026-04-01", image_filename="default.png", is_sold=True, buyer_username="StudentE"),
            # Add one unsold item just to have it
            Product(title="Nintendo Switch OLED", seller="PowerSeller", description="Comes with dock.", price=220.00, condition="Like New", category="Electronics", date_added="2026-04-20", image_filename="switch.jpg", is_sold=False)
        ]
        db.session.bulk_save_objects(dummy_data)
        db.session.commit()



# --- AUTHENTICATION ROUTES ---
@app.route('/', methods=['GET', 'POST'])
def login():
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
            return redirect(url_for('marketplace'))
        else:
            flash("Invalid username or password.")
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('marketplace'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if password != confirm_password:
            flash("Passwords do not match. Please try again.")
            return redirect(url_for('signup'))
        if User.query.filter_by(username=username).first():
            flash("Username already exists. Please choose another.")
            return redirect(url_for('signup'))
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        session['user_id'] = new_user.id
        session['username'] = new_user.username
        flash("Account created successfully!")
        return redirect(url_for('marketplace'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('login'))

# --- MARKETPLACE ROUTES ---
@app.route('/marketplace')
def marketplace():
    if 'user_id' not in session:
        flash("Please log in to view the marketplace.")
        return redirect(url_for('login'))
    search_query = request.args.get('search', '').lower()
    condition_query = request.args.get('condition', 'All Conditions')
    category_query = request.args.get('category', 'All Categories')
    sort_query = request.args.get('sort', 'Newest First')
    
    # Only show items that haven't been sold yet
    products = Product.query.filter_by(is_sold=False).all()
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
    return render_template('marketplace.html', products=filtered_products, recent_items=recent_items)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    product = Product.query.get_or_404(product_id)
    return render_template('product.html', product=product)

# --- NEW: UPDATED DASHBOARD ROUTE ---
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
        
        file = request.files.get('image_file')
        filename = 'default.png' 
        
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        new_listing = Product(
            title=title,
            seller=session['username'],
            seller_rating=5.0,
            reviews=0,
            description=description,
            price=float(price),
            condition=condition,
            category=category,
            date_added=date.today().strftime("%Y-%m-%d"),
            image_filename=filename,
            is_sold=False 
        )
        
        db.session.add(new_listing)
        db.session.commit()
        flash(f"Successfully listed: {title}!")
        return redirect(url_for('dashboard'))

    recent_items = Product.query.filter_by(is_sold=False).order_by(Product.date_added.desc()).limit(3).all()
    my_active_listings = Product.query.filter_by(seller=session['username'], is_sold=False).all()
    my_sold_listings = Product.query.filter_by(seller=session['username'], is_sold=True).all()
    total_earnings = sum(item.price for item in my_sold_listings)

    # --- CALCULATE CHART DATA (Revenue Over Time) ---
    # Sort sold items by date so the graph flows left to right
    sorted_sales = sorted(my_sold_listings, key=lambda x: x.date_added)
    
    revenue_by_date = {}
    for item in sorted_sales:
        if item.date_added in revenue_by_date:
            revenue_by_date[item.date_added] += item.price
        else:
            revenue_by_date[item.date_added] = item.price

    return render_template('dashboard.html', 
                           my_listings=my_active_listings, 
                           my_sold_listings=my_sold_listings,
                           total_earnings=total_earnings,
                           recent_items=recent_items,
                           chart_labels=list(revenue_by_date.keys()),
                           chart_data=list(revenue_by_date.values()))

# --- PAYMENT & CHECKOUT ROUTES ---
@app.route('/buy/<int:product_id>', methods=['POST'])
def buy_product(product_id):
    if 'user_id' not in session:
        flash("Please log in to purchase items.")
        return redirect(url_for('login'))
        
    product = Product.query.get_or_404(product_id)
    payment_type = request.form.get('payment_type')
    location = request.form.get('meetup_location')
    
    if location == 'other':
        location = request.form.get('custom_location')

    if payment_type == 'cash':
        flash(f"Order confirmed! Please meet {product.seller} at the {location} for a cash exchange for '{product.title}'.")
    elif payment_type == 'new_card':
        card_number = request.form.get('card_number')
        last_four = card_number[-4:] if card_number else "XXXX"
        flash(f"Success! Charged ${product.price:.2f} to the card ending in {last_four}. Pick up your item from {product.seller} at the {location}.")
    else:
        flash(f"Success! Charged ${product.price:.2f} to your saved Visa. Pick up your item from {product.seller} at the {location}.")

    # --- NEW: Mark as sold instead of deleting ---
    product.is_sold = True
    product.buyer_username = session['username']
    db.session.commit()

    return redirect(url_for('marketplace'))

@app.route('/checkout/<int:product_id>')
def checkout_page(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # UPGRADED: Find the product in the SQLite Database instead of the old dummy list!
    product = Product.query.get_or_404(product_id)
    return render_template('checkout.html', product=product)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash("Please log in to view your profile.")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    
    # --- NEW: Catch "ghost" sessions from old databases ---
    if not user:
        session.clear()
        flash("Session expired or invalid. Please log in again.")
        return redirect(url_for('login'))
    
    # Fetch all items where this user is the buyer
    my_purchases = Product.query.filter_by(buyer_username=user.username).order_by(Product.date_added.desc()).all()

    return render_template('profile.html', user=user, purchases=my_purchases)

if __name__ == '__main__':
    app.run(debug=True)