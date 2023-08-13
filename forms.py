from marshmallow import validates
from wtforms import Form, StringField, TextAreaField, PasswordField, HiddenField, validators
from wtforms.fields import EmailField, IntegerField, DateTimeField
from models import User, Estacionamientos


def lenght_honeypot(form, field):
    if len(field.data) > 0:
        raise validators.ValidationError('El campo debe estar vacio')

class CommentForm(Form):
    comment = TextAreaField('Comentario')
    honeypot = HiddenField('',[lenght_honeypot])

class LoginForm(Form):
    username = StringField(
        "Username",
        [validators.length(min = 4, max = 25), validators.DataRequired()],
    )
    password = PasswordField('Password', [validators.DataRequired()])


class usersForm(Form):
    username = StringField(
        "username",
        [validators.length(min = 4, max = 25), validators.DataRequired()],
    )
    email = EmailField(
        "Correo electronico",
        [validators.length(min = 10, max = 50), validators.DataRequired()],
    )
    password = PasswordField('Contraseña', [
        validators.DataRequired(),
        validators.Length(min=8, max=200, message='La contraseña debe tener entre 8 y 50 caracteres'),
        validators.Regexp(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$',
                          message='La contraseña debe contener al menos una letra mayúscula, una letra minúscula, un número y un carácter especial')
    ])
    estacionamiento = StringField('estacionamiento',
        [validators.length(min = 7, max = 25), validators.DataRequired()
    ])

    @validates('username')
    def validate_username(self, field):
        username = field.data
        user = User.query.filter_by(username = username).first()
        if user is not None:
            raise validators.ValidationError('El usuario ya se encuentra registrado!')
        
    @validates('email')
    def validate_email(self, field):
        email = field.data
        email = User.query.filter_by(email = email).first()
        if email is not None:
            raise validators.ValidationError('El correo electrónico ya se ha utilizado!')
        

class EstacionamientoForm(Form):
    nombreE = StringField('nombreE',
        [validators.length(min = 7, max = 25), validators.DataRequired()
    ])
    capacidad = IntegerField(
        'capacidad', 
        [validators.NumberRange(min=1, max=9999), validators.data_required()
    ])
    codigo_postal = IntegerField('codigo_postal',
        [validators.NumberRange(min=1000, max=999998), validators.data_required()
    ])

    def validate_nombreE(form,field):
        estacionamiento = field.data
        nombreE = Estacionamientos.query.filter_by(nombreE = estacionamiento).first()
        if nombreE is not None:
            raise validators.ValidationError('El estacionamiento ya se encuentra registrado!')


class tarifasForm(Form):
    tiempo_tol = IntegerField(
        'tiempo_tol', 
        [validators.NumberRange(min=1, max=9999), validators.data_required()
    ])
    dos_horas = IntegerField(
        'dos_horas', 
        [validators.NumberRange(min=1, max=9999), validators.data_required()
    ])
    hora_extra = IntegerField(
        'hora_extra', 
        [validators.NumberRange(min=1, max=9999), validators.data_required()
    ])
    estacionamiento = StringField('estacionamiento',
        [validators.length(min=7, max=25),validators.DataRequired()
    ])


class registrosForm(Form):
    estacionamiento = StringField('estacionamiento',
        [validators.length(min = 7, max = 25), validators.DataRequired()
    ])

