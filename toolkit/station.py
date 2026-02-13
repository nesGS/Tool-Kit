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

# Ver vista general de una estación
@stations.route('/<int:station_id>')
@login_required
def view_station(station_id):
    station = Station.query.get_or_404(station_id)
    recent_history = StationHistory.query.filter_by(station_id=station_id).order_by(StationHistory.created_at.desc()).limit(5).all()
    recent_breakdowns = Breakdown.query.filter_by(station_id=station_id).order_by(Breakdown.reported_date.desc()).limit(3).all()
    recent_interventions = Intervention.query.filter(
        Intervention.station_id == station_id,
        Intervention.technician_name.isnot(None)
    ).order_by(
        Intervention.created_at.desc()
    ).limit(3).all()
    return render_template(
        'stations/view_station.html',
        station=station,
        recent_history=recent_history,
        recent_breakdowns=recent_breakdowns,
        recent_interventions=recent_interventions
    )

# Ver detalle completo de una estación
@stations.route('/<int:station_id>/details')
@login_required
def view_station_details(station_id):
    station = Station.query.get_or_404(station_id)
    recent_history = StationHistory.query.filter_by(station_id=station_id).order_by(StationHistory.created_at.desc()).limit(5).all()
    return render_template('stations/view_station_details.html', station=station, recent_history=recent_history)

# Crear nueva estación
@stations.route('/new', methods=['GET', 'POST'])
@login_required
def create_station():
    if request.method == 'POST':
        name = request.form.get('name')
        island = request.form.get('island')
        municipality = request.form.get('municipality')
        location = request.form.get('location')
        coordinates = request.form.get('coordinates')
        contact = request.form.get('contact')
        how_to_get = request.form.get('how_to_get')
        required_vehicle = request.form.get('required_vehicle')
        measurement_type = request.form.get('measurement_type')
        status = request.form.get('status', 'activa')
        
        # Validar que no exista
        if Station.query.filter_by(name=name).first():
            flash('Ya existe una estación con ese nombre', 'danger')
            return redirect(url_for('stations.create_station'))
        
        # Crear estación
        station = Station(
            name=name,
            island=island,
            municipality=municipality,
            location=location,
            coordinates=coordinates,
            contact=contact,
            how_to_get=how_to_get,
            required_vehicle=required_vehicle,
            measurement_type=measurement_type,
            status=status,
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
        station.island = request.form.get('island')
        station.municipality = request.form.get('municipality')
        station.location = request.form.get('location')
        station.coordinates = request.form.get('coordinates')
        station.contact = request.form.get('contact')
        station.how_to_get = request.form.get('how_to_get')
        station.required_vehicle = request.form.get('required_vehicle')
        station.measurement_type = request.form.get('measurement_type')
        station.status = request.form.get('status')
        
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
        return redirect(url_for('stations.view_station_details', station_id=station_id))
    
    return render_template('stations/add_sensor.html', station=station)

# Editar sensor
@stations.route('/<int:station_id>/sensors/<int:sensor_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_sensor(station_id, sensor_id):
    station = Station.query.get_or_404(station_id)
    sensor = Sensor.query.filter_by(id=sensor_id, station_id=station_id).first_or_404()

    if request.method == 'POST':
        sensor.sensor_type = request.form.get('sensor_type')
        sensor.model = request.form.get('model')
        sensor.serial_number = request.form.get('serial_number')
        sensor.status = request.form.get('status', 'operativo')
        sensor.installation_date = datetime.strptime(request.form.get('installation_date'), '%Y-%m-%d') if request.form.get('installation_date') else None

        log_change(station_id, 'sensor_updated', description=f'Sensor {sensor.sensor_type} actualizado')
        db.session.commit()

        flash('Sensor actualizado exitosamente', 'success')
        return redirect(url_for('stations.view_station_details', station_id=station_id))

    return render_template('stations/edit_sensor.html', station=station, sensor=sensor)

# Eliminar sensor
@stations.route('/<int:station_id>/sensors/<int:sensor_id>/delete', methods=['POST'])
@login_required
def delete_sensor(station_id, sensor_id):
    sensor = Sensor.query.filter_by(id=sensor_id, station_id=station_id).first_or_404()
    sensor_label = sensor.model or sensor.sensor_type
    db.session.delete(sensor)
    log_change(station_id, 'sensor_deleted', description=f'Sensor {sensor_label} eliminado')
    db.session.commit()

    flash('Sensor eliminado exitosamente', 'success')
    return redirect(url_for('stations.view_station_details', station_id=station_id))

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
        return redirect(url_for('stations.view_station_details', station_id=station_id))
    
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
        return redirect(url_for('stations.view_station_details', station_id=station_id))
    
    return render_template('stations/add_technical_detail.html', station=station)

# Editar detalle técnico
@stations.route('/<int:station_id>/details/<int:detail_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_technical_detail(station_id, detail_id):
    station = Station.query.get_or_404(station_id)
    detail = TechnicalDetail.query.filter_by(id=detail_id, station_id=station_id).first_or_404()

    if request.method == 'POST':
        detail.detail_type = request.form.get('detail_type')
        detail.key = request.form.get('key')
        detail.value = request.form.get('value')

        log_change(station_id, 'detail_updated', description=f'Detalle técnico {detail.key} actualizado')
        db.session.commit()

        flash('Detalle técnico actualizado', 'success')
        return redirect(url_for('stations.view_station_details', station_id=station_id))

    return render_template('stations/edit_technical_detail.html', station=station, detail=detail)

# Eliminar detalle técnico
@stations.route('/<int:station_id>/details/<int:detail_id>/delete', methods=['POST'])
@login_required
def delete_technical_detail(station_id, detail_id):
    detail = TechnicalDetail.query.filter_by(id=detail_id, station_id=station_id).first_or_404()
    detail_key = detail.key
    db.session.delete(detail)
    log_change(station_id, 'detail_deleted', description=f'Detalle técnico {detail_key} eliminado')
    db.session.commit()

    flash('Detalle técnico eliminado', 'success')
    return redirect(url_for('stations.view_station_details', station_id=station_id))

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

# Programar intervención (queda activa hasta realizarse)
@stations.route('/<int:station_id>/interventions/schedule', methods=['GET', 'POST'])
@login_required
def schedule_intervention(station_id):
    station = Station.query.get_or_404(station_id)

    if request.method == 'POST':
        intervention = Intervention(
            station_id=station_id,
            intervention_type=request.form.get('intervention_type'),
            title=request.form.get('title'),
            description=request.form.get('description'),
            intervention_date=None,
            technician_name=None,
            performed_by=current_user.id
        )

        db.session.add(intervention)
        log_change(station_id, 'intervention_scheduled', description=f'Intervención programada: {intervention.title}')
        db.session.commit()

        flash('Intervención programada exitosamente', 'info')
        return redirect(url_for('stations.view_station', station_id=station_id))

    return render_template('stations/schedule_intervention.html', station=station)

# Marcar intervención programada como realizada
@stations.route('/interventions/<int:intervention_id>/complete', methods=['GET', 'POST'])
@login_required
def complete_intervention(intervention_id):
    intervention = Intervention.query.get_or_404(intervention_id)

    if request.method == 'POST':
        intervention.intervention_date = datetime.utcnow()
        intervention.technician_name = current_user.username
        intervention.performed_by = current_user.id

        log_change(
            intervention.station_id,
            'intervention_completed',
            description=f'Intervención realizada: {intervention.title}'
        )
        db.session.commit()

        flash('Intervención marcada como realizada', 'success')
        return redirect(url_for('stations.view_station', station_id=intervention.station_id))

    return render_template('stations/complete_intervention.html', intervention=intervention)

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
            intervention_date=datetime.utcnow(),
            technician_name=current_user.username,
            performed_by=current_user.id
        )
        
        db.session.add(intervention)
        log_change(station_id, 'intervention_added', description=f'Intervención: {intervention.title}')
        db.session.commit()
        
        flash('Intervención registrada exitosamente', 'success')
        return redirect(url_for('stations.view_station', station_id=station_id))
    
    return render_template('stations/add_intervention.html', station=station)

# Ver historial completo
@stations.route('/<int:station_id>/history')
@login_required
def view_history(station_id):
    station = Station.query.get_or_404(station_id)
    history = StationHistory.query.filter_by(station_id=station_id).order_by(StationHistory.created_at.desc()).all()
    return render_template('stations/view_history.html', station=station, history=history)

# Eliminar registro de historial (solo admin)
@stations.route('/history/<int:history_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_history_record(history_id):
    history_record = StationHistory.query.get_or_404(history_id)
    station_id = history_record.station_id
    db.session.delete(history_record)
    db.session.commit()
    flash('Registro de historial eliminado', 'success')
    return redirect(url_for('stations.view_history', station_id=station_id))

# Ver historial completo de averías
@stations.route('/<int:station_id>/breakdowns/history')
@login_required
def view_breakdowns_history(station_id):
    station = Station.query.get_or_404(station_id)
    breakdowns = Breakdown.query.filter_by(station_id=station_id).order_by(Breakdown.reported_date.desc()).all()
    return render_template('stations/view_breakdowns_history.html', station=station, breakdowns=breakdowns)

# Eliminar avería (solo admin)
@stations.route('/breakdowns/<int:breakdown_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_breakdown(breakdown_id):
    breakdown = Breakdown.query.get_or_404(breakdown_id)
    station_id = breakdown.station_id
    db.session.delete(breakdown)
    db.session.commit()
    flash('Avería eliminada', 'success')
    return redirect(url_for('stations.view_breakdowns_history', station_id=station_id))

# Ver historial completo de intervenciones
@stations.route('/<int:station_id>/interventions/history')
@login_required
def view_interventions_history(station_id):
    station = Station.query.get_or_404(station_id)
    interventions = Intervention.query.filter_by(station_id=station_id).order_by(
        Intervention.created_at.desc()
    ).all()
    return render_template('stations/view_interventions_history.html', station=station, interventions=interventions)

# Eliminar intervención (solo admin)
@stations.route('/interventions/<int:intervention_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_intervention(intervention_id):
    intervention = Intervention.query.get_or_404(intervention_id)
    station_id = intervention.station_id
    db.session.delete(intervention)
    db.session.commit()
    flash('Intervención eliminada', 'success')
    return redirect(url_for('stations.view_interventions_history', station_id=station_id))
