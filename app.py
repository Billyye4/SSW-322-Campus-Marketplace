from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# 1. Add 'condition' to your dummy database
# Just updating the dummy_products list in app.py
dummy_products = [
    {
        "id": 1,
        "title": "Funkadelic Maggot Brain Vinyl",
        "seller": "VinylCollector99",
        "seller_rating": 4.9,  # <-- Added rating
        "description": "Classic funk rock album. Sleeve is in near-mint condition.",
        "price": 25.00,
        "condition": "Used - Good",
        "category": "Music",
        "date_added": "2026-03-10"
    },
    {
        "id": 2,
        "title": "Corsair 32GB DDR5 RAM",
        "seller": "HardwareSteve",
        "seller_rating": 5.0,  # <-- Added rating
        "description": "Upgraded my rig recently, these work perfectly. Great for a new build.",
        "price": 80.00,
        "condition": "Like New",
        "category": "Electronics",
        "date_added": "2026-03-12"
    },
    {
        "id": 3,
        "title": "Python Toolchains & Refactoring",
        "seller": "GradStudentBob",
        "seller_rating": 3.8,  # <-- Added rating
        "description": "Lightly used textbook. No highlighting on the pages.",
        "price": 45.00,
        "condition": "Used - Fair",
        "category": "Books",
        "date_added": "2026-03-14"
    }
]

# --- HOME ROUTE ---
@app.route('/')
def home():
    search_query = request.args.get('search', '').lower()
    condition_query = request.args.get('condition', 'All Conditions')
    category_query = request.args.get('category', 'All Categories')
    sort_query = request.args.get('sort', 'Newest First')
    
    filtered_products = []
    
    for product in dummy_products:
        matches_search = search_query in product['title'].lower() or search_query in product['description'].lower() or search_query == ''
        matches_condition = condition_query == 'All Conditions' or condition_query == product['condition']
        matches_category = category_query == 'All Categories' or category_query == product['category']
        
        if matches_search and matches_condition and matches_category:
            filtered_products.append(product)

    if sort_query == 'Price: Low to High':
        filtered_products.sort(key=lambda x: x['price'])
    elif sort_query == 'Price: High to Low':
        filtered_products.sort(key=lambda x: x['price'], reverse=True)
    elif sort_query == 'Newest First':
        filtered_products.sort(key=lambda x: x['date_added'], reverse=True)
    elif sort_query == 'Oldest First':
        filtered_products.sort(key=lambda x: x['date_added'])

    # --- NEW ADDITION FOR THE SIDEBAR ---
    # Grab the 3 newest items
    recent_items = sorted(dummy_products, key=lambda x: x['date_added'], reverse=True)[:3]

    # Pass BOTH filtered_products and recent_items to index.html
    return render_template('index.html', products=filtered_products, recent_items=recent_items)

# For a single product page
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    # Find the product by ID
    product = next((p for p in dummy_products if p['id'] == product_id), None)
    
    if product:
        return render_template('product.html', product=product)
    return "Product not found", 404

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