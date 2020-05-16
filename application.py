import os

from flask import Flask, session, flash, render_template, request, abort, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import csv
import jsonify
import json
import requests

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

key=os.getenv("API_KEY")
# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

app.static_folder = 'static'


@app.route("/")
def index():

    if not session.get('logged_in'):
        return render_template("index.html", message="Please Register/Login")
    else:
        return render_template("index.html", message="Hey  there !!!",title="Welcome")


@app.route("/register")
def register():
    return render_template("register.html",title="Register")


@app.route("/login")
def login():
    return render_template("login.html",title="Login")


@app.route("/register-details", methods=["POST"])
def register_details():
    email = request.form.get("email")
    password = request.form.get("password")
    age = request.form.get("age")

    if db.execute("SELECT * FROM users WHERE email=:email", {"email": email}).rowcount != 0:
        return render_template("error.html", message="Email already exist",title="Error")

    db.execute("INSERT INTO users (email,password,age) VALUES (:email,:password,:age) ",
               {"email": email, "password": password, "age": age})
    db.commit()
    return render_template("index.html", message="Successfully registered",title="Success")


@app.route("/login-details", methods=["POST"])
def login_details():
    email = request.form.get("email")
    password = request.form.get("password")

    user = db.execute("SELECT * FROM users WHERE email=:email AND password=:password",
                      {"email": email, "password": password}).fetchone()
    if not user:
        return render_template("error.html", message="wrong password",title="Error")

    else:
        session['logged_in'] = True
        print(user.id)
        session['user_id'] = user.id

        return redirect(url_for("search"))


@app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect(url_for("index"))


@app.route("/search/")
def search():
    return render_template("search.html", message="Search Books",title="Search")


# //Search form route

@app.route("/search-info", methods=["POST"])
def search_books():
    info = request.form.get("info")
    info = info.lower()
    books = db.execute(
        "SELECT * FROM books WHERE isbn LIKE '%{}%' OR LOWER (title) LIKE '%{}%' OR LOWER (author) LIKE '%{}%' LIMIT 10 ".format(
            info, info,
            info)).fetchall()

    if not books:
        return render_template("error.html", message="404 No Books Found",title="404")

    return render_template("books.html", books=books, message="Books Found", var=0,title="Books")


@app.route("/search-books/<int:book_id>")
def book_details(book_id):
    book = db.execute("SELECT * from books where id =:id", {"id": book_id}).fetchone()
    reviews = db.execute("SELECT * from reviews where book_id=:book_id LIMIT 5", {"book_id": book_id}).fetchall()
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": str(key), "isbns": book.isbn})
    review = res.json()

    session['book_id'] = book_id

    return render_template("bookDetails.html", message="Book Info", book=book, reviews=reviews,
                           apireview=review['books'][0],title="Books Info")


@app.route("/review", methods=["POST"])
def review():
    user_id = session['user_id']
    book_id = session['book_id']
    review = request.form.get("input")
    text_review = request.form.get("textReview")
    if db.execute("SELECT * FROM reviews WHERE user_id=:user_id AND book_id=:book_id",
                  {"user_id": user_id, "book_id": book_id}).rowcount != 0:
        return render_template("error.html", message="You have already reviewed this book",title="Error")
    else:

        db.execute(
            "Insert into reviews (review,book_id,text_review,user_id) VALUES (:review,:book_id,:text_review,:user_id)",
            {"review": review, "book_id": book_id, "text_review": text_review, "user_id": user_id})
        db.commit()

        return render_template("index.html",message="Review Added",title="Success")


@app.route("/api/<isbn>")
def api(isbn):
    book = db.execute("SELECT * from books where isbn =:isbn", {"isbn": isbn}).fetchone()
    books = db.execute("SELECT AVG(review), count(*) from reviews group by book_id=:book_id",
                       {"book_id": book.id}).fetchone()
    avg = str(books[0])
    rating = str(books[1])
    return json.dumps({
        "title": book.title, "author": book.author, "year": book.released_year, "isbn": book.isbn,
        "review_count": rating, "average_score": avg
    })


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
