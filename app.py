from flask import Flask, render_template

app = Flask(__name__)

# This is the route for your homepage
@app.route('/')
def home():
    # Flask automatically looks in the "templates" folder for this file
    return render_template('index.html')

if __name__ == '__main__':
    # debug=True automatically restarts the server when you make changes
    app.run(debug=True)