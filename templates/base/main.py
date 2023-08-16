#.venv\Scripts\activate

from flask import Flask, get_flashed_messages, render_template, request, make_response, session
from flask import redirect, url_for, flash, g, json, copy_current_request_context
from flask_mail import Mail, Message
import threading
from functools import wraps
from config import DevelopmentConfig
from models import db, User, Estacionamientos, Boletos, Tarifas, Pagos
from helper import date_format
from flask_wtf.csrf import CSRFProtect
import forms 
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf = CSRFProtect(app)
mail = Mail()
db.init_app(app)
csrf.init_app(app)
mail.init_app(app)
with app.app_context():
    db.create_all()

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
    endpoints_prohibidos_sin = ['admin', 'eliminar', 'boletos', 'estacionamientos', 'tarifas', 'usuarios', 'eliminar_usuarios', 'registros', 'registrar_entrada', 'registrar_salida']
    endpoints_prohibidos_con = ['admin', 'eliminar', 'boletos', 'estacionamientos', 'tarifas', 'usuarios', 'eliminar_usuarios', 'registros']

    admin = User.query.filter_by(username = 'admin').first()
    if admin is None:
        estacionamiento = Estacionamientos(nombreE = 'Estacionamiento A', capacidad = 50, codigo_postal = 159357)
        db.session.add(estacionamiento)
        db.session.commit()
        tarifa = Tarifas(tiempo_tol = 15, dos_horas = 20, hora_extra = 20, estacionamiento = 'Estacionamiento A')
        db.session.add(tarifa)
        db.session.commit()
        admin = User(username = 'admin', email = '20203tn005@utez.edu.mx', password = 'admin123*', estacionamiento = 'Estacionamiento A')
        db.session.add(admin)
        db.session.commit()
    if 'username' not in session and request.endpoint in endpoints_prohibidos_sin:
        flash(('Debes iniciar sesión!','warning'))
        return redirect(url_for('login'))
    elif 'username' in session and session['username'] != 'admin' and request.endpoint in endpoints_prohibidos_con:
        flash(('Acceso restringido para usuarios que no son administradores!','danger'))
        return redirect(url_for('index'))
    elif 'username' in session and session['username'] == 'admin' and request.endpoint in ['login','create']:
        flash(('Hay una sesión activa!','info'))
        return redirect(url_for('admin'))
    elif 'username' in session and request.endpoint in ['login','create']:
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
            if username == "admin":
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
                    create_form.estacionamiento.data)
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
                        estacionamiento_form.codigo_postal.data)
        db.session.add(estacionamiento)
        db.session.commit()

        tarifa = Tarifas(tiempo_tol=15,
                        dos_horas=20,
                        hora_extra=20,
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
            'hora_extra': tarifas_form.hora_extra.data
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
                    create_form.estacionamiento.data)
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

@app.route('/inicio', methods = ['GET', 'POST'])
def index():
    title = "SISCON"
    username = session['username']
    boletos = Boletos.query.filter_by(usuario = username).all()
    ticket = Boletos.query.filter_by(usuario = username).first()
    return render_template('index.html', title = title, username = username, boletos = boletos, ticket = ticket)

@app.route('/registrar_entrada', methods = ['GET', 'POST'])
def registrar_entrada():
    nombre = session['username']
    usuario = User.query.filter_by(username = nombre).first()
    if request.method == 'POST':
        ticket = Boletos(usuario = nombre, hora_entrada = request.form['hora_entrada'], hora_salida = None, tarifa = 0, estatus = 'Pendiente', estacionamiento = usuario.estacionamiento)
        db.session.add(ticket)
        db.session.commit()
        success_message = 'Hora de entrada registrada éxitosamente! El código de su boleto es {}!'.format(ticket.idBoleto)
        flash((success_message,'success'))
        return render_template('alerta_entrada.html', ticket = ticket)
    else:
        return redirect(url_for('index'))

def calcular_precio(tiempo_mins):
    print("tiempo: ",tiempo_mins)
    nombre = session['username']
    datos_user = User.query.filter_by(username=nombre).first()
    tarifa = Tarifas.query.filter_by(estacionamiento=datos_user.estacionamiento).first()

    print("tiempo minutos",tiempo_mins)
    if tiempo_mins <= tarifa.tiempo_tol:
        total = 0.0
    elif tiempo_mins <= 120:
        total = tarifa.dos_horas
    else:
        horas_adicionales = (tiempo_mins - 120) / 60 
        total = tarifa.dos_horas + (horas_adicionales * tarifa.hora_extra)
    return total

@app.route('/registrar_salida', methods = ['GET', 'POST'])
def registrar_salida():
    nombre = session['username']
    variable = ""
    datos_user = User.query.filter_by(username = nombre).first()
    if request.method == 'POST':
        boleto = Boletos.query.filter_by(idBoleto = request.form['idBoleto']).first()
        print(nombre)
        if boleto is not None:
            if boleto.estatus == 'Pendiente':
                if boleto.usuario == nombre:

                    Boletos.query.filter_by(idBoleto = boleto.idBoleto).update({'hora_salida': request.form['hora_salida']})
                    db.session.commit()
                    hora_entrada = datetime.strptime(str(boleto.hora_entrada), '%Y-%m-%d %H:%M:%S')
                    hora_salida = datetime.strptime(str(boleto.hora_salida), '%Y-%m-%d %H:%M:%S')

                    tiempo = hora_salida - hora_entrada
                    #Tiempo convertido a minutos
                    tiempo_mins = tiempo.total_seconds() / 60

                    total_a_pagar = calcular_precio(tiempo_mins)

                    Boletos.query.filter_by(idBoleto = request.form['idBoleto']).update(dict(tarifa = total_a_pagar, estatus = 'Pagado'))
                    db.session.commit()
                    pago = Pagos(usuario = nombre, total_pago = total_a_pagar, estacionamiento = datos_user.estacionamiento)
                    db.session.add(pago)
                    db.session.commit()
                    variable = "Realizado"
                    flash(('Boleto pagado correctamente!','success'))
                else:
                    variable = "Caridad"
                    flash(('Te agradecemos que seas caritativo, pero no puedes pagar boletos de otras personas!','primary'))
            else:
                variable = "Pagado"
                total_a_pagar = 0
                success_message = 'El pago de este boleto ya se ha realizado!'
                flash((success_message,'warning'))
        else: 
            variable = "NoEncontrado"
            flash(('El boleto no se encuentra registrado!', 'danger')) 
    return render_template('alerta_salida.html', ticket = boleto, variable=variable)

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

@app.route('/ajax-login', methods=['POST'])
def ajax_login():
    print(request.form)
    username = request.form['username']
    response = {'status':200, 'username':username, 'id':1}
    return json.dumps(response)



if __name__ == '__main__':

    app.run(port=8000)
