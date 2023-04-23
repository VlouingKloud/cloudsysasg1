from flask import Flask, request, abort, redirect, make_response
import duckdb
import bcrypt

import jwt
from conf import *

app = Flask(__name__)

class UserMgr:
    """ This is the class to manage users
    """
    def __init__(self, filename = None):
        if filename:
            self.con = duckdb.connect(filename)
        else:
            self.con = duckdb.connect()
        self.con.sql("CREATE TABLE IF NOT EXISTS users(name varchar primary key, password varchar);")

    def create(self, username, password):
        """ create a new user
            return True if ok
            return False if there is duplicate
        """
        sql = "SELECT COUNT(*) FROM users WHERE name='{}'".format(username)
        if self.con.sql(sql).fetchone()[0] > 0:
            return False
        password = password.encode('utf-8')
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())

        sql = "INSERT INTO users VALUES ('{}', '{}')".format(username, hashed.decode("utf-8"))
        self.con.sql(sql)
        return True

    def update(self, username, old, new):
        """ update the password of a given user
            return True if ok
            anyother cases will return False
        """
        sql = "SELECT password FROM users WHERE name = '{}'".format(username)
        result = self.con.sql(sql).fetchall()
        if len(result) != 1:
            return False
        if not bcrypt.checkpw(old.encode("utf-8"), result[0][0].encode("utf-8")):
            return False
        new = new.encode("utf-8")
        hashed = bcrypt.hashpw(new, bcrypt.gensalt())

        sql = "UPDATE users SET password = '{}' WHERE name = '{}'".format(hashed.decode("utf-8"), username)
        self.con.sql(sql)
        return True

    def login(self, username, password):
        """ check if the username and password match
            return a jwt if ok
            otherwise will return False
        """
        sql = "SELECT password FROM users WHERE name = '{}'".format(username)
        result = self.con.sql(sql).fetchall()
        if len(result) != 1:
            return False
        if not bcrypt.checkpw(password.encode("utf-8"), result[0][0].encode("utf-8")):
            return False
        return jwt.createJWT(username)


# init the UserMgr
umgr = UserMgr()


# POST /users
@app.post("/users")
def postUsers():
    user = request.form['username']
    password = request.form['password']
    try:
        flag = umgr.create(user, password)
        if flag:
            return make_response("user {} created".format(user), 201)
        else:
            return make_response("duplicate", 409)
    except Exception:
        abort(400)


# PUT /users
@app.put("/users")
def putUsers():
    user = request.form['username']
    old = request.form['old-password']
    new = request.form['new-password']
    try:
        flag = umgr.update(user, old, new)
        if flag:
            return make_response("updated password for {}".format(user), 200)
        else:
            return make_response("forbidden", 403)
    except Exception:
        abort(400)


# POST /users/login
@app.post("/users/login")
def postLogin():
    user = request.form['username']
    password = request.form['password']
    try:
        res = umgr.login(user, password)
        if not res:
            return make_response("forbidden", 403)
        else:
            return make_response(res, 200)
    except Exception:
        abort(400)

@app.get("/users/auth")
def getAuth():
    try:
        token = request.headers.get('Authorization')
        if jwt.verifyJWT(token):
            return make_response("ok", 200)
        else:
            return make_response("forbidden", 403)
    except Exception:
        return make_response("forbidden", 403)

if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 12356)
