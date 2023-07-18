from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, logout_user
from forms import LoginForm, RegisterForm, CreatePostForm


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
bootstrap = Bootstrap(app)

##Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


##Cafe TABLE Configuration
class Cafe(db.Model):
    __tablename__ = "cafes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)


#Create the User Table
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))

# db.create_all()


@app.route("/")
def home():
    query = request.args.get('search')
    print(query)
    if query is None:
        all_cafes = Cafe.query.order_by(Cafe.id).all()
    elif query == "":
        all_cafes = Cafe.query.order_by(Cafe.id).all()
    else:
        all_cafes = Cafe.query.filter_by(location=query).all()
        if all_cafes:
            return render_template("index.html", cafes=all_cafes)
        else:
            flash("Sorry, we don't have a cafe at that location.")
            return render_template("index.html", cafes=all_cafes)
    return render_template("index.html", cafes=all_cafes)


# Register new users into the User database
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        # If user's email already exists
        if User.query.filter_by(email=form.email.data).first():
            # Send flash messsage
            flash("You've already signed up with that email, log in instead!")
            # Redirect to /login route.
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("register.html", form=form)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()

        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))

    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/new-post", methods=["GET", "POST"])
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_cafe = Cafe(
            name=form.name.data,
            map_url=form.map_url.data,
            img_url=form.img_url.data,
            location=form.location.data,
            has_sockets=form.has_sockets.data,
            has_toilet=form.has_toilet.data,
            has_wifi=form.has_wifi.data,
            can_take_calls=form.can_take_calls.data,
            seats=form.seats.data,
            coffee_price=form.coffee_price.data,
        )
        db.session.add(new_cafe)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("add_cafe.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    post = Cafe.query.get(post_id)
    edit_form = CreatePostForm(
        name=post.name,
        map_url=post.map_url,
        img_url=post.img_url,
        location=post.location,
        has_sockets=post.has_sockets,
        has_toilet=post.has_toilet,
        has_wifi=post.has_wifi,
        can_take_calls=post.can_take_calls,
        seats=post.seats,
        coffee_price=post.coffee_price,
    )
    if edit_form.validate_on_submit():
        post.name = edit_form.name.data
        post.map_url = edit_form.map_url.data
        post.img_url = edit_form.img_url.data
        post.location = edit_form.location.data
        post.has_sockets = edit_form.has_sockets.data
        post.has_toilet = edit_form.has_toilet.data
        post.has_wifi = edit_form.has_wifi.data
        post.can_take_calls = edit_form.can_take_calls.data
        post.seats = edit_form.seats.data
        post.coffee_price = edit_form.coffee_price.data
        db.session.commit()
        return redirect(url_for("home", post_id=post.id))

    return render_template("add_cafe.html", form=edit_form)


@app.route("/report-closed/<int:cafe_id>", methods=["DELETE", 'GET', 'POST'])
def delete_cafe(cafe_id):
    # api_key = request.args.get("api-key")
    # if api_key == "TopSecretAPIKey":
    cafe = Cafe.query.get(cafe_id)
    if cafe:
        db.session.delete(cafe)
        db.session.commit()
        return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)