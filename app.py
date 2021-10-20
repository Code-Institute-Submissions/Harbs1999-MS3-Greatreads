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
@app.route("/home")
def home():
    return render_template("index.html")


@app.route("/sign_up", methods=["GET", "POST"])
def sign_up():
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

                return redirect(url_for("profile", username=session["user"]))
            else:
                flash("Incorrect Username/Password")
                return redirect(url_for("login"))

        else:
            flash(Markup("Incorrect Username/Password <a href='{{ url_for('sign_up') }}'>Sign up here!</a>"))

    return render_template("login.html")


@app.route("/profile/<username>/<book_id>")
def profile(username, book_id):
    # Grab the current sessions username to display
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

        

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/get_books")
def get_books():
    books = mongo.db.books.find()
    return render_template("books.html", books=books)


@app.route("/book/<book_id>")
def book(book_id):
    books = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    return render_template("book.html", books=books, username=username)


@app.route("/add_book", methods=["GET", "POST"])
def add_book():
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
        return redirect(url_for('book'))
        
    return render_template("add_book.html")


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
            