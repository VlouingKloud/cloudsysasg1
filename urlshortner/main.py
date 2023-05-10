import string
import re
import os
from hashlib import shake_128
import urllib3
from flask import Flask, request, abort, redirect, make_response
import base64
import json
from functools import wraps
import psycopg2

# import all the constants
import conf

# read secrets
environs = ["DB_CONFIG_FILE"]
for environ in environs:
    if environ in os.environ:
        filename = os.environ[environ]
    elif os.path.isfile("/run/secrets/" + environ):
        filename = "/run/secrets/" + environ
    else:
        exit(1)
    if environ == 'JWT_KEY_FILE':
        key = filename
        continue
    with open(filename, 'r') as f:
        if environ == 'DB_CONFIG_FILE':
            db_config = {}
            lines = f.read().strip().split(' ')
            for line in lines:
                line = line.strip().split("=")
                if len(line) != 2:
                    exit(2)
                db_config[line[0].strip()] = line[1].strip()
        db_config['DATABASE'] = None


app = Flask(__name__)

def _genShort(url, size = conf.HASH_LEN):
    """private function to generate short ID for a given url.
       basically, it first hash the url and then transform the result to base62
    """
    enc = url.encode()
    hash = shake_128(enc).hexdigest(size)
    hex = eval('0x' + hash)

    ## now we convert it to base62
    short = ""
    while True:
        hex, rem = divmod(hex, len(conf.ALPHABET))
        short += conf.ALPHABET[rem]
        if hex == 0:
            break
    return short

def check_url(url):
    """
        The following is adapted from other project 
        github link:https://github.com/django/django/blob/stable/1.3.x/django/core/validators.py#L45
    """
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$' # path
        , re.IGNORECASE) # case-insensitive
    if regex.match(url):
        return True
    else:
        return False

class Shortner:
    """ This is the class to manage short urls
    """
    def __init__(self, host, database, user, password):
        """ if a filename is provided, persistent storage will be enabled.
        """
        self.conn = psycopg2.connect(
                host=host,
                database=database,
                user=user,
                password=password,
        )

        self.con = self.conn.cursor()
        self.con.execute("CREATE TABLE IF NOT EXISTS urlpair(short varchar primary key, original varchar, count bigint, username varchar);")
        self.conn.commit()

    def add(self, url, user):
        """ This is for shortening a url (POST /)
            if there is a collision, we simply overwrite the previous one
        """
        short = _genShort(url)
        self.con.execute("select original from urlpair where short = '{}' and username = '{}'".format(short, user))
        result = self.con.fetchall()
        if len(result) == 1:
            self.con.execute("UPDATE urlpair SET original = '{}', count = 1 WHERE short = '{}' and username = '{}'".format(url, short, user))
        elif len(result) == 0:
            self.con.execute("INSERT INTO urlpair VALUES ('{}', '{}', 1, '{}')".format(short, url, user))
        else:
            raise Exception("got more than one results")
        self.conn.commit()
        return short

    def get(self, short):
        """ This is for get /:id
        """
        self.con.execute("select original from urlpair where short = '{}'".format(short))
        result = self.con.fetchall()
        if len(result) == 1:
            self.con.execute("UPDATE urlpair SET count = count + 1 WHERE short = '{}'".format(short))
            return result[0][0]
        elif len(result) == 0:
            return None
        else:
            raise Exception("got more than one results")

    def put(self, url, short, user):
        """ This is for put /:id
        When the given id is in the database, it will change the mapping to the new url
        otherwise, it will return None
        """
        self.con.execute("select original from urlpair where short = '{}' and username = '{}'".format(short, user))
        result = self.con.fetchall()
        if len(result) == 1:
            self.con.execute("UPDATE urlpair SET original = '{}', count = 0 WHERE short = '{}' and username = '{}'".format(url, short, user))
            self.conn.commit()
            return url
        elif len(result) == 0:
            return None
        else:
            raise Exception("got more than one results")

    def delete(self, short, user):
        """ This is for delete /:id
        """
        self.con.execute("select original from urlpair where short = '{}' and username = '{}'".format(short, user))
        result = self.con.fetchall()
        if len(result) == 1:
            self.con.execute("delete from urlpair where short = '{}' and username = '{}'".format(short, user))
            self.conn.commit()
            return result[0][0]
        elif len(result) == 0:
            return None
        else:
            raise Exception("got more than one results")

    def clear(self, user):
        """ this is for DELETE /, which will clear the table.
        """
        self.con.execute("delete from urlpair where username = '{}'".format(user))
        self.conn.commit()
        return True

    def getAllKeys(self, user):
        """ This is for GET /, which will return all the short IDs.
        """
        self.con.execute("select short from urlpair where username = '{}'".format(user))
        result = self.con.fetchall()
        # we need to flat the result.
        flat = [key for z in result for key in z]
        return " ".join(flat)

    def stat(self, n = None):
        """ This is for GET /stat and GET /stat/n
        """
        self.con.execute("select short, original, count, user from urlpair order by count desc;")
        result = self.con.fetchall()
        if n:
            result = result[:n]
        resp = " \n".join("{}=>{}: {}".format(i[0], i[1], i[2]) for i in result)
        return resp

# init the Shortner
shortner = Shortner(db_config['DBADDR'], db_config['DATABASE'], db_config['DBUSER'], db_config['DBPASSWORD'])

# require_auth, this function will be used as
# a decorator, and will decorate all the handlers 
# which reuqire auth
def require_auth(f):
    @wraps(f)
    def inner(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return make_response("forbidden", 403)
        http = urllib3.PoolManager()
        headers = {
                'Authorization': token,
                'Content-Type': 'application/json'
                }
        r = http.request('GET', conf.AUTH_URL, headers=headers)
        if r.status == 200:
            return f(*args, **kwargs)
        else:
            return make_response("forbidden", 403)
    return inner

def get_user_from_token(token):
    """ private function used get username from a token
    """
    if "Bearer " in token:
        token = token.split(' ')[1]
    enc_header, enc_payload, enc_sig = token.split(".")
    payload = json.loads(base64.urlsafe_b64decode(enc_payload + '==').decode('utf-8'))
    return payload['user']

# GET /
@app.get('/')
@require_auth
def getIndex():
    user = get_user_from_token(request.headers.get('Authorization'))
    return make_response(shortner.getAllKeys(user), 200)

# POST /
@app.post('/')
@require_auth
def postIndex():
    url = request.form['url']
    user = get_user_from_token(request.headers.get('Authorization'))
    if not check_url(url):
        return make_response("url nor valid", 400)
    try:
        short = shortner.add(url, user)
        return make_response(short, 201)
    except Exception:
        return make_response("error", 400)

# DELETE /
@app.delete('/')
@require_auth
def deleteIndex():
    user = get_user_from_token(request.headers.get('Authorization'))
    shortner.clear(user)
    abort(404)


# GET /:id
@app.get('/<id>')
def getID(id):
    url = shortner.get(id)
    if url:
        return redirect(location=url, code = 301)
    else:
        abort(404)

# PUT /:id
@app.put('/<id>')
@require_auth
def putID(id):
    try:
        user = get_user_from_token(request.headers.get('Authorization'))
        url = request.form['url']
        if not check_url(url):
            return make_response("url nor valid", 400)
        url = shortner.put(url, id, user)
        if url:
            return make_response(url + "=> " + id, 200)
        else:
            return make_response("not found", 404)
    except Exception:
        return make_response("error", 400)

# DELETE /:id
@app.delete('/<id>')
@require_auth
def deleteID(id):
    user = get_user_from_token(request.headers.get('Authorization'))
    url = shortner.delete(id, user)
    if url:
        resp = make_response(url, 204)
        return resp
    else:
        abort(404)

# GET /stat
@app.get('/stat')
def getStat():
    return shortner.stat()

# GET /stat/:n
@app.get('/stat/<n>')
def getNStat(n):
    return shortner.stat(int(n))

@app.get("/srvstatus")
def getSrvStatus():
    return make_response("ok", 200)

if __name__ == '__main__':
    # listen not only the localhost
    app.run(host= conf.ADDR, port = conf.PORT)
