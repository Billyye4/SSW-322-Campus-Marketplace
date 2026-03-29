<<<<<<< HEAD
from flask import Flask, render_template, request, redirect, url_for
=======
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import date
>>>>>>> 85088ece75e88cdc9c5cc6687e88eb1ead78d8ec

app = Flask(__name__)
app.secret_key = "super_secret_campus_key"

# 1. Configure the SQLite database
# This tells Flask to create a file called 'marketplace.db' in your project folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///marketplace.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 2. Define the Product Database Model
# This replaces the dummy dictionaries. Each attribute becomes a column in the database.
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

# 3. Initialize the database with our starter data
with app.app_context():
    db.create_all()
    # If the database is completely empty, add our 3 starter items
    if not Product.query.first():
        starter_items = [
            Product(title="Funkadelic Maggot Brain Vinyl", seller="VinylCollector99", seller_rating=4.9, reviews=12, description="Classic funk rock album. Sleeve is in near-mint condition.", price=25.00, condition="Used - Good", category="Music", date_added="2026-03-10"),
            Product(title="Corsair 32GB DDR5 RAM", seller="HardwareSteve", seller_rating=5.0, reviews=54, description="Upgraded my rig recently, these work perfectly. Great for a new build.", price=80.00, condition="Like New", category="Electronics", date_added="2026-03-12"),
            Product(title="Python Toolchains & Refactoring", seller="GradStudentBob", seller_rating=3.8, reviews=4, description="Lightly used textbook. No highlighting on the pages.", price=45.00, condition="Used - Fair", category="Books", date_added="2026-03-14")
        ]
        db.session.bulk_save_objects(starter_items)
        db.session.commit()

# --- HOME ROUTE ---
@app.route('/')
def home():
    search_query = request.args.get('search', '').lower()
    condition_query = request.args.get('condition', 'All Conditions')
    category_query = request.args.get('category', 'All Categories')
    sort_query = request.args.get('sort', 'Newest First')
    
    # Query all products from the database!
    products = Product.query.all()
    filtered_products = []
    
    for product in products:
        # Notice we use dot notation (product.title) instead of dictionary syntax now
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

    # Use a direct database query to get the 3 newest items for the sidebar
    recent_items = Product.query.order_by(Product.date_added.desc()).limit(3).all()

    return render_template('index.html', products=filtered_products, recent_items=recent_items)

# --- SINGLE PRODUCT ROUTE ---
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    # This automatically throws a 404 error if the ID doesn't exist in the DB
    product = Product.query.get_or_404(product_id)
    return render_template('product.html', product=product)

# --- DUMMY PAYMENT ROUTE ---
@app.route('/buy/<int:product_id>', methods=['POST'])
def buy_product(product_id):
    product = Product.query.get_or_404(product_id)
    flash(f"Success! You just 'purchased' {product.title} for ${product.price:.2f}")
    
    # Optional: If you wanted items to disappear when bought, you would run this:
    # db.session.delete(product)
    # db.session.commit()
    
    return redirect(url_for('home'))

# --- SELLER DASHBOARD (My Listings) ---
# Added methods=['GET', 'POST'] to allow form submissions
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        # 1. Grab all the data from the HTML form
        title = request.form.get('title')
        price = request.form.get('price')
        category = request.form.get('category')
        condition = request.form.get('condition')
        description = request.form.get('description')
        
        # 2. Package it into a new Product database object
        new_listing = Product(
            title=title,
            seller="Seller",  # We are setting you as the permanent seller for these!
            seller_rating=5.0, # Start with a perfect 5 stars
            reviews=0,
            description=description,
            price=float(price),
            condition=condition,
            category=category,
            date_added=date.today().strftime("%Y-%m-%d") # Automatically grabs today's date
        )
        
        # 3. Save it to the database permanently
        db.session.add(new_listing)
        db.session.commit()
        
        # 4. Flash a success message and reload the page
        flash(f"Successfully listed: {title}!")
        return redirect(url_for('dashboard'))

    # If it's just a normal GET request (loading the page):
    recent_items = Product.query.order_by(Product.date_added.desc()).limit(3).all()
    
    # We filter the left column to ONLY show items where the seller is "Billy"
    my_active_listings = Product.query.filter_by(seller="Billy").all()

    return render_template('dashboard.html', my_listings=my_active_listings, recent_items=recent_items)

# This handles the "Buy Now" button click
@app.route('/buy/<int:product_id>', methods=['POST'])
def buy_product(product_id):
    # In the future, you could add logic here (like checking if the item is still in stock).
    # For now, we just instantly redirect the user to the checkout page!
    return redirect(url_for('checkout_page', product_id=product_id))

# This actually displays the Checkout HTML page
@app.route('/checkout/<int:product_id>')
def checkout_page(product_id):
    # Find the specific product so we can show its price/title on the checkout screen
    product = next((p for p in dummy_products if p['id'] == product_id), None)
    
    if product:
        # Assuming you saved the checkout code I gave you earlier as 'checkout.html'
        return render_template('checkout.html', product=product)
    
    return "Product not found", 404

if __name__ == '__main__':
    app.run(debug=True)