import json
import os
import sys
from cryptography.fernet import Fernet
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
crypt = Fernet(key=os.getenv('ENCRY_KEY').encode())

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
        session['outReq'] = None
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
                    cookieDict = crypt.encrypt(cookieDict.encode())
                    resp.set_cookie('login', cookieDict, max_age=60 * 60 * 24 * 7)
                return resp
            else:
                return render_template('signin.html', err="Username Or Password Is Wrong")
        else:
            cookieDict = request.cookies.get('login')
            if cookieDict:
                cookieDict = crypt.decrypt(cookieDict.encode()).decode()
                cookieDict = json.loads(cookieDict)
                if signInQuery(cookieDict['email'], cookieDict['pass']):
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
                cookieDict = crypt.decrypt(cookieDict.encode()).decode()
                cookieDict = json.loads(cookieDict)
                if signInQuery(cookieDict['email'], cookieDict['pass']):
                    return redirect(url_for('signin'))
            return render_template("signup.html", err="")


def getRequests():
    if 'user' in session:
        user = session['user']
        query = "SELECT fromID, uname FROM request,signup WHERE request.fromID=signup.userid and toID={}".format(user)
        cursor = mysql.connection.cursor()
        cursor.execute(query)
        session['requests'] = cursor.fetchall()
        query = "SELECT toID FROM request WHERE fromId={}".format(user)
        cursor = mysql.connection.cursor()
        cursor.execute(query)
        session['outReq'] = cursor.fetchall()
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
        getMatrix()
    return None


def getMatrix():
    cursor = mysql.connection.cursor()
    query = "SELECT * from friends"
    cursor.execute(query)
    temp = cursor.fetchall()
    userNum = len(session['allUsers']) + 1
    userMatrix = [[sys.maxsize for _ in range(userNum)] for __ in range(userNum)]
    for i in range(userNum):
        userMatrix[i][i] = 0
    for elem in temp:
        userMatrix[elem[0]][elem[1]] = 1
    floyd(userNum, userMatrix)


def retVal(value):
    if value == sys.maxsize:
        return "N/A"
    if value == 1:
        return "Friend"
    if value % 10 == 1:
        if value // 10 == 1:
            return str(value) + "th"
        return str(value // 10) + "1st"
    if value % 10 == 2:
        if value // 10 == 1:
            return str(value) + "th"
        return str(value // 10) + "2nd" if value // 10 != 0 else "2nd"
    if value % 10 == 3:
        if value // 10 == 1:
            return str(value) + "th"
        return str(value // 10) + "3rd" if value // 10 != 0 else "3rd"
    else:
        return str(value) + "th"


def floyd(V, userMatrix):
    levelFriend = list(map(lambda i: list(map(lambda j: j, i)), userMatrix))
    for k in range(V):
        for i in range(V):
            for j in range(V):
                levelFriend[i][j] = min(levelFriend[i][j], levelFriend[i][k] + levelFriend[k][j])
    fromVal = session['user']
    newList = []
    for elem in session['allUsers']:
        toVal = elem[0]
        distance = retVal(levelFriend[fromVal][toVal])
        newList.append((elem[0], elem[1], distance))
    session['allUsers'] = newList
    prims(userMatrix, V)


@app.route('/dashboard', methods=['POST', 'GET'])
def dashboard():
    if 'user' in session:
        user = session['name']
        if request.method == 'GET':
            getRequests()
            renderDetails = {
                'user': user,
                'email': session['email'],
                'userid': session['user'],
                'incomingReq': session['requests'],
                'outgoingReq': session['outReq'],
                'all': session['allUsers']
            }
            return render_template('dashboard.html', required=renderDetails)
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
    session.pop('email', None)
    session.pop('outReq', None)
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
        temp0 = cursor.fetchall()
        query = "SELECT * FROM request WHERE fromID={} and toID={}".format(fromUser, toUser)
        cursor.execute(query)
        temp1 = cursor.fetchall()
        if len(temp0) == 0 and len(temp1) == 0:
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


@app.route('/removeFriend', methods=['GET'])
def removeFriend():
    if 'user' in session:
        fromUser, toUser = request.args.get('id'), session['user']
        if fromUser == toUser:
            return redirect(url_for('dashboard'))
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM friends WHERE uID={} and fID={}".format(fromUser, toUser)
        cursor.execute(query)
        temp = cursor.fetchall()
        if len(temp) == 1:
            queryDEL1 = "DELETE FROM friends WHERE uID={} and fID={}".format(fromUser, toUser)
            queryDEL2 = "DELETE FROM friends WHERE uID={} and fID={}".format(toUser, fromUser)
            cursor.execute(queryDEL1)
            cursor.execute(queryDEL2)
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('signin'))


@app.route('/sendMessage', methods=['GET'])
def sendMessage():
    if 'user' in session:
        renderDetails = {
            'non': session['nonReach'],
            'edgeList': session['edgeList']
        }
        return render_template('message.html', required=renderDetails)
    else:
        return redirect(url_for('signin'))


def minDistance(dist, visited, vertices):
    min = sys.maxsize
    min_index = -1
    for ver in range(vertices):
        if dist[ver] < min and visited[ver] == False:
            min = dist[ver]
            min_index = ver
    return min_index


def idMapping(edgeList, nonReach):
    query = "SELECT * FROM users"
    cursor = mysql.connection.cursor()
    cursor.execute(query)
    temp = list(cursor.fetchall())
    for i in range(len(edgeList)):
        edgeList[i] = (temp[edgeList[i][0]][1], temp[edgeList[i][1]][1])
    for i in range(len(nonReach)):
        nonReach[i] = temp[nonReach[i]][1]
    session['edgeList'] = edgeList
    session['nonReach'] = nonReach
    mysql.connection.commit()
    cursor.close()


def backtrackMST(a, vertices):
    edgeList = []
    nonReach = []
    for i in range(vertices):
        if a[i] is None:
            nonReach.append(i)
            continue
        elif a[i] == -1:
            continue
        else:
            edgeList.append((i, a[i]))
    idMapping(edgeList, nonReach)


def prims(userMatrix, vertices):
    temp = 2
    g = [[0 for _ in range(vertices)] for __ in range(vertices)]
    for i in range(vertices):
        for j in range(vertices):
            g[i][j] = userMatrix[i][j] if userMatrix[i][j] != sys.maxsize else 0
    parentArr = [None] * vertices
    dist = [sys.maxsize] * vertices
    dist[temp], parentArr[temp] = 0, -1
    visited = [False] * vertices
    for _ in range(vertices):
        u = minDistance(dist, visited, vertices)
        if u != -1:
            visited[u] = True
            for ver in range(vertices):
                if 0 < g[u][ver] < dist[ver] and visited[ver] == False:
                    dist[ver] = g[u][ver]
                    parentArr[ver] = u
    backtrackMST(parentArr, vertices)


if __name__ == '__main__':
    port = int(os.environ.get('APP_PORT'))
    host = os.environ.get('APP_HOST')
    app.run(host=host, port=port, debug=True)
