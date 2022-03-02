import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for, Markup)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/index", methods=["GET", "POST"])
def index():
    """ Home page, recommended books """
    featured = mongo.db.featured.find_one()

    return render_template("index.html", featured=featured)


@app.route("/edit_featured", methods=["GET", "POST"])
def edit_featured():
    """ Edit home page recommended book """
    if request.method == "POST":
        book_details = {
            "book_cover": request.form.get("book_cover"),
            "book_title": request.form.get("book_title"),
            "book_author": request.form.get("book_author"),
            "book_desc": request.form.get("book_desc"),
            "user": session["user"]
        }

        featured = mongo.db.featured.find_one()
        mongo.db.featured.update(featured, book_details)
        flash("Feature Updated!")
        redirect(url_for('index'))

    return render_template("edit_featured") 


@app.route("/sign_up", methods=["GET", "POST"])
def sign_up():
    """ Sign up page """
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("sign_up"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # user 'session' cookie 
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("sign_up.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """ Login page """
    if request.method == "POST":
        # Does username exist in the database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # Check to see if password matches username that has been inputted
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(request.form.get("username")))

                return redirect(url_for("index", username=session["user"]))
            else:
                flash("Incorrect Username/Password")
                return redirect(url_for("login"))

        else:
            flash(Markup("Incorrect Username/Password <a href='{{ url_for('sign_up') }}'>Sign up here!</a>"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    """ Users profile page """
    books = mongo.db.books.find()
    # Grab the current sessions username to display
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username, books=books)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    """ logout functionality """
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/get_books")
def get_books():
    """ Browse books page """
    books = mongo.db.books.find()
    return render_template("books.html", books=books)


@app.route("/book/<book_id>")
def book(book_id):
    """ Individual books """
    books = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    reviews = mongo.db.reviews.find()

    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    return render_template("book.html", books=books, username=username, reviews=reviews)


@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    """ Add book form """
    if request.method == "POST":
        book_details = {
            "book_cover": request.form.get("book_cover"),
            "book_title": request.form.get("book_title"),
            "book_author": request.form.get("book_author"),
            "book_desc": request.form.get("book_desc"),
            "review": request.form.get("review"),
            "user": session["user"]
        }
        mongo.db.books.insert_one(book_details)
        flash("Your book has been added!")
        return redirect(url_for('get_books'))

    return render_template("add_book.html")


@app.route("/add_review", methods=["GET", "POST"])
def add_review(): 
    """ Add review form """
    if request.method == "POST":
        review_book = {
            "review": request.form.get("review"),
            "user": session["user"]
        }
        mongo.db.reviews.insert_one(review_book)
        flash("Review Added!")
        return redirect(url_for('get_books'))

    return render_template("add_review.html")


@app.route("/edit_book/<book_id>", methods=["GET", "POST"])
def edit_book(book_id):
    """ Edit book form """
    if request.method == "POST":
        book_details = {
            "book_cover": request.form.get("book_cover"),
            "book_title": request.form.get("book_title"),
            "book_author": request.form.get("book_author"),
            "book_desc": request.form.get("book_desc"),
            "review": request.form.get("review"),
            "user": session["user"]
        }
        mongo.db.books.update({"_id": ObjectId(book_id)}, book_details)
        flash("Book Updated!")
        return redirect(url_for("get_books"))

    books = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    return render_template("edit_book.html", books=books)


@app.route("/delete_book/<book_id>")
def delete_book(book_id):
    """ Delete book functionality """
    mongo.db.books.remove({"_id": ObjectId(book_id)})
    flash("Book Deleted.")
    return redirect(url_for("get_books"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)
