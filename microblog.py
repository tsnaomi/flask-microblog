#!usr/bin/env Python

from datetime import datetime
from flask import (abort, flash, Flask, redirect, render_template, request,
                   session, url_for)
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.seasurf import SeaSurf
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flaskext.bcrypt import Bcrypt
from flask_mail import Mail, Message
from random import randint

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME='linguisticpythonista@gmail.com',
    MAIL_PASSWORD='',  # FILL OUT
    MAIL_DEFAULT_SENDER=('Blogette', 'linguisticpythonista@gmail.com'))

db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)
csrf = SeaSurf(app)
mail = Mail(app)
bcrypt = Bcrypt(app)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    body = db.Column(db.Text)
    pub_date = db.Column(db.DateTime)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'))

    def __init__(self, title, body):
        self.title = title
        self.body = body
        self.pub_date = datetime.utcnow()
        self.author_id = Author.query.filter_by(
            username=session['current_user']).first().id

    def __repr__(self):
        return 'POST: %r' % self.title


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(40), unique=True)
    username = db.Column(db.String(40), unique=True)
    password = db.Column(db.String(80))
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    def __init__(self, email, username, password):
        self.email = email
        self.username = username
        self.password = bcrypt.generate_password_hash(password)

    def __repr__(self):
        return 'AUTHOR: %r' % self.username


class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(32), unique=True)
    email = db.Column(db.String(40), unique=True)
    username = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(20))
    date = db.Column(db.DateTime)

    def __init__(self, email, username, password):
        self.key = str(int(randint(10**31, 10**32-1)))
        self.date = datetime.utcnow()
        self.email = email
        self.username = username
        self.password = password

    def __repr__(self):
        return 'REG_KEY: %r' % self.key


def read_posts():
    ''' Returns a list of the post objects in the database
        with the most recently created posts returned first. '''
    return Post.query.order_by(Post.pub_date.desc()).all()


def read_post(id):
    ''' Returns the post identified by 'id'. '''
    if Post.query.get(id):
        return Post.query.get(id)
    raise KeyError('Crap. No post at that ID.')


def write_post(title, body):
    ''' Creates a new post based on the title and text body supplied. '''
    if title and body:
        db.session.add(Post(title, body))
        db.session.commit()
    else:
        raise ValueError('Crap. You\'re missing something.')


def edit_post(id, title, body):
    ''' Commits edit to post. '''
    if title and body:
        Post.query.get(id).title, Post.query.get(id).body = title, body
        db.session.commit()
    else:
        raise ValueError('Crap. You\'re missing something.')


def delete_post(id):
    ''' Deletes post... '''
    if Post.query.get(id):
        db.session.delete(Post.query.get(id))
        db.session.commit()
    else:
        raise KeyError('Crap. No post to delete.')


def register(email, username, password):
    ''' Creates a registration object for an aspiring user. '''
    if email and username and password:
        registration = Registration(email, username, password)
        db.session.add(registration)
        db.session.commit()
        return registration
    raise ValueError('''Crap. You're missing something or the username is
                     already taken.''')


def create_author(username, password, email):
    ''' Creates user. '''
    db.session.add(Author(username, password, email))
    db.session.commit()


@app.route('/', methods=['GET', ])
def list_view():
    return render_template('lists.html', posts=read_posts())


@app.route('/post/<id>', methods=['GET', ])
def details_view(id):
    try:
        return render_template('details.html', post=read_post(id))
    except Exception:
        abort(404)


@app.route('/add', methods=['POST', 'GET'])
def add_view():
    if not session.get('current_user'):
        abort(401)
    if request.method == 'POST':
        try:
            write_post(request.form['title'], request.form['body'])
            return redirect(url_for('list_view'))
        except Exception:
            flash('Please provide both a title and body.')
    return render_template('add.html')


@app.route('/edit/<_id>', methods=['POST', 'GET'])
def edit_view(_id):
    try:
        if not session.get('current_user'):
            raise LookupError
        post, action = read_post(_id), '/edit/%s' % _id
        if post.author_id != Author.query.filter_by(
                username=session['current_user']).first().id:
            flash('403: This is not yours to edit.')
            return redirect(url_for('details_view', id=_id))
        if request.method == 'POST':
            edit_post(post.id, request.form['title'], request.form['body'])
            return redirect(url_for('details_view', id=_id))
    except KeyError:
        abort(404)
    except LookupError:
        abort(401)
    except ValueError:
        flash('Please provide both a title and body.')
    return render_template('edit.html', post=post, action=action)


@app.route('/delete/31415926/<id>', methods=['GET', ])
def delete_view(id):
    try:
        post = read_post(id)
        if not session.get('current_user'):
            raise LookupError
        if post.author_id != Author.query.filter_by(
                username=session['current_user']).first().id:
            flash('403: This is not yours to delete.')
            return redirect(url_for('details_view', id=id))
        delete_post(id)
    except KeyError:
        abort(404)
    except LookupError:
        abort(401)
    return redirect(url_for('list_view'))


@app.route('/login', methods=['POST', 'GET'])
def login_view():
    if session.get('current_user'):
        flash('You are already logged in as %s.' % session['current_user'])
        return redirect(url_for('list_view'))
    if request.method == 'POST':
        author = Author.query.filter_by(username=
                                        request.form['username']).first()
        password = request.form['password']
        if author is None or not bcrypt.check_password_hash(author.password,
                                                            password):
            flash('Invalid username or password.')
        else:
            session['current_user'] = author.username
            flash('You are now logged in as %s.' % session['current_user'])
            return redirect(url_for('list_view'))
    return render_template('login.html')


@app.route('/logout')
def logout_view():
    session.pop('current_user', None)
    flash('You have been logged out.')
    return redirect(url_for('list_view'))


@app.route('/register', methods=['POST', 'GET'])
def registration_view():
    if request.method == 'POST':
        try:
            author = register(request.form['email'], request.form['username'],
                              request.form['password'])
            body = '''Please proceed here to confirm Blogette account:\r\n
                      http://ec2-54-186-11-38.us-west-2.compute.amazonaws.com/confirmation/%s''' % author.key
            msg = Message(subject='Blogette Registration Confirmation',
                          body=body, recipients=[request.form['email']])
            mail.send(msg)
            flash('Check email for cofirmation link.')
            return redirect(url_for('login_view'))
        except ValueError:
            flash('Email or username already taken.')
        except Exception:
            flash('Something unfathomable went wrong.')
    return render_template('register.html')


@app.route('/confirmation/<key>', methods=['POST', 'GET'])
def confirmation_view(key):
    if Registration.query.filter_by(key=key).first() is not None:
        author = Registration.query.filter_by(key=key).first()
        create_author(author.email, author.username, author.password)
        flash('Registration confirmed! Welcome to Blogette.')
        return redirect(url_for('login_view'))
    abort(404)


@app.errorhandler(401)
def not_authenticated(e):
    flash('401: Log the fuck in.')
    return redirect(url_for('login_view'))


@app.errorhandler(404)
def page_not_found(e):
    flash('404: This page does not exist.')
    return render_template('layout.html')

if __name__ == '__main__':
    manager.run()
