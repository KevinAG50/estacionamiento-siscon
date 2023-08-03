from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'Usuarios'

    idUsuario = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(40))
    password = db.Column(db.String(200))
    estacionamiento = db.Column(db.ForeignKey('Estacionamientos.nombreE'))
    create_date = db.Column(db.DateTime, default=datetime.datetime.now)

    def __init__(self, username, email, password, estacionamiento):
        self.username = username
        self.email = email
        self.password = self.create_password(password)
        self.estacionamiento = estacionamiento

    def create_password(self, password):
        return generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password, password)


class Estacionamientos(db.Model):
    __tablename__ = 'Estacionamientos'

    idEstacionamiento = db.Column(db.Integer, primary_key=True)
    nombreE = db.Column(db.String(100), unique=True)
    capacidad = db.Column(db.Integer)
    codigo_postal = db.Column(db.Integer)

    def __init__(self, nombreE, capacidad, codigo_postal):
        self.nombreE = nombreE
        self.capacidad = capacidad
        self.codigo_postal = codigo_postal


class Tarifas(db.Model):
    __tablename__ = 'Tarifas'

    idTarifa = db.Column(db.Integer, primary_key=True)
    tiempo_tol = db.Column(db.Integer)
    dos_horas = db.Column(db.Integer)
    hora_extra = db.Column(db.Integer)
    pension_dia = db.Column(db.Integer)
    pension_semana = db.Column(db.Integer)
    pension_mes = db.Column(db.Integer)
    estacionamiento = db.Column(db.ForeignKey('Estacionamientos.nombreE'))
    
    def __init__(self, tiempo_tol, dos_horas, hora_extra, pension_dia, pension_mes, pension_semana, estacionamiento):
        self.tiempo_tol = tiempo_tol
        self.dos_horas = dos_horas
        self.hora_extra = hora_extra
        self.pension_dia = pension_dia
        self.pension_semana = pension_semana
        self.pension_mes = pension_mes 
        self.estacionamiento = estacionamiento


class Boletos(db.Model):
    __tablename__ = 'Boletos'

    idBoleto = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50))
    hora_entrada = db.Column(db.DateTime)
    hora_salida = db.Column(db.DateTime)
    tarifa = db.Column(db.Integer)
    estatus = db.Column(db.String(50))
    estacionamiento = db.Column(db.ForeignKey('Estacionamientos.nombreE'))

    def __init__(self, usuario, hora_entrada, hora_salida, tarifa, estatus, estacionamiento):
        self.usuario = usuario
        self.hora_entrada = hora_entrada
        self.hora_salida = hora_salida
        self.tarifa = tarifa
        self.estatus = estatus
        self.estacionamiento = estacionamiento


class Pagos(db.Model):
    __tablename__ = 'Pagos'

    idPago = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50))
    total_pago = db.Column(db.Integer)
    estacionamiento = db.Column(db.String(50), db.ForeignKey('Estacionamientos.nombreE'))

    def __init__(self, usuario, total_pago, estacionamiento):
        self.usuario = usuario
        self.total_pago = total_pago
        self.estacionamiento = estacionamiento