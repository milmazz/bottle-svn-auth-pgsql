# -*- coding: utf-8 -*-

import os
import uuid
import psycopg2
import smtplib

from bottle import Bottle, request, static_file, \
                   jinja2_template as template
from bottle.ext import sqlalchemy
from wtforms import Form, TextField, PasswordField, HiddenField, \
                    SubmitField, validators
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from sqlalchemy import create_engine, Column, Integer, String, \
                       DateTime, Text, and_, ForeignKey
from sqlalchemy.ext.declarative import declarative_base 
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.exc import NoResultFound
# UUID for PostgreSQL
from sqlalchemy.dialects.postgresql import UUID, INET

##########
# Models #
##########
Base = declarative_base()
engine = create_engine("postgresql+psycopg2://svn_user:svn_pass@/subversion")

app = Bottle()
plugin = sqlalchemy.Plugin(
    engine,
    Base.metadata,
    keyword='db',
    create=True,
    commit=True,
    use_kwargs=False
)

app.install(plugin)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(32), nullable=False, )
    full_name = Column(String(64))
    email = Column(String(64))
    password = Column(String(64))

    tokens = relationship("Token", order_by="Token.id", backref="users",
                          lazy="dynamic")

    def __repr__(self):
        return "<User('%s','%s','%s','%s')>" % (self.username, self.full_name,
                                                self.email, self.password)


class Token(Base):
    __tablename__ = 'tokens'

    id = Column(Integer, primary_key=True)
    token = Column(UUID, nullable=False)
    ts = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))

    def __repr__(self):
        return "<Token('%s')>" % self.token


class Group(Base):
    __tablename__ = 'group'
    
    username = Column(String(32), primary_key=True)
    member_of = Column(String(64))


class Log(Base):
    __tablename__ = 'log'

    id = Column(Integer, primary_key=True)
    uname = Column(String(32))
    ts = Column(DateTime)
    uri = Column(Text())
    ip = Column(INET)

#########
# Forms #
#########
class PasswordResetForm(Form):
    """
    Model form username form
    """
    username = TextField('Username', [
        validators.Length(min=6, max=60),
        validators.Required()
    ])
    submit = SubmitField('Reset my password')


class SetPasswordForm(Form):
    """
    Model form password & verify password form
    """
    username = HiddenField('username')
    new_pass = PasswordField('New password', [
        validators.Required(),
        validators.Length(min=6),
        validators.EqualTo('confirm_pass', 'Passwords must match')

        ])
    confirm_pass = PasswordField('Confirm password')
    submit = SubmitField('Change my password')

#########
# Utils #
#########
def send_email(user, passwd, recipient, subject, msg):
    """
    Send an email trought GMail

    user: The GMail username, as a string
    passwd: The GMail password, as a string
    recipient: The email address to send the message
    subject: The email subject
    msg: The message
    """
    # Initialize SMTP Server
    session = smtplib.SMTP('smtp.gmail.com', 587)
    session.starttls()
    session.login(user, passwd)

    # Sending email
    message = MIMEText(msg, _charset='utf-8')
    message['Subject'] = subject
    message['From'] = user
    message['To'] = recipient

    session.sendmail(user, recipient, message.as_string())
    session.quit()

#############
# CONF SMTP #
#############
local_cfg = {
    "smtp_from": "noreply@example.com",
    "smtp_pass": "noreply_pass", 
    "site_url": "http://recover.example.com",
    "site_team": "Company Name"
}

################
# Static files #
################
dirname = os.path.dirname(__file__)

@app.route('/js/<filename>')
def js_static(filename):
	return static_file(filename, root=os.path.join(dirname, 'js'))

@app.route('/img/<filename>')
def img_static(filename):
	return static_file(filename, root=os.path.join(dirname, 'img'))

@app.route('/css/<filename>')
def css_static(filename):
	return static_file(filename, root=os.path.join(dirname, 'css'))

@app.route('/password_reset')
def password_reset_form():
    """
    Show the username form for reset password.
    """
    form = PasswordResetForm(request.forms)
    return template('password_reset_form', form=form)

@app.route('/password_reset', method='POST')
def password_reset(db):
    """
    Sending instructions to recover password to username email
    if exist in users's database 
    """
    form = PasswordResetForm(request.forms)
    if form.validate():
        # Checking if the username exist in user's database
        username = form.username.data
        try:
            user = db.query(User).filter_by(username=username).one()

            token = str(uuid.uuid4())
            user_token = Token(token=token, ts=datetime.now(), user_id=user.id)
            db.add(user_token)

            # Sending email with instructions for recover password
            email_user = local_cfg["smtp_from"] 
            email_pass = local_cfg["smtp_pass"]
            subject = "Password reset"
            link = ''.join([local_cfg["site_url"], '/reset?username=%s&token=%s' % (username, token)])
            tpl = template('password_reset_email', link=link, username=user.full_name,
                            site_team=local_cfg["site_team"])

            send_email(email_user, email_pass, user.email, subject, tpl)

            return template('password_reset_done')
        except NoResultFound, e:
            return template('password_reset_form', form=form, invalid=True)
    return template('password_reset_form', form=form)

@app.route('/reset')
def password_reset_confirm_form(db):
    """
    Show the form to recover password

    The querystring follow this pattern:
	/reset?username=$USERNAME&token=$TOKEN

    The token must exist in database and be valid (<1 day)
    """
    try:
        username = request.query.username
        token = uuid.UUID(request.query.token)

        token = db.query(Token).join(User).filter(and_(User.username==username,
                                                    Token.token==str(token))).one()
        
        if datetime.now() <= token.ts + timedelta(days=1):
            form = SetPasswordForm(request.forms, username=username)
            return template('password_reset_confirm', form=form, error=False)
        else:
            return template('password_reset_confirm', error=True)
    except ValueError, e:
        return template('password_reset_confirm', error=True)
    except NoResultFound, e:
        return template('password_reset_confirm',  error=True)

@app.route('/reset', method='POST')
def password_reset_confirm(db):
    form = SetPasswordForm(request.forms)
    if form.validate():
        try:
            user = db.query(User).filter_by(username=form.username.data).one()
            user.password = form.new_pass.data

            # Email
            email_user = local_cfg["smtp_from"] 
            email_pass = local_cfg["smtp_pass"]
            subject = "Password reset"

            tpl = template('password_reset_complete_email', username=user.full_name,
                            site_team=local_cfg["site_team"])

            send_email(email_user, email_pass, user.email, subject, tpl)

            return template('password_reset_complete')
        except NoResultFound, e:
            return template('password_reset_confirm', error=True)
    return template('password_reset_confirm', form=form, error=False)
