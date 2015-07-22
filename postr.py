from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from werkzeug import check_password_hash, generate_password_hash
import werkzeug.security
from datetime import datetime

USER_FOLDER = 'user_data' # this is the world's most horrible thing, fix it later
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
app.config['UPLOAD_FOLDER'] = USER_FOLDER

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

class File(db.Model):
    """This is a file object"""
    __tablename__ = 'file'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(24))
    type = db.Column(db.String(50))

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', foreign_keys="File.author_id", backref=db.backref('files', lazy='dynamic'))

    def __init__(self, filename, author): # allowed_extensions
        self.filename = filename
        self.author = author
        self.post = post
    def __repr__(self):
        return '<File %r by %r>' % (self.filename, self.author)

    @classmethod
    def upload(cls, file, author):
        prefix,ext = file.filename.rsplit('.', 1) # if a file is uploaded with no extension then ur fuxked mate.
        if ext.lower() in cls.allowed_extensions:
            secure_filename = "%s.%s" % (werkzeug.security.pbkdf2_hex(prefix, keylen=32, salt=app.secret_key),ext)
            file.save(werkzeug.security.safe_join(app.config['UPLOAD_FOLDER'], secure_filename))
            file_model = cls(secure_filename, author)
            flash('File uploaded!')
            return file_model
        else:
            return "File extension is wack. You can upload %s" % cls.allowed_extensions
    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(id=id).first()
    @classmethod
    def get_by_author(cls, author=None):
        return cls.query.filter_by(author=author).all()
    __mapper_args__ = {
        'polymorphic_on':'type',
        'polymorphic_identity':'file'
    }


class Image(File):
    __tablename__ = 'image'
    allowed_extensions = {'png','jpg','gif','jpeg'}
    id = db.Column(db.Integer, db.ForeignKey('file.id'), primary_key=True)

    def __init__(self, filename, author):
        super(Image,self).__init__(filename, author)
        self.filename = filename

    __mapper_args__ = {
        'polymorphic_identity':'image'
    }

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), index=True, unique=True)
    password = db.Column(db.String(50))
    join_date = db.Column(db.DateTime)

    avatar_id = db.Column(db.Integer, db.ForeignKey('file.id'))
    avatar = db.relationship('File', foreign_keys="User.avatar_id")
    def __init__(self, username, password, join_date=None):
        self.username = username
        self.password = password
        self.join_date = ensure_date(join_date)

    # from doge
    @classmethod
    def get_by_username(cls, username):  
        return cls.query.filter_by(username=username).first()

    def __repr__(self):
        # usually <User: %s>, but it's in the dox...
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

    def __init__(self, message, author, recipient, message_date=None, ):
        self.message = message
        self.author = author
        self.recipient = recipient
        self.message_date = ensure_date(message_date)


    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    def __repr__(self):
        return'<Message: %r>' % self.message

class Attachment(db.Model):

    __tablename__ = 'attachment'
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

    post = db.relationship('Post', foreign_keys="Attachment.post_id", backref=db.backref('attachments', lazy='dynamic'))
    file = db.relationship('File', foreign_keys="Attachment.file_id", backref=db.backref('files', lazy='dynamic'))

    def __init__(self, post, file):

        self.post = post
        self.file = file

    def __repr__(self):
        return'<Attachment %r on %r>' % (self.file, self.post)

@app.before_request
def before_request():
    g.user_data = USER_FOLDER
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
                return redirect(url_for('dashboard', username=get_user.username))
                flash("ORIGHT YEH. Logged in as %s" % user_input)
        else:
            flash("Incorrect username or password.")
    return render_template('login.html', form=request.form)

@app.route('/<username>')
def dashboard(username):
    user = User.get_by_username(username)
    if user is None:
        return abort(404)
    else:
        images = user.files.order_by(desc(File.id))
        posts = user.messages.order_by(desc(Post.message_date))
        # user, rather than username
        return render_template('dashboard.html', user=user, user_images=images, posts=posts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # https://docs.python.org/3/library/html.html#html.escape
        new_user = User(request.form['register_username'], generate_password_hash(request.form['register_password'], method='pbkdf2:sha256'))
        db.session.add(new_user)
        db.session.commit()
        # escape here too. id do like username = html.escape(request.form[...])salt=app.secret_key
        flash("You can now log in as %s" % request.form['register_username'])
        return redirect(url_for('home'))

@app.route('/new/avatar', methods=['POST'])
@app.route('/new/avatar/<pid>', methods=['GET'])
def new_avatar(pid=None):
    def update_user_with_avatar():
        db.session.add(g.user)
        db.session.commit()
    upload = request.files.get('input_avatar' ,'')
    if upload:
        file = Image.upload(upload, g.user)
        db.session.add(file)
        db.session.commit()
        g.user.avatar = file
        update_user_with_avatar()
    else:
        file = Image.get_by_id(pid)
        g.user.avatar = file
        update_user_with_avatar()
    return redirect(url_for('dashboard', username=g.user.username))

@app.route('/<username>/post', methods=['POST'])
def post(username):  # post seems like a confusing name, because HTTP POST
    author = g.user
    recipient = User.get_by_username(username)
    # html escape PROBABLY doesnt matter here because jinja will handle it
    post = Post(request.form['input_message'], author, recipient)
    attachments = request.files.getlist('input_file')
    print(attachments)
    if post.message is not '':
        db.session.add(post)
        db.session.commit()
        if attachments[0]:
            for attachment in attachments:
                file = Image.upload(attachment, g.user)
                db.session.add(file)
                db.session.commit()
                attachment = Attachment(post, file)
                db.session.add(attachment)
                db.session.commit()
        flash('Thx!')  # why in the middle of add and commit?
    else:
        flash('Say something better')
    return redirect(url_for('dashboard', username=username))

@app.route('/post/<post_id>')
def single(post_id):
    post = Post.get_by_id(post_id)
    user = post.author
    return render_template('dashboard.html', user=user, posts=[post])

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

@app.route('/user_data/<filename>')
def user_data(filename):
    with app.open_resource('user_data/'+filename) as f:
        contents = f.read()
    return contents