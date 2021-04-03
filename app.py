import os
from flask import Flask, jsonify, request, redirect, render_template
from flask_mysqldb import MySQL

app = Flask(__name__)
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


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        query = "select * from signup where email like '{}' and pw like '{}'".format(email,password)
        cursor.execute(query)
        temp = cursor.fetchall()
        mysql.connection.commit()
        cursor.close()
        if(len(temp)>0):
            return render_template('dashboard.html',user=temp[0][0])
        else:
            return render_template('login.html',err="Username Or Password Is Wrong")
    else:
        return render_template('login.html',err="")




@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        uname = request.form["username"]
        pw = request.form["password"]
        cnfPw = request.form["confirmPwd"]
        email = request.form["email"]
        currUser['uname']=uname
        currUser['email']=email
        if(pw != cnfPw):
            return render_template('signup.html',err="Password Fields Didn't Match")
        cursor = mysql.connection.cursor()
        query = "INSERT INTO signup(uname,pw,email) VALUES(%s,%s,%s)"
        cursor.execute(query,(uname,pw,email))
        mysql.connection.commit()
        cursor.close()
        return render_template("dashboard.html",user=uname)
    else:
        return render_template("signup.html",err="")
    


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5555))
    app.run(host='localhost', port=port, debug=True)
