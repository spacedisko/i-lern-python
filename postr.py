from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from werkzeug import generate_password_hash, check_password_hash
from datetime import datetime


# imports are usually done in:
# import python-builtin
#
# from python-builtin import bit, thing  # alpha ordering
#
# import third-party
#
# import your-own

# multi line imports like:
# from flask import (abort,
#                    flash,
#                    Flask,
#                    g,
#                    redirect,
#                    render_template,
#                    request,
#                    session,
#                    url_for,
#                    )


app = Flask(__name__)
app.secret_key = 'jEw9iS6A3qUeg4oYl7Nel0rud2ceFf2anS4oT6vO9hiv1p'
# space between variable and square brack isnt a good idea
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test2.db'
db = SQLAlchemy(app)

@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    db.drop_all()
    db.create_all()
    # think about when you use ' vs " and stick to it
    # i use " for output that a user sees. some people
    # use " to indicate a string that has variables in it
    # (eg like a format string)
    # also do you know about the logging module?
    print("Initialized the database.")

def ensure_date(date):
    if date is None:
        return datetime.utcnow()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), index=True, unique=True)
    password = db.Column(db.String(50))
    join_date = db.Column(db.DateTime)

    def __init__(self, username, password, join_date=None):
        self.username = username
        self.password = password
        self.join_date = ensure_date(join_date)

    # from doge
    @classmethod
    def get_by_username(cls, username):  
        return cls.query.filter_by(username=username).first()

    def __repr__(self):
        # usually <User: %s>
        return '<User %r>' % self.username

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    message = db.Column(db.String(140))
    message_date = db.Column(db.DateTime)

    # oh do you really need to do this in sqlalchemy
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    author = db.relationship('User', foreign_keys="Post.author_id", backref=db.backref('posts', lazy='dynamic'))
    recipient = db.relationship('User', foreign_keys="Post.recipient_id", backref=db.backref('messages', lazy='dynamic'))

    def __init__(self, message, author, recipient, message_date=None):
        self.message = message
        self.author = author
        self.recipient = recipient
        # might be worth splitting this into a function since youve
        # used it twice. something like ensure_date(date)
        self.message_date = ensure_date(message_date)

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    def __repr__(self):
        return'<Message: %r>' % self.message

@app.before_request
def before_request():
    g.user = None
    try:
        g.user = User.query.filter_by(username=session['username']).first()
    except KeyError:
        pass


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        user_input = request.form.get('username', '')
        user_input_pass = request.form.get('password', '')
        if user_input is not None:
            get_user = User.get_by_username(user_input)
            login_ok = (check_password_hash(get_user.password, user_input_pass))
            if login_ok:
                session['username'] = user_input
                return redirect(url_for('dashboard', username=user_input))
                flash("ORIGHT YEH. Logged in as %s" % user_input)
        else:
            flash("Incorrect username or password.")
    return render_template('test.html', form=request.form)

@app.route('/<username>')
def dashboard(username):
    users = User.query.all()
    user = User.get_by_username(username)
    # "is" is better than == (ignatius fixed this now :3 ok)
    if user is None:
        return abort(404)
    else:
        posts = user.messages.order_by(desc(Post.message_date))
        # user, rather than username
        return render_template('dashboard.html', username=user, posts=posts, users=users)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # https://docs.python.org/3/library/html.html#html.escape
        new_user = User(request.form['register_username'], generate_password_hash(request.form['register_password'], method='pbkdf2:sha256', salt_length=8))
        db.session.add(new_user)
        db.session.commit()
        # escape here too. id do like username = html.escape(request.form[...])
        flash("You can now log in as %s" % request.form['register_username'])
        return redirect(url_for('home'))

@app.route('/<username>/post', methods=['POST'])
def post(username):  # post seems like a confusing name, because HTTP POST
    author = g.user
    recipient = User.get_by_username(username)
    # html escape PROBABLY doesnt matter here because jinja will handle it
    post = Post(request.form['input_message'], author, recipient)
    if post.message is not '':
        db.session.add(post)
        db.session.commit()
        flash('Thx!')  # why in the middle of add and commit?
    else:
        flash('Say something better')
    return redirect(url_for('dashboard', username=username))

@app.route('/post/<post_id>')
def single(post_id):
    post = Post.get_by_id(post_id)
    user = post.author
    return render_template('dashboard.html', username=user, posts=[post])

@app.route('/post/<post_id>/delete')
def delete_post(post_id):
    post = Post.get_by_id(post_id)
    if post.recipient_id is g.user.id:
        db.session.delete(post)
        db.session.commit()
        flash("Post deleted")
    else:
        flash("Can't delete it")
    return redirect(url_for('dashboard', username=post.recipient.username))

@app.route('/<username>/delete')
def delete_user(username):
    user = User.get_by_username(username)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted")
    return redirect(url_for('dashboard', username=post.recipient.username))

@app.route('/logout')
def logout():
    flash('Logged out')
    session.pop('username', None)
    return redirect(url_for('home'))