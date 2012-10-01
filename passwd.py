# -*- coding: utf-8 -*-

import os
import uuid
import psycopg2
import smtplib

from bottle import Bottle, route, template, request, static_file, \
                   jinja2_template as template
from wtforms import Form, TextField, PasswordField, HiddenField, \
                    SubmitField, validators
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from sqlalchemy import create_engine, Column, Integer, String, \
                       DateTime, and_, ForeignKey
from sqlalchemy.ext.declarative import declarative_base 
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.orm.exc import NoResultFound
# UUID for PostgreSQL
from sqlalchemy.dialects.postgresql import UUID

##########
# Models #
##########
engine = create_engine("postgresql+psycopg2://svn_user:svn_pass@/svn_db?host=/var/run/postgresql")

Base = declarative_base()

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
    #token = Column(String, nullable=False)
    token = Column(UUID, nullable=False)
    ts = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))

    def __repr__(self):
        return "<Token('%s')>" % self.token

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

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

@route('/js/<filename>')
def js_static(filename):
	return static_file(filename, root=os.path.join(dirname, 'js'))

@route('/img/<filename>')
def img_static(filename):
	return static_file(filename, root=os.path.join(dirname, 'img'))

@route('/css/<filename>')
def css_static(filename):
	return static_file(filename, root=os.path.join(dirname, 'css'))

@route('/password_reset')
def password_reset_form():
    """
    Show the username form for reset password.
    """
    form = PasswordResetForm(request.forms)
    return template('password_reset_form', form=form)

@route('/password_reset', method='POST')
def password_reset():
    """
    Sending instructions to recover password to username email if exist in users's
    database 
    """
    form = PasswordResetForm(request.forms)
    if form.validate():
        # Checking if the username exist in user's database
        username = form.username.data
        session = Session()
        try:
            user = session.query(User).filter_by(username=username).one()
            session.commit()

            token = str(uuid.uuid4())
            user_token = Token(token=token, ts=datetime.now(), user_id=user.id)
            session.add(user_token)
            session.commit()

            # Sending email with instructions for recover password
            email_user = local_cfg["smtp_from"] 
            email_pass = local_cfg["smtp_pass"]
            subject = "Password reset"
			link = ''.join([local_cfg["site_url"], '/reset?username=%s&token=%s' % (username, token)])
            tpl = template('password_reset_email', link=link, username=user.full_name, site_team=local_cfg["site_team"])

            send_email(email_user, email_pass, user.email, subject, tpl)

            return template('password_reset_done')
        except NoResultFound, e:
            return template('password_reset_form', form=form, invalid=True)
    return template('password_reset_form', form=form)

@route('/reset')
def password_reset_confirm_form():
    """
    Show the form to recover password

    The querystring follow this pattern:
	/reset?username=$USERNAME&token=$TOKEN

    The token must exist in database and be valid (<1 day)
    """
    token = request.query.token
    username = request.query.username

    session = Session()
    try:
        token = session.query(Token).join(User).filter(and_(User.username==username,
                                                    Token.token==token)).one()
        
        session.commit()
        if datetime.now() <= token.ts + timedelta(days=1):
            form = SetPasswordForm(request.forms, username=username)
            return template('password_reset_confirm', form=form, error=False)
        else:
            return template('password_reset_confirm', error=True)
    except NoResultFound, e:
        return template('password_reset_confirm',  error=True)

@route('/reset', method='POST')
def password_reset_confirm():
    form = SetPasswordForm(request.forms)
    if form.validate():
        session = Session()
        try:
            user = session.query(User).filter_by(username=form.username.data).one()
            user.password = form.new_pass.data
            session.commit()

            # Email
            email_user = local_cfg["smtp_from"] 
            email_pass = local_cfg["smtp_pass"]
            subject = "Password reset"

            tpl = template('password_reset_complete_email', username=user.full_name, site_team=local_cfg["site_team"])
)

            send_email(email_user, email_pass, user.email, subject, tpl)

            return template('password_reset_complete')
        except NoResultFound, e:
            return template('password_reset_confirm', error=True)
    return template('password_reset_confirm', form=form, error=False)
