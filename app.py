import json
import os
from flask import Flask, request, redirect, render_template, session, url_for, make_response
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('APP_SECRET_KEY')
mysql = MySQL()
app.config['MYSQL_HOST'] = os.getenv('DB_HOST')
app.config['MYSQL_USER'] = os.getenv('DB_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('DB_PASS')
app.config['MYSQL_DB'] = os.getenv('DB_SCHEMA')

mysql.init_app(app)
currUser = {}


@app.route('/')
def home():
    return render_template('homepage.html')


def signInQuery(email, password):
    cursor = mysql.connection.cursor()
    query = "select * from signup where email='{}'".format(email)
    cursor.execute(query)
    temp = cursor.fetchall()
    mysql.connection.commit()
    cursor.close()
    if len(temp) != 1:
        return False
    if check_password_hash(temp[0][2], password):
        session['user'] = temp[0][0]
        session['name'] = temp[0][1]
        session['requests'] = None
        session['email'] = temp[0][3]
        session['allUsers'] = None
        return True
    return False


@app.route('/signin', methods=['POST', 'GET'])
def signin():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    else:
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            keep = 'keepSignedIn' in request.form.keys()
            if signInQuery(email, password):
                resp = make_response(redirect(url_for('dashboard')))
                if keep:
                    cookieDict = json.dumps({'email': email, "pass": password})
                    resp.set_cookie('login', cookieDict, max_age=60 * 60 * 24 * 7)
                return resp
            else:
                return render_template('signin.html', err="Username Or Password Is Wrong")
        else:
            cookieDict = request.cookies.get('login')
            if cookieDict:
                cookieDict = json.loads(cookieDict)
                if signInQuery(cookieDict['email'], cookieDict['pass']):
                    print("used cookie")
                    return redirect(url_for('signin'))
            return render_template('signin.html', err="")


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    else:
        if request.method == 'POST':
            uname = request.form["username"]
            pw = request.form["password"]
            cnfPw = request.form["confirmPwd"]
            email = request.form["email"]
            currUser['uname'] = uname
            currUser['email'] = email
            if pw != cnfPw:
                return render_template('signup.html', err="Password Fields Didn't Match")
            hashedPwd = generate_password_hash(pw, "sha256")
            cursor = mysql.connection.cursor()
            query = "INSERT INTO signup(uname,pw,email) VALUES(%s,%s,%s)"
            cursor.execute(query, (uname, hashedPwd, email))
            mysql.connection.commit()
            cursor.close()
            return redirect(url_for('signin'))
        else:
            cookieDict = request.cookies.get('login')
            if cookieDict:
                cookieDict = json.loads(cookieDict)
                if signInQuery(cookieDict['email'], cookieDict['pass']):
                    print("used cookie")
                    return redirect(url_for('signin'))
            return render_template("signup.html", err="")


def getRequests():
    if 'user' in session:
        user = session['user']
        query = "SELECT fromID, uname FROM request,signup WHERE request.fromID=signup.userid and toID={}".format(user)
        cursor = mysql.connection.cursor()
        cursor.execute(query)
        session['requests'] = cursor.fetchall()
        cursor.close()
    getAllUsers()
    return


def getAllUsers():
    if 'user' in session:
        query = "SELECT * FROM users where userid != {}".format(session['user'])
        cursor = mysql.connection.cursor()
        cursor.execute(query)
        session['allUsers'] = cursor.fetchall()
        cursor.close()
    return None


@app.route('/dashboard', methods=['POST', 'GET'])
def dashboard():
    if 'user' in session:
        user = session['name']
        if request.method == 'GET':
            getRequests()
            return render_template('dashboard.html', user=user,email=session['email'],userid=session['user'],req=session['requests'])
        else:
            return render_template('dashboard.html', user="Not Completed")
    else:
        return redirect(url_for('signin'))


@app.route('/signout', methods=['GET'])
def signout():
    session.pop('user', None)
    session.pop('name', None)
    session.pop('requests', None)
    session.pop('allUsers', None)
    session.pop('email',None)
    resp = make_response(redirect(url_for('home')))
    resp.set_cookie('login', "CLEAR", max_age=0)
    return resp


@app.route('/addRequest', methods=['GET'])
def addRequest():
    if 'user' in session:
        fromUser, toUser = session['user'], request.args.get('id')
        if fromUser == toUser:
            return redirect(url_for('dashboard'))
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM friends WHERE uID={} and fID={}".format(fromUser, toUser)
        cursor.execute(query)
        temp = cursor.fetchall()
        if len(temp) == 0:
            query = "INSERT INTO request(fromID, toID) VALUES({},{})".format(fromUser, toUser)
            cursor.execute(query)
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('signin'))


@app.route('/addFriend', methods=['GET'])
def addFriend():
    if 'user' in session:
        fromUser, toUser = request.args.get('id'), session['user']
        if fromUser == toUser:
            return redirect(url_for('dashboard'))
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM request WHERE fromID={} and toID={}".format(fromUser, toUser)
        cursor.execute(query)
        temp = cursor.fetchall()
        if len(temp) == 1:
            queryDEL = "DELETE FROM request WHERE fromID={} and toId={}".format(fromUser, toUser)
            queryADD1 = "INSERT INTO friends(uID, fID) VALUES({},{})".format(fromUser, toUser)
            queryADD2 = "INSERT INTO friends(uID, fID) VALUES({},{})".format(toUser, fromUser)
            cursor.execute(queryDEL)
            cursor.execute(queryADD1)
            cursor.execute(queryADD2)
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('signin'))


@app.route('/declineRequest', methods=['GET'])
def declineRequest():
    if 'user' in session:
        fromUser, toUser = request.args.get('id'), session['user']
        if fromUser == toUser:
            return redirect(url_for('dashboard'))
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM request WHERE fromID={} and toID={}".format(fromUser, toUser)
        cursor.execute(query)
        temp = cursor.fetchall()
        if len(temp) == 1:
            queryDEL = "DELETE FROM request WHERE fromID={} and toId={}".format(fromUser, toUser)
            cursor.execute(queryDEL)
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('signin'))


if __name__ == '__main__':
    port = int(os.environ.get('APP_PORT'))
    host = os.environ.get('APP_HOST')
    app.run(host=host, port=port, debug=True)
