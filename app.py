from flask import Flask, render_template, request

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

@app.route('/')
def home():
    # Grab the search term AND the condition from the URL
    search_query = request.args.get('search', '').lower()
    condition_query = request.args.get('condition', 'All Conditions')
    category_query = request.args.get('category', 'All Categories')
    sort_query = request.args.get('sort', 'Newest First')
    
    filtered_products = []
    
    # Filter the products based on search AND condition
    for product in dummy_products:
        # Check if it matches the search term (if there is one)
        matches_search = search_query in product['title'].lower() or search_query in product['description'].lower() or search_query == ''
        # Check if it matches the dropdown condition
        matches_condition = condition_query == 'All Conditions' or condition_query == product['condition']
        # Check if it matches the dropdown category
        matches_category = category_query == 'All Categories' or category_query == product['category']
        
        # If it matches BOTH, add it to our filtered list
        if matches_search and matches_condition:
            filtered_products.append(product)
    
    if sort_query == 'Price: Low to High':
        filtered_products.sort(key=lambda x: x['price'])
    elif sort_query == 'Price: High to Low':
        filtered_products.sort(key=lambda x: x['price'], reverse=True)
    elif sort_query == 'Newest First':
        filtered_products.sort(key=lambda x: x['date_added'], reverse=True)
    elif sort_query == 'Oldest First':
        filtered_products.sort(key=lambda x: x['date_added'])

    return render_template('index.html', products=filtered_products)

# For a single product page
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    # Find the product by ID
    product = next((p for p in dummy_products if p['id'] == product_id), None)
    
    if product:
        return render_template('product.html', product=product)
    return "Product not found", 404

if __name__ == '__main__':
    app.run(debug=True)