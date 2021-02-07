# Zadaća 21.1: kopiram s predavanja i dodajem Fake Delete
# Zadaća 21.2: Dodajem Edit password opciju

import random
import uuid
import hashlib
from flask import Flask, render_template, request, make_response, redirect, url_for
from models import User, db


app = Flask(__name__)
db.create_all()


@app.route("/", methods=["GET"])
def index():
    session_token = request.cookies.get("session_token")

    if session_token:
        user = db.query(User).filter_by(session_token=session_token).first()
    else:
        user = None

    return render_template("index.html", user=user)


@app.route("/login", methods=["POST"])
def login():
    name = request.form.get("user-name")
    email = request.form.get("user-email")
    password = request.form.get("user-password")

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # create a secret number
    secret_number = random.randint(1, 30)

    # see if user already exists
    user = db.query(User).filter_by(email=email).first()

    if not user:
        # create a User object
        user = User(name=name, email=email, secret_number=secret_number, password=hashed_password)

        # save the user object into a database
        db.add(user)
        db.commit()

    if hashed_password != user.password:
        return "Wrong password..go back and try again!"
    elif hashed_password == user.password:
        # create session token
        session_token = str(uuid.uuid4())

        user.session_token = session_token
        db.add(user)
        db.commit()

        # save user's email into a cookie
        response = make_response(redirect(url_for('index')))
        response.set_cookie("session_token", session_token, httponly=True, samesite="Strict")

        return response

@app.route("/logout")
def logout():
    response = make_response(redirect(url_for('index')))
    response.set_cookie("session_token", expires=0)

    return response


@app.route("/result", methods=["POST"])
def result():
    guess = int(request.form.get("guess"))

    session_token = request.cookies.get("session_token")

    # get user from the database based on her/his email address
    user = db.query(User).filter_by(session_token=session_token).first()

    if guess == user.secret_number:
        message = "Correct! The secret number is {0}".format(str(guess))

        # create a new random secret number
        new_secret = random.randint(1, 30)

        # update the user's secret number
        user.secret_number = new_secret

        # update the user object in a database
        db.add(user)
        db.commit()
    elif guess > user.secret_number:
        message = "Your guess is not correct... try something smaller."
    elif guess < user.secret_number:
        message = "Your guess is not correct... try something bigger."

    return render_template("result.html", message=message)


@app.route("/profile", methods=["GET"])
def profile():
    session_token = request.cookies.get("session_token")

    user = db.query(User).filter_by(session_token=session_token).first()

    if user:
        return render_template("profile.html", user=user)
    else:
        return redirect(url_for("index"))

@app.route("/profile/edit", methods=["GET", "POST"])
def profile_edit():
    session_token = request.cookies.get("session_token")

    user = db.query(User).filter_by(session_token=session_token).first()

    if request.method == "GET":
        if user:
            return render_template("profile_edit.html", user=user)
        else:
            return redirect(url_for("index"))

    elif request.method == "POST":
        name = request.form.get("profile-name")
        email = request.form.get("profile-email")
        old_password = request.form.get("old-password")
        new_password = request.form.get("new-password")
        confirm_password = request.form.get("confirm-password")

        # update
        user.name = name
        user.email = email

        if old_password and new_password:
            hashed_old_password = hashlib.sha256(old_password.encode()).hexdigest()  # hash the old password
            hashed_new_password = hashlib.sha256(new_password.encode()).hexdigest()  # hash the old password

            # check if old password hash is equal to the password hash in the database
            if hashed_old_password == user.password:

                # CHECK IF NEW AND CONFIRMED PASSWORDS MATCH
                if new_password == confirm_password:
                    # if yes, save the new password hash in the database
                    user.password = hashed_new_password
                else:
                    # IF NOT, RETURN ERROR
                    return "The new and confirmed passwords do not match. Go back and try again."
            else:
                # if not, return error
                return "Wrong (old) password! Go back and try again."


        # store into database
        db.add(user)
        db.commit()

        return redirect(url_for("profile"))

@app.route("/profile/delete", methods=["GET", "POST"])
def profile_delete():
    session_token = request.cookies.get("session_token")

    user = db.query(User).filter_by(session_token=session_token).first()

    if request.method == "GET":
        if user:
            return render_template("profile_delete.html", user=user)
        else:
            return redirect(url_for("index"))

    elif request.method == "POST":

        # SET DELETE COLUMN TO TRUE E.G. DEACTIVATED PROFILE
        user.deleted = True
        db.add(user)
        db.commit()

        return redirect(url_for("index"))


@app.route("/users", methods=["GET"])
def all_users():

    users = db.query(User).filter_by(deleted=False).all()   # FIND ALL UNDELETED USERS

    return render_template("users.html", users=users)


@app.route("/user/<user_id>", methods=["GET"])
def user_details(user_id):

    user = db.query(User).get(int(user_id))

    return render_template("user_details.html", user=user)

if __name__ == '__main__':
    app.run()