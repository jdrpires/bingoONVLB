from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class RegisterForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField("E-mail", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField(
        "Senha",
        validators=[DataRequired(), Length(min=8, max=128)],
    )
    password_confirmation = PasswordField(
        "Confirme a senha",
        validators=[
            DataRequired(),
            EqualTo("password", message="As senhas precisam ser iguais."),
        ],
    )
    submit = SubmitField("Criar conta")


class LoginForm(FlaskForm):
    email = StringField("E-mail", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Senha", validators=[DataRequired()])
    submit = SubmitField("Entrar")


class BingoForm(FlaskForm):
    name = StringField(
        "Nome do bingo",
        validators=[DataRequired(), Length(min=2, max=120)],
    )
    submit = SubmitField("Criar bingo")
