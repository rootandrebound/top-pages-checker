from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    """Render website's home page."""
    return render_template('home.html')
