import json
import os
from flask import Flask, request, redirect, render_template, session, url_for, make_response
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'KRACKHEAD$1234'
mysql = MySQL()
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'pieceofshit'
app.config['MYSQL_DB'] = 'test_db'

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
    if check_password_hash(temp[0][2], password):
        session['user'] = temp[0][0]
        session['name'] = temp[0][1]
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
                    resp.set_cookie('login', cookieDict, max_age=60*60*24*7)
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


@app.route('/dashboard', methods=['POST', 'GET'])
def dashboard():
    if 'user' in session:
        user = session['name']
        if request.method == 'GET':
            return render_template('dashboard.html', user=user)
        else:
            return render_template('dashboard.html', user="Not Completed")
    else:
        return redirect(url_for('signin'))


@app.route('/signout', methods=['GET'])
def signout():
    session.pop('user', None)
    session.pop('name', None)
    resp = make_response(redirect(url_for('home')))
    resp.set_cookie('login', "CLEAR", max_age=0)
    return resp


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5555))
    app.run(host='localhost', port=port, debug=True)
