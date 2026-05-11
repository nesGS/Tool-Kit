from flask import Blueprint, render_template
from flask_login import current_user
from .station_models import Station

home = Blueprint('home', __name__)

@home.route('/')
def index():
    stations_with_issues = []
    if current_user.is_authenticated:
        stations = Station.query.order_by(Station.name.asc()).all()
        stations_with_issues = [
            station for station in stations
            if station.has_active_breakdowns or station.has_active_interventions
        ]

    return render_template(
        'home/index.html',
        stations_with_issues=stations_with_issues
    )
