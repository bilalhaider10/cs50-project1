import os

from flask import Flask, session, flash, render_template, request, abort, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import csv
import requests

res = requests.get("https://www.goodreads.com/book/review_counts.json",
                   params={"key": "y2jcOE9RMX0cbEowqFDMbw", "isbns": "9781632168146"})

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
app.static_folder = 'static'


f = open("books.csv")
reader = csv.reader(f)
for isbn, title, author, released_year in reader:
    db.execute("INSERT INTO books (isbn, title, author, released_year) VALUES (:isbn, :title, :author,:released_year)",
               {"isbn": isbn,"title":title, "author": author, "released_year": released_year})
    print(f"Added {isbn} ")
db.commit()

@app.route("/")
def index():
    if not session.get('logged_in'):
        return render_template("index.html", message="Please Register/Login")
    else:
        return render_template("index.html", message="Hi")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/register-details", methods=["POST"])
def register_details():
    email = request.form.get("email")
    password = request.form.get("password")
    age = request.form.get("age")

    if db.execute("SELECT * FROM users WHERE email=:email", {"email": email}).rowcount != 0:
        return render_template("error.html", message="Email already exist")

    db.execute("INSERT INTO users (email,password,age) VALUES (:email,:password,:age) ",
               {"email": email, "password": password, "age": age})
    db.commit()
    return render_template("index.html", message="Successfully registered")


@app.route("/login-details", methods=["POST"])
def login_details():
    email = request.form.get("email")
    password = request.form.get("password")

    if db.execute("SELECT * FROM users WHERE email=:email AND password=:password",
                  {"email": email, "password": password}).rowcount != 0:
        session['logged_in'] = True
        return redirect(url_for("index"))
    else:

        return render_template("error.html", message="wrong password")


@app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    main()
