from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from . import db
from .models import User
from .utils import admin_required

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Inicio de sesión exitoso', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home.dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('auth/login.html')


@auth.route('/create-user', methods=['GET', 'POST'])
@login_required
@admin_required  # Solo admins pueden acceder
def create_user():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'on'  # Checkbox
        
        # Validar que el usuario no exista
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe', 'danger')
            return redirect(url_for('auth.create_user'))
        
        if User.query.filter_by(email=email).first():
            flash('El email ya está registrado', 'danger')
            return redirect(url_for('auth.create_user'))
        
        # Crear nuevo usuario
        new_user = User(
            username=username, 
            email=email,
            is_admin=is_admin,
            created_by=current_user.id  # Registrar quién lo creó
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'Usuario {username} creado exitosamente', 'success')
        return redirect(url_for('auth.list_users'))
    
    return render_template('auth/create_user.html')

@auth.route('/users')
@login_required
@admin_required
def list_users():
    users = User.query.all()
    return render_template('auth/list_users.html', users=users)

@auth.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('No puedes eliminarte a ti mismo', 'danger')
        return redirect(url_for('auth.list_users'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    
    flash(f'Usuario {user.username} eliminado', 'success')
    return redirect(url_for('auth.list_users'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('auth.login'))