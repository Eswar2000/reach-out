import os
from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
# Initialize
db = SQLAlchemy(app)


# model
class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Name %r>' % self.id


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
    if request.method == 'GET':
        return render_template('signup.html', err="GET")
    else:
        return render_template('signup.html', err="POST")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5555))
    app.run(host='localhost', port=port, debug=True)
