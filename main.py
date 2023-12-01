#.venv\Scripts\activate

from flask import Flask, get_flashed_messages, render_template, request, make_response, session
from flask import redirect, url_for, flash, g, json, copy_current_request_context, send_file
from flask_mail import Mail, Message
import threading
from functools import wraps
from config import DevelopmentConfig
from models import db, User, Estacionamientos, Boletos, Tarifas, Pagos
from helper import date_format
from flask_wtf.csrf import CSRFProtect
import forms 
from datetime import datetime
from io import BytesIO
import qrcode
from base64 import b64encode
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.units import inch
import base64

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf = CSRFProtect(app)
mail = Mail()
db.init_app(app)

def send_email(user_email, username):
    msg = Message('Gracias por tu registro!', sender=app.config['MAIL_USERNAME'], recipients=[user_email])
    msg.html = render_template('email.html', username = username)
    mail.send(msg)

@app.errorhandler(404)
def page_not_found(e):
    title = "Error"
    username = session['username']
    return render_template('404.html', title = title, username = username), 404

@app.before_request
def before_request():
    endpoints_prohibidos_sin = ['admin', 'index', 'codigo', 'eliminar', 'boletos', 'estacionamientos', 'tarifas', 'usuarios', 'eliminar_usuarios', 'registros', 'registrar_entrada', 'registrar_salida','registrar_por_admin']
    endpoints_prohibidos_con = ['admin', 'eliminar', 'boletos', 'estacionamientos', 'tarifas', 'usuarios', 'eliminar_usuarios', 'registros','registrar_por_admin']
    
    admin = User.query.filter_by(username = 'admin').first()

    if admin is None:
        estacionamiento = Estacionamientos(nombreE = 'Estacionamiento A', capacidad = 3, codigo_postal = 159357, lugares = 0)
        db.session.add(estacionamiento)
        db.session.commit()
        tarifa = Tarifas(tiempo_tol = 15, dos_horas = 20, hora_extra = 20, pension_dia = 200, pension_semana = 1000, pension_mes = 4000, estacionamiento = 'Estacionamiento A')
        db.session.add(tarifa)
        db.session.commit()
        admin = User(username = 'admin', email = '20203tn005@utez.edu.mx', password = 'admin123*', estacionamiento = 'Estacionamiento A', privilegio = "admin")
        db.session.add(admin)
        db.session.commit()

    if 'username' not in session and request.endpoint in endpoints_prohibidos_sin:
        flash(('Debes iniciar sesión!','warning'))
        return redirect(url_for('login'))
    elif 'username' in session:
        usuario = User.query.filter_by(username=session['username']).first()

        if usuario:
            if usuario.privilegio != "admin" and request.endpoint in endpoints_prohibidos_con:
                flash(('Acceso restringido para usuarios que no son administradores!','danger'))
                return redirect(url_for('index'))
            elif usuario.privilegio == "admin" and request.endpoint in ['login','create']:
                flash(('Hay una sesión activa!','info'))
                return redirect(url_for('admin'))
            elif request.endpoint in ['login','create']:
                flash(('Hay una sesión activa!','info'))
                return redirect(url_for('index'))


@app.after_request
def after_request(response):
    return response

@app.route('/cookie')
def cookie():
    response = make_response(render_template('cookie.html'))
    response.set_cookie('COOKIE', 'SISCON')
    return response

@app.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username')
        success_message = 'Hasta la próxima!'
        flash((success_message,'primary'))
    return redirect(url_for('login')) 

@app.route('/admin', methods = ['GET', 'POST'])
def admin():
    username = session['username']
    title = "Inicio"
    return render_template('admin.html', title = title, username = username)

@app.route('/', methods = ['GET', 'POST'])
def login():
    title = "Login"
    login_form = forms.LoginForm(request.form)
    if request.method == 'POST' and login_form.validate():
        username = login_form.username.data
        password = login_form.password.data
    
        user = User.query.filter_by(username = username).first()
        if user is not None and user.verify_password(password):
            if user.privilegio == "admin":
                success_message = 'Bienvenido {}!'.format(username)
                flash((success_message,'success'))
                session['username'] = username
                session['user_id'] = user.idUsuario
                return redirect(url_for('admin'))
            else:
                success_message = 'Bienvenido {}!'.format(username)
                flash((success_message,'success'))
                session['username'] = username
                session['user_id'] = user.idUsuario
                return redirect(url_for('index'))
        else: 
            flash(('Usuario o Contraseña no validos!','danger')) 
            if 'username' in session:
                session.pop('username')
            return redirect(url_for('login'))    
    return render_template('login.html', title = title, form=login_form)

@app.route('/create', methods = ['GET', 'POST'])
def create():
    title = "Registrarse"
    create_form = forms.usersForm(request.form)
    estacionamientos = Estacionamientos.query.all()
    if request.method == 'POST' and create_form.validate():
        user = User(create_form.username.data, 
                    create_form.email.data,
                    create_form.password.data,
                    create_form.estacionamiento.data,
                    create_form.privilegio.data)
        db.session.add(user)
        db.session.commit()

        @copy_current_request_context
        def send_message(email, username):
            send_email(email, username)
        success_message = 'Usuario registrado!'
        flash((success_message,'success'))

        sender = threading.Thread(name = 'mail_sender', target = send_message, args = (user.email, user.username))
        sender.start()

        return redirect(url_for('create'))
    else:
        username = create_form.username.data
        email = create_form.email.data
        user = User.query.filter_by(username = username).first()
        email = User.query.filter_by(email = email).first()
        if user is not None:
            error_message = 'El usuario ya se encuentra registrado!'
            flash((error_message,'danger')) 
        elif email is not None:
            error_message = 'El correo electrónico ya se ha utilizado!'
            flash((error_message,'danger')) 
    return render_template('create.html', title = title, form = create_form, estacionamientos = estacionamientos)

@app.route('/estacionamientos', methods = ['GET', 'POST'])
def estacionamientos():
    username = session['username']
    title = "Estacionamientos"
    estacionamiento_form = forms.EstacionamientoForm(request.form)
    estacionamientos = Estacionamientos.query.all()

    if request.method == 'POST' and estacionamiento_form.validate():
        estacionamiento = Estacionamientos(estacionamiento_form.nombreE.data, 
                        estacionamiento_form.capacidad.data,
                        estacionamiento_form.codigo_postal.data,
                        lugares=0)
        db.session.add(estacionamiento)
        db.session.commit()

        tarifa = Tarifas(tiempo_tol=15,
                        dos_horas=20,
                        hora_extra=20,
                        pension_dia=200,
                        pension_semana=1000,
                        pension_mes=4000,
                        estacionamiento=estacionamiento_form.nombreE.data)
        db.session.add(tarifa)
        db.session.commit()

        success_message = 'Estacionamiento registrado en la base de datos!'
        flash((success_message,'success'))
        return redirect(url_for('estacionamientos'))

    else:
        nombreE = estacionamiento_form.nombreE.data
        estacionamiento = Estacionamientos.query.filter_by(nombreE = nombreE).first()
        if estacionamiento is not None:
            error_message = 'El estacionamiento ya se encuentra registrado!'
            flash((error_message,'danger'))
    return render_template('estacionamientos.html', form = estacionamiento_form, title = title, username = username, estacionamientos = estacionamientos)

@app.route('/tarifas', methods = ['GET', 'POST'])
def tarifas():
    username = session['username']
    title = "Tarifas"
    estacionamientos = Estacionamientos.query.all()
    tarifas_form = forms.tarifasForm(request.form)
    tarifas = Tarifas.query.all()

    if request.method == 'POST' and tarifas_form.validate():
        estacionamiento_data = {
            'tiempo_tol': tarifas_form.tiempo_tol.data,
            'dos_horas': tarifas_form.dos_horas.data,
            'hora_extra': tarifas_form.hora_extra.data,
            'pension_dia': tarifas_form.pension_dia.data,
            'pension_semana': tarifas_form.pension_semana.data,
            'pension_mes': tarifas_form.pension_mes.data
        }

        Tarifas.query.filter_by(estacionamiento=tarifas_form.estacionamiento.data).update(estacionamiento_data)
        db.session.commit()

        success_message = 'Tarifas Actualizadas Correctamente!'
        flash((success_message,'success'))

    return render_template('tarifas.html', form = tarifas_form, estacionamientos = estacionamientos, tarifas = tarifas, username = username, title = title)

@app.route('/usuarios', methods = ['GET', 'POST'])
def usuarios():
    username = session['username']
    title = "Usuarios"
    usuarios = User.query.all()
    create_form = forms.usersForm(request.form)
    estacionamientos = Estacionamientos.query.all()
    if request.method == 'POST' and create_form.validate():
        user = User(create_form.username.data, 
                    create_form.email.data,
                    create_form.password.data,
                    create_form.estacionamiento.data,
                    create_form.privilegio.data)
        db.session.add(user)
        db.session.commit()

        @copy_current_request_context
        def send_message(email, username):
            send_email(email, username)
        success_message = 'Usuario registrado!'
        flash((success_message,'success'))

        sender = threading.Thread(name = 'mail_sender', target = send_message, args = (user.email, user.username))
        sender.start()

        return redirect(url_for('usuarios'))
    else:
        username = create_form.username.data
        email = create_form.email.data
        user = User.query.filter_by(username = username).first()
        email = User.query.filter_by(email = email).first()
        if user is not None:
            error_message = 'El usuario ya se encuentra registrado!'
            flash((error_message,'danger'))
        elif email is not None:
            error_message = 'El correo electrónico ya se ha utilizado!'
            flash((error_message,'danger'))
    return render_template('usuarios.html', form = create_form, estacionamientos = estacionamientos, usuarios = usuarios, username = username, title = title)

@app.route('/eliminar_usuario', methods =  ['GET', 'POST'])
def eliminar_usuario():
    if request.method == 'POST':
        idUsuario = request.form['idUsuario']
        usuario = User.query.get(idUsuario)
        if usuario:
            if usuario.idUsuario == 1:
                flash(('No puedes eliminar al creador de todo!', 'danger'))
            else:
                db.session.delete(usuario)
                db.session.commit()
                flash(('Usuario eliminado correctamente!', 'success'))
        else:
            flash(('No se encontró el usuario a eliminar!', 'danger'))
    return redirect(url_for('usuarios'))

@app.route('/modificar_usuario', methods =  ['GET', 'POST'])
def modificar_usuario():
    if request.method == 'POST':
        idUsuario = request.form['idUsuario']
        nombre = request.form['username']
        usuario = User.query.get(idUsuario)
        if usuario:
            if usuario.idUsuario == 1:
                flash(('No puedes modificar al creador de todo!', 'danger'))
            else:
                user = User.query.filter_by(username = nombre).first()
                if user is not None:
                    error_message = 'El nombre de usuario ya se encuentra registrado! Utiliza otro!'
                    flash((error_message,'danger')) 
                else:
                    usuario_data = {
                    'username': nombre,
                    }

                    User.query.filter_by(idUsuario=idUsuario).update(usuario_data)
                    db.session.commit()
                    flash(('Usuario modificado correctamente!', 'success'))      
        else:
            flash(('No se encontró el usuario a modificar!', 'danger'))        
    return redirect(url_for('usuarios'))

@app.route('/registros', methods = ['GET', 'POST'])
def registros():
    username = session['username']
    title = "Registros"
    estacionamientos = Estacionamientos.query.all()
    registros_form = forms.registrosForm(request.form)
    estacionamiento_nombre = registros_form.estacionamiento.data
    boletos = Boletos.query.filter_by(estacionamiento = estacionamiento_nombre).all()
    suma_total_pagos = 0
    if request.method == 'POST' and registros_form.validate():
        pagos_estacionamiento = Pagos.query.filter_by(estacionamiento = estacionamiento_nombre).all()
        suma_total_pagos = sum(pago.total_pago for pago in pagos_estacionamiento)

    return render_template('registros.html', form = registros_form, boletos = boletos, suma_total_pagos = suma_total_pagos, username = username, estacionamiento = estacionamiento_nombre, estacionamientos = estacionamientos, title = title)



@app.route('/registrados', methods = ['GET', 'POST'])
def registrados():
    suma_total_pagos = 0
    username = session['username']
    title = "Registrados"
    registros=''
    fecha_inicio = ''
    fecha_fin = ''
    if request.method == 'POST':

        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']

        query = text(f"SELECT sumar_boletos('{fecha_inicio}', '{fecha_fin}')")
        suma_total_pagos = db.session.execute(query).scalar()
            
        registros = obtener_registros(fecha_inicio, fecha_fin) 
    return render_template('registrados.html', username = username,  title = title, registros = registros, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, suma_total_pagos=suma_total_pagos)

@app.route('/ajax-login', methods=['POST'])
def ajax_login():
    print(request.form)
    username = request.form['username']
    response = {'status':200, 'username':username, 'id':1}
    return json.dumps(response)


if __name__ == '__main__':
    csrf.init_app(app)
    mail.init_app(app)

    with app.app_context():
        db.create_all()

    app.run(port=8000)
