import string
import re
from hashlib import shake_128
import urllib3
from flask import Flask, request, abort, redirect, make_response
import base64
import json

import duckdb

# import all the constants
from conf import *

app = Flask(__name__)

def _genShort(url, size = HASH_LEN):
    """private function to generate short ID for a given url.
       basically, it first hash the url and then transform the result to base62
    """
    enc = url.encode()
    hash = shake_128(enc).hexdigest(size)
    hex = eval('0x' + hash)

    ## now we convert it to base62
    short = ""
    while True:
        hex, rem = divmod(hex, len(ALPHABET))
        short += ALPHABET[rem]
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
    def __init__(self, filename = None):
        """ if a filename is provided, persistent storage will be enabled.
        """
        if filename:
            self.con = duckdb.connect(filename)
        else:
            self.con = duckdb.connect()
        # an index will be created by setting primary key
        self.con.sql("CREATE TABLE IF NOT EXISTS urlpair(short varchar primary key, original varchar, count bigint, user varchar);")

    def add(self, url, user):
        """ This is for shortening a url (POST /)
            if there is a collision, we simply overwrite the previous one
        """
        short = _genShort(url)
        result = self.con.sql("select original from urlpair where short = '{}' and user = '{}'".format(short, user)).fetchall()
        if len(result) == 1:
            self.con.sql("UPDATE urlpair SET original = '{}', count = 1 WHERE short = '{}' and user = '{}'".format(url, short, user))
        elif len(result) == 0:
            self.con.sql("INSERT INTO urlpair VALUES ('{}', '{}', 1, '{}')".format(short, url, user))
        else:
            raise Exception("got more than one results")
        return short

    def get(self, short):
        """ This is for get /:id
        """
        result = self.con.sql("select original from urlpair where short = '{}'".format(short)).fetchall()
        if len(result) == 1:
            self.con.sql("UPDATE urlpair SET count = count + 1 WHERE short = '{}'".format(short))
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
        result = self.con.sql("select original from urlpair where short = '{}' and user = '{}'".format(short, user)).fetchall()
        if len(result) == 1:
            self.con.sql("UPDATE urlpair SET original = '{}', count = 0 WHERE short = '{}' and user = '{}'".format(url, short, user))
            return url
        elif len(result) == 0:
            return None
        else:
            raise Exception("got more than one results")

    def delete(self, short, user):
        """ This is for delete /:id
        """
        result = self.con.sql("select original from urlpair where short = '{}' and user = '{}'".format(short, user)).fetchall()
        if len(result) == 1:
            self.con.sql("delete from urlpair where short = '{}' and user = '{}'".format(short, user))
            return result[0][0]
        elif len(result) == 0:
            return None
        else:
            raise Exception("got more than one results")

    def clear(self, user):
        """ this is for DELETE /, which will clear the table.
        """
        self.con.sql("delete from urlpair where user = '{}'".format(user))
        return True

    def getAllKeys(self, user):
        """ This is for GET /, which will return all the short IDs.
        """
        result = self.con.sql("select short from urlpair where user = '{}'".format(user)).fetchall()
        # we need to flat the result.
        flat = [key for z in result for key in z]
        return " ".join(flat)

    def stat(self, n = None):
        """ This is for GET /stat and GET /stat/n
        """
        result = self.con.sql("select short, original, count, user from urlpair order by count desc;").fetchall()
        if n:
            result = result[:n]
        resp = " \n".join("{}=>{}: {}".format(i[0], i[1], i[2]) for i in result)
        return resp

# init the Shortner
shortner = Shortner()

# require_auth, this function will be used as
# a decorator, and will decorate all the handlers 
# which reuqire auth
def require_auth(f):
    def inner(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return make_response("forbidden", 403)
        http = urllib3.PoolManager()
        headers = {
                'Authorization': token,
                'Content-Type': 'application/json'
                }
        r = http.request('GET', AUTH_URL, headers=headers)
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
        return make_response(short, 200)
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

if __name__ == '__main__':
    # listen not only the localhost
    app.run(host="0.0.0.0", port = 12345)
