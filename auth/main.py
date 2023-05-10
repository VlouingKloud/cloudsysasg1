from flask import Flask, request, abort, redirect, make_response
import bcrypt
import psycopg2

import os

import jwt
import conf

app = Flask(__name__)

# read the sensitive information
environs = ["JWT_KEY_FILE", "DB_CONFIG_FILE"]
for environ in environs:
    if environ in os.environ:
        filename = os.environ[environ]
    elif os.path.isfile("/run/secrets/" + environ):
        filename = "/run/secrets/" + environ
    else:
        exit(1)
    with open(filename, 'r') as f:
        if environ == 'JWT_KEY_FILE':
            key = f.read().strip()
        elif environ == 'DB_CONFIG_FILE':
            db_config = {}
            lines = f.read().strip().split(' ')
            for line in lines:
                line = line.strip().split("=")
                if len(line) != 2:
                    exit(2)
                db_config[line[0].strip()] = line[1].strip()
        db_config['DATABASE'] = None

class UserMgr:
    """ This is the class to manage users
    """
    def __init__(self, host, database, user, password):
        self.conn = psycopg2.connect(
                host=host,
                database=database,
                user=user,
                password=password,
        )
        self.con = self.conn.cursor()
        self.con.execute("CREATE TABLE IF NOT EXISTS users(name varchar primary key, password varchar);")
        self.conn.commit()

    def create(self, username, password):
        """ create a new user
            return True if ok
            return False if there is duplicate
        """
        sql = "SELECT COUNT(*) FROM users WHERE name='{}'".format(username)
        self.con.execute(sql)
        if self.con.fetchone()[0] > 0:
            return False
        password = password.encode('utf-8')
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())

        sql = "INSERT INTO users VALUES ('{}', '{}')".format(username, hashed.decode("utf-8"))
        self.con.execute(sql)
        self.conn.commit()
        return True

    def update(self, username, old, new):
        """ update the password of a given user
            return True if ok
            anyother cases will return False
        """
        sql = "SELECT password FROM users WHERE name = '{}'".format(username)
        self.con.execute(sql)
        result = self.con.fetchall()
        if len(result) != 1:
            return False
        if not bcrypt.checkpw(old.encode("utf-8"), result[0][0].encode("utf-8")):
            return False
        new = new.encode("utf-8")
        hashed = bcrypt.hashpw(new, bcrypt.gensalt())

        sql = "UPDATE users SET password = '{}' WHERE name = '{}'".format(hashed.decode("utf-8"), username)
        self.con.execute(sql)
        self.conn.commit()
        return True

    def login(self, username, password):
        """ check if the username and password match
            return a jwt if ok
            otherwise will return False
        """
        sql = "SELECT password FROM users WHERE name = '{}'".format(username)
        self.con.execute(sql)
        result = self.con.fetchall()
        if len(result) != 1:
            return False
        if not bcrypt.checkpw(password.encode("utf-8"), result[0][0].encode("utf-8")):
            return False
        return jwt.createJWT(username, key = key)


# init the UserMgr
umgr = UserMgr(db_config['DBADDR'], db_config['DATABASE'], db_config['DBUSER'], db_config['DBPASSWORD'])


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
    except Exception as e:
        print(e, flush = True)
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
    except Exception as e:
        print(e, flush = True)
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
        if "Bearer " in token:
            token = token.split(' ')[1]
        if jwt.verifyJWT(token, key):
            return make_response("ok", 200)
        else:
            return make_response("forbidden", 403)
    except Exception:
        return make_response("forbidden", 403)

@app.get("/srvstatus")
def getSrvStatus():
    return make_response("ok", 200)

if __name__ == "__main__":
    app.run(host = conf.ADDR, port = conf.PORT)
