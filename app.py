import os
from flask import Flask, jsonify, request, redirect, render_template
from flask_mysqldb import MySQL

app = Flask(__name__)
mysql = MySQL()
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Thestylishstar1'
app.config['MYSQL_DB'] = 'test_db'

mysql.init_app(app)

currUser = {}

@app.route('/')
def home():
    return render_template('homepage.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template('login.html', err="")
    else:
        uname = request.form['username']
        password = request.form['password']


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        uname = request.form["username"]
        pw = request.form["password"]
        cnfPw = request.form["confirmPwd"]
        email = request.form["email"]
        currUser['uname']=uname
        currUser['email']=email
        cursor = mysql.connection.cursor()
        query = "INSERT INTO signup(uname,pw,email) VALUES(%s,%s,%s)"
        cursor.execute(query,(uname,pw,cnfPw,email))
        mysql.connection.commit()
        cursor.close()
        return render_template("homepage.html")
    return render_template('signup.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5555))
    app.run(host='localhost', port=port, debug=True)
