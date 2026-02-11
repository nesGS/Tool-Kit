from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from . import db
from .station_models import Station, Sensor, Router, TechnicalDetail, Breakdown, Intervention, StationHistory
from .utils import admin_required
from datetime import datetime

stations = Blueprint('stations', __name__)

# Función auxiliar para registrar cambios
def log_change(station_id, action, field=None, old_value=None, new_value=None, description=None):
    history = StationHistory(
        station_id=station_id,
        action=action,
        field_changed=field,
        old_value=str(old_value) if old_value else None,
        new_value=str(new_value) if new_value else None,
        description=description,
        changed_by=current_user.id
    )
    db.session.add(history)

# Lista de estaciones
@stations.route('/')
@login_required
def list_stations():
    stations = Station.query.all()
    return render_template('stations/list_stations.html', stations=stations)

# Ver detalle de una estación
@stations.route('/<int:station_id>')
@login_required
def view_station(station_id):
    station = Station.query.get_or_404(station_id)
    return render_template('stations/view_station.html', station=station)

# Crear nueva estación
@stations.route('/new', methods=['GET', 'POST'])
@login_required
def create_station():
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        status = request.form.get('status', 'activa')
        installation_date = request.form.get('installation_date')
        
        # Validar que no exista
        if Station.query.filter_by(name=name).first():
            flash('Ya existe una estación con ese nombre', 'danger')
            return redirect(url_for('stations.create_station'))
        
        # Crear estación
        station = Station(
            name=name,
            location=location,
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None,
            status=status,
            installation_date=datetime.strptime(installation_date, '%Y-%m-%d') if installation_date else None,
            created_by=current_user.id
        )
        
        db.session.add(station)
        db.session.commit()
        
        # Registrar en historial
        log_change(station.id, 'created', description=f'Estación {name} creada')
        db.session.commit()
        
        flash(f'Estación {name} creada exitosamente', 'success')
        return redirect(url_for('stations.view_station', station_id=station.id))
    
    return render_template('stations/create_station.html')

# Editar estación
@stations.route('/<int:station_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_station(station_id):
    station = Station.query.get_or_404(station_id)
    
    if request.method == 'POST':
        old_status = station.status
        
        station.name = request.form.get('name')
        station.location = request.form.get('location')
        station.latitude = float(request.form.get('latitude')) if request.form.get('latitude') else None
        station.longitude = float(request.form.get('longitude')) if request.form.get('longitude') else None
        station.status = request.form.get('status')
        
        if request.form.get('installation_date'):
            station.installation_date = datetime.strptime(request.form.get('installation_date'), '%Y-%m-%d')
        
        # Registrar cambio de estado si hubo
        if old_status != station.status:
            log_change(station.id, 'status_changed', 'status', old_status, station.status)
        
        log_change(station.id, 'updated', description='Información de estación actualizada')
        
        db.session.commit()
        flash('Estación actualizada exitosamente', 'success')
        return redirect(url_for('stations.view_station', station_id=station.id))
    
    return render_template('stations/edit_station.html', station=station)

# Eliminar estación (solo admin)
@stations.route('/<int:station_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_station(station_id):
    station = Station.query.get_or_404(station_id)
    station_name = station.name
    db.session.delete(station)
    db.session.commit()
    flash(f'Estación {station_name} eliminada exitosamente', 'success')
    return redirect(url_for('stations.list_stations'))

# Añadir sensor
@stations.route('/<int:station_id>/sensors/add', methods=['GET', 'POST'])
@login_required
def add_sensor(station_id):
    station = Station.query.get_or_404(station_id)
    
    if request.method == 'POST':
        sensor = Sensor(
            station_id=station_id,
            sensor_type=request.form.get('sensor_type'),
            model=request.form.get('model'),
            serial_number=request.form.get('serial_number'),
            status=request.form.get('status', 'operativo'),
            installation_date=datetime.strptime(request.form.get('installation_date'), '%Y-%m-%d') if request.form.get('installation_date') else None
        )
        
        db.session.add(sensor)
        log_change(station_id, 'sensor_added', description=f'Sensor {sensor.sensor_type} añadido')
        db.session.commit()
        
        flash('Sensor añadido exitosamente', 'success')
        return redirect(url_for('stations.view_station', station_id=station_id))
    
    return render_template('stations/add_sensor.html', station=station)

# Configurar router
@stations.route('/<int:station_id>/router', methods=['GET', 'POST'])
@login_required
def configure_router(station_id):
    station = Station.query.get_or_404(station_id)
    router = station.router
    
    if request.method == 'POST':
        if not router:
            router = Router(station_id=station_id)
        
        router.model = request.form.get('model')
        router.ip_address = request.form.get('ip_address')
        router.mac_address = request.form.get('mac_address')
        router.serial_number = request.form.get('serial_number')
        router.firmware_version = request.form.get('firmware_version')
        router.status = request.form.get('status', 'online')
        
        db.session.add(router)
        log_change(station_id, 'router_configured', description='Router configurado/actualizado')
        db.session.commit()
        
        flash('Router configurado exitosamente', 'success')
        return redirect(url_for('stations.view_station', station_id=station_id))
    
    return render_template('stations/configure_router.html', station=station, router=router)

# Añadir detalle técnico
@stations.route('/<int:station_id>/details/add', methods=['GET', 'POST'])
@login_required
def add_technical_detail(station_id):
    station = Station.query.get_or_404(station_id)
    
    if request.method == 'POST':
        detail = TechnicalDetail(
            station_id=station_id,
            detail_type=request.form.get('detail_type'),
            key=request.form.get('key'),
            value=request.form.get('value')
        )
        
        db.session.add(detail)
        log_change(station_id, 'detail_added', description=f'Detalle técnico: {detail.key}')
        db.session.commit()
        
        flash('Detalle técnico añadido', 'success')
        return redirect(url_for('stations.view_station', station_id=station_id))
    
    return render_template('stations/add_technical_detail.html', station=station)

# Reportar avería
@stations.route('/<int:station_id>/breakdowns/report', methods=['GET', 'POST'])
@login_required
def report_breakdown(station_id):
    station = Station.query.get_or_404(station_id)
    
    if request.method == 'POST':
        breakdown = Breakdown(
            station_id=station_id,
            title=request.form.get('title'),
            description=request.form.get('description'),
            severity=request.form.get('severity', 'media'),
            reported_by=current_user.id
        )
        
        db.session.add(breakdown)
        log_change(station_id, 'breakdown_reported', description=f'Avería reportada: {breakdown.title}')
        db.session.commit()
        
        flash('Avería reportada exitosamente', 'warning')
        return redirect(url_for('stations.view_station', station_id=station_id))
    
    return render_template('stations/report_breakdown.html', station=station)

# Resolver avería
@stations.route('/breakdowns/<int:breakdown_id>/resolve', methods=['GET', 'POST'])
@login_required
def resolve_breakdown(breakdown_id):
    breakdown = Breakdown.query.get_or_404(breakdown_id)
    
    if request.method == 'POST':
        breakdown.resolved = True
        breakdown.resolved_date = datetime.utcnow()
        breakdown.resolved_by = current_user.id
        breakdown.resolution_notes = request.form.get('resolution_notes')
        
        log_change(breakdown.station_id, 'breakdown_resolved', description=f'Avería resuelta: {breakdown.title}')
        db.session.commit()
        
        flash('Avería marcada como resuelta', 'success')
        return redirect(url_for('stations.view_station', station_id=breakdown.station_id))
    
    return render_template('stations/resolve_breakdown.html', breakdown=breakdown)

# Registrar intervención
@stations.route('/<int:station_id>/interventions/add', methods=['GET', 'POST'])
@login_required
def add_intervention(station_id):
    station = Station.query.get_or_404(station_id)
    
    if request.method == 'POST':
        intervention = Intervention(
            station_id=station_id,
            intervention_type=request.form.get('intervention_type'),
            title=request.form.get('title'),
            description=request.form.get('description'),
            intervention_date=datetime.strptime(request.form.get('intervention_date'), '%Y-%m-%d') if request.form.get('intervention_date') else datetime.utcnow(),
            duration_hours=float(request.form.get('duration_hours')) if request.form.get('duration_hours') else None,
            cost=float(request.form.get('cost')) if request.form.get('cost') else None,
            technician_name=request.form.get('technician_name'),
            performed_by=current_user.id
        )
        
        db.session.add(intervention)
        log_change(station_id, 'intervention_added', description=f'Intervención: {intervention.title}')
        db.session.commit()
        
        flash('Intervención registrada exitosamente', 'success')
        return redirect(url_for('stations.view_station', station_id=station_id))
    
    return render_template('stations/add_intervention.html', station=station, now=datetime.now())

# Ver historial completo
@stations.route('/<int:station_id>/history')
@login_required
def view_history(station_id):
    station = Station.query.get_or_404(station_id)
    history = StationHistory.query.filter_by(station_id=station_id).order_by(StationHistory.created_at.desc()).all()
    return render_template('stations/view_history.html', station=station, history=history)
