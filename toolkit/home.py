from flask import Blueprint, render_template
from flask_login import login_required, current_user

home = Blueprint('home', __name__)

@home.route('/')
def index():
    return render_template('home/index.html')

@home.route('/dashboard')
@login_required
def dashboard():
    return render_template('home/dashboard.html')