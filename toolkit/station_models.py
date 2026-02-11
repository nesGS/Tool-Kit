from . import db
from datetime import datetime
from flask_login import current_user

class Station(db.Model):
    __tablename__ = 'Station'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='activa')  # activa, inactiva, mantenimiento, averiada
    installation_date = db.Column(db.DateTime, nullable=True)
    
    # Relaciones
    sensors = db.relationship('Sensor', backref='station', lazy=True, cascade='all, delete-orphan')
    router = db.relationship('Router', backref='station', uselist=False, cascade='all, delete-orphan')
    technical_details = db.relationship('TechnicalDetail', backref='station', lazy=True, cascade='all, delete-orphan')
    breakdowns = db.relationship('Breakdown', backref='station', lazy=True, cascade='all, delete-orphan')
    interventions = db.relationship('Intervention', backref='station', lazy=True, cascade='all, delete-orphan')
    history = db.relationship('StationHistory', backref='station', lazy=True, cascade='all, delete-orphan')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    @property
    def active_breakdowns(self):
        """Averías activas (no resueltas)"""
        return [b for b in self.breakdowns if not b.resolved]
    
    @property
    def has_active_breakdowns(self):
        """¿Tiene averías activas?"""
        return len(self.active_breakdowns) > 0
    
    def __repr__(self):
        return f'<Station {self.name}>'


class Sensor(db.Model):
    __tablename__ = 'sensor'
    
    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('Station.id'), nullable=False)
    sensor_type = db.Column(db.String(50), nullable=False)  # temperatura, humedad, presión, viento, lluvia
    model = db.Column(db.String(100), nullable=True)
    serial_number = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='operativo')  # operativo, averiado, en_calibración
    installation_date = db.Column(db.DateTime, nullable=True)
    last_calibration = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Sensor {self.sensor_type} - {self.model}>'


class Router(db.Model):
    __tablename__ = 'router'
    
    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('Station.id'), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 o IPv6
    mac_address = db.Column(db.String(17), nullable=True)
    serial_number = db.Column(db.String(100), nullable=True)
    firmware_version = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='online')  # online, offline, mantenimiento
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Router {self.model} - {self.ip_address}>'


class TechnicalDetail(db.Model):
    __tablename__ = 'technical_detail'
    
    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('Station.id'), nullable=False)
    detail_type = db.Column(db.String(50), nullable=False)  # alimentación, conectividad, estructura, etc.
    key = db.Column(db.String(100), nullable=False)  # ej: "Tipo de alimentación"
    value = db.Column(db.Text, nullable=False)  # ej: "Solar + Batería de respaldo"
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<TechnicalDetail {self.key}>'


class Breakdown(db.Model):
    __tablename__ = 'breakdown'
    
    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('Station.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default='media')  # baja, media, alta, crítica
    reported_date = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_date = db.Column(db.DateTime, nullable=True)
    resolved = db.Column(db.Boolean, default=False)
    resolution_notes = db.Column(db.Text, nullable=True)
    
    reported_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    resolved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relación con usuario que reportó
    reporter = db.relationship('User', foreign_keys=[reported_by])
    resolver = db.relationship('User', foreign_keys=[resolved_by])
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def duration(self):
        """Duración de la avería"""
        if self.resolved and self.resolved_date:
            return self.resolved_date - self.reported_date
        return datetime.utcnow() - self.reported_date
    
    def __repr__(self):
        return f'<Breakdown {self.title}>'


class Intervention(db.Model):
    __tablename__ = 'intervention'
    
    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('Station.id'), nullable=False)
    intervention_type = db.Column(db.String(50), nullable=False)  # mantenimiento, reparación, calibración, instalación
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    intervention_date = db.Column(db.DateTime, default=datetime.utcnow)
    technician_name = db.Column(db.String(100), nullable=True)
    
    performed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    technician = db.relationship('User', foreign_keys=[performed_by])
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Intervention {self.title}>'


class StationHistory(db.Model):
    __tablename__ = 'station_history'
    
    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('Station.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # created, updated, status_changed, etc.
    field_changed = db.Column(db.String(100), nullable=True)  # Campo que cambió
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    
    changed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', foreign_keys=[changed_by])
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StationHistory {self.action}>'