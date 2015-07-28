from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, safe_join, send_from_directory
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.mail import Mail, Message
from sqlalchemy import desc
from werkzeug import check_password_hash, generate_password_hash
import werkzeug.security
from datetime import datetime
import base64
import urllib.request
import uuid

USER_FOLDER = 'user_data' # this is the world's most horrible thing, fix it later
TEMP_FOLDER = 'user_temp'

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



app = Flask(__name__, static_folder='static')


app.secret_key = 'jEw9iS6A3qUeg4oYl7Nel0rud2ceFf2anS4oT6vO9hiv1p'
# space between variable and square brack isnt a good idea
app.config.from_pyfile('mail.cfg')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test2.db'
app.config['UPLOAD_FOLDER'] = USER_FOLDER
app.config['TEMP_FOLDER'] = TEMP_FOLDER

mail = Mail(app)
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

    def make_from_base_64(data):
        secure_filename = werkzeug.security.pbkdf2_hex(data, keylen=4, salt=app.secret_key) + '.png'
        with open(werkzeug.security.safe_join(app.config['TEMP_FOLDER'], secure_filename), 'wb') as f:
            imgdata = urllib.request.url2pathname(data)
            decoded = base64.b64decode(imgdata)
            f.write(decoded)
        return request.files.get(f.name)

    @classmethod
    def upload_from_base_64_data(cls, imgdata, author):
        secure_filename = "%s.png" % (werkzeug.security.pbkdf2_hex(imgdata, keylen=32, salt=app.secret_key))
        with open(werkzeug.security.safe_join(app.config['UPLOAD_FOLDER'], secure_filename), 'wb') as f:
            imgdata = urllib.request.url2pathname(imgdata)
            decoded = base64.b64decode(imgdata)
            f.write(decoded)
        file_model = cls(secure_filename, author)
        return file_model
   
    @classmethod
    def upload(cls, file, author):
        prefix,ext = file.filename.rsplit('.', 1) # if a file is uploaded with no extension then ur fuxked mate.
        if ext.lower() in cls.allowed_extensions:
            secure_filename = "%s.%s" % (werkzeug.security.pbkdf2_hex(prefix, keylen=32, salt=app.secret_key),ext)
            file.save(werkzeug.security.safe_join(app.config['UPLOAD_FOLDER'], secure_filename))
            file_model = cls(secure_filename, author)
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
    email = db.Column(db.String(0), index=True, unique=True)
    verified = db.Column(db.Boolean)
    verification_code = db.Column(db.String(40))
    join_date = db.Column(db.DateTime)

    avatar_id = db.Column(db.Integer, db.ForeignKey('file.id'))
    avatar = db.relationship('File', foreign_keys="User.avatar_id")

    def __init__(self, username, password, email, verification_code=None, join_date=None, verified=0):
        self.username = username
        self.password = password
        self.email = email
        self.verification_code = str(uuid.uuid4().hex)
        self.join_date = ensure_date(join_date)
        self.verified = verified

    def verify(self, email, code):
        pass

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
    if g.user:
        return redirect(url_for('dashboard', username=g.user.username))
    if request.method == 'POST':
        user_input = request.form.get('username', '')
        user_input_pass = request.form.get('password', '')
        if user_input is not None:
            get_user = User.get_by_username(user_input)
            print(get_user)
            login_ok = (check_password_hash(get_user.password, user_input_pass)) and get_user.verified is True
            print(get_user.verified)
            if login_ok:
                session['username'] = user_input
                flash("ORIGHT YEH. Logged in as %s" % user_input)
                return redirect(url_for('dashboard', username=get_user.username))

            elif get_user.verified is False:
                print('MATE CMON')
                flash("You need to confirm your email…")
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
        posts = user.messages.order_by(desc(Post.message_date))[:8]
        # user, rather than username
        return render_template('dashboard.html', user=user, user_images=images, posts=posts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # https://docs.python.org/3/library/html.html#html.escape
        new_user = User(request.form['register_username'],
                        generate_password_hash(request.form['register_password'],method='pbkdf2:sha256'),
                        request.form['register_email']
                        )
        db.session.add(new_user)
        db.session.commit()
        # escape here too. id do like username = html.escape(request.form[...])salt=app.secret_key
        flash("An email has been sent to %s — You need to verify before signing in" % new_user.email )
        return redirect(url_for('home'))

@app.route('/avatar', methods=['GET'])
def new_avatar(id=None):
    def update_user_with_avatar():
        db.session.add(g.user)
        db.session.commit()

    file = Image.get_by_id(request.args.get('id', ''))
    g.user.avatar = file
    update_user_with_avatar()
    flash('Avatar changed!')
    return redirect(url_for('dashboard', username=g.user.username))

@app.route('/<username>/post', methods=['POST'])
def post(username):  # post seems like a confusing name, because HTTP POST
    author = g.user
    recipient = User.get_by_username(username)
    # html escape PROBABLY doesnt matter here because jinja will handle it
    post = Post(request.form['input_message'], author, recipient)
    attachments = request.files.getlist('input_file')
    input_img_data = request.form['image_data']
    if post.message is not '':
        db.session.add(post)
        db.session.commit()
        if input_img_data is not '':
            file = Image.upload_from_base_64_data(input_img_data, g.user) # Hhhmmmm???
            db.session.add(file)
            db.session.commit()
            attachment = Attachment(post, file)
            db.session.add(attachment)
            db.session.commit()
            # file = Image.make_from_base_64(input_img_data)
            print(file)
        if attachments[0]:
            for attachment in attachments:
                file = Image.upload(attachment, g.user)
                db.session.add(file)
                db.session.commit()
                attachment = Attachment(post, file)
                db.session.add(attachment)
                db.session.commit()
        flash('Thx!')  
    else:
        flash('Say something better')
    return redirect(url_for('dashboard', username=username))

@app.route('/<author>/post/<post_id>')
def single(post_id, author):
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

@app.route('/'+app.config['UPLOAD_FOLDER']+'/<filename>')
def get_user_data(filename):
    with app.open_resource(safe_join(app.config['UPLOAD_FOLDER'], filename)) as f:
        return f.read()

@app.route('/'+app.config['TEMP_FOLDER']+'/<filename>')
def get_temp_data(filename):
    with app.open_resource(safe_join(app.config['TEMP_FOLDER'], filename)) as f:
        return f.read()

@app.route('/glitch')
def glitch():
    return render_template('glitch.html')

@app.route('/mail', methods=['GET'])
def mail():
    # http://localhost:5000/mail?confirm=blah@blah.com&code=12314823812038129381208319

    if request.method == 'GET':
        email_get = request.args.get('confirm')
        code_get = request.args.get('code')

        if code_get:
            flash('Email Confirmed')
            return redirect(url_for('home'))

    # msg = Message("Hello",sender="from@postr.com", recipients=["test@test.test"])
    # mail.send(msg)
    return email_get
