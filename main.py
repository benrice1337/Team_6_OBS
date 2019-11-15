import time
import os
from flask import Flask, render_template, request
import jwt
import sqlalchemy as db
import pymysql

app = Flask(__name__)

app.config['SECRET'] = os.environ['JWT_SECRET']
engine = db.create_engine(os.environ['DB_CONN_STRING'], pool_pre_ping=True)

#use this route to establish the db connection when its ready
@app.route('/connect')
def connect():
    try:
        app.config['DB_CONN'] = engine.connect()
        return 'Connection Successful', 200
    except:
        return 'Connection Failed', 500

@app.route('/')
def home():
    """The home page."""
    return render_template("obs_navigation.html")

@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Creates a new user."""
    if request.method == "GET":
        return render_template("signup.html")
    if request.method == "POST":
        username = request.form.get("username", None)
        password = request.form.get("password", None)
        email = request.form.get("email", None)

        #check whether all the data was passed in properly
        if username is None or password is None or email is None:
            return "Failed Request", 404

        #check database for existing user
        sql = 'SELECT uid, username, email FROM accounts WHERE email=\'' + email + '\''
        existing = app.config['DB_CONN'].execute(sql).fetchall()
        if len(existing) == 0:
            #send to database
            sql = 'INSERT INTO accounts (username, password, email) VALUES'
            sql += ' (\'' + username + '\',\'' + password + '\',\'' + email + '\');'
            app.config['DB_CONN'].execute(sql)

            #query for additional auto-generated user info
            sql = 'SELECT uid, username, email FROM accounts WHERE email=\'' + email + '\''
            test = app.config['DB_CONN'].execute(sql).fetchall()

            payload = {'uid' : test[0][0], 'username' : test[0][1], 'email' : test[0][2]}
            token = jwt.encode(payload, app.config['SECRET'], algorithm='HS256')
            return token, 200

        return "Email address already in use", 400

@app.route('/login', methods=["GET", "POST"])
def login():
    """Logs in."""
    if request.method == "GET":
        return "Success", 404
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        #check whether all the data was passed in properly
        if username is None or password is None:
            return "Failed Request", 404

        sql = 'SELECT * FROM accounts WHERE username=\'' + username + '\''
        sql += ' AND password=\'' + password + '\''
        test = app.config['DB_CONN'].execute(sql).fetchall()
        #Add form input cases

        if len(test) != 0:
            epoch_time = int(time.time()) + 3600
            payload = {'uid' : test[0][0], 'username' : test[0][1]}
            payload['email'] = test[0][2]
            payload['exp'] = epoch_time
            token = jwt.encode(payload, app.config['SECRET'], algorithm='HS256')
            return token, 200

        return "Invalid User Credentials", 400

@app.route('/welcome')
def welcome():
    """Welcome page."""
    return render_template("obs_home.html")

if __name__ == "__main__":

    app.run(debug=True)