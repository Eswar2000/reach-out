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

def getMatrix():
    cursor = mysql.connection.cursor()
    query = "SELECT * from friends"
    cursor.execute(query)
    temp = cursor.fetchall()
    query = "SELECT count(*) from signup"
    cursor.execute(query)
    userNum = cursor.fetchall()
    userNum = userNum[0][0]
    print(userNum)
    print(temp)
    # userMat = [[0]*userNum]*userNum
    # for ele in temp:
    #     userMat[ele[0]][ele[1]] = 1
    # print(userMat)

@app.route('/')
def home():
    getMatrix()
    return "matrix"

if __name__ == '__main__':
    port = int(os.environ.get('APP_PORT'))
    host = os.environ.get('APP_HOST')
    app.run(host=host, port=port, debug=True)