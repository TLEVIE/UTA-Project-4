# Import dependencies
from flask import Flask, render_template, request, jsonify, g
import sqlite3
import json

# Create Flask app
app = Flask(__name__)

# Home endpoint on Flask app.route /
@app.route('/')
def home():
    return render_template('home.html')

# Home endpoint on Flask app.route /js
@app.route('/application')
def js():
    return render_template('application.html')

# Run Flask app
if __name__ == "__main__":
    app.run(debug=True)
