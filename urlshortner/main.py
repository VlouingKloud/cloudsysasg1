import string
import re
from hashlib import shake_128
import urllib3
from flask import Flask, request, abort, redirect, make_response

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
        self.con.sql("CREATE TABLE IF NOT EXISTS urlpair(short varchar primary key, original varchar, count bigint);")

    def add(self, url):
        """ This is for shortening a url (POST /)
            if there is a collision, we simply overwrite the previous one
        """
        short = _genShort(url)
        result = self.con.sql("select original from urlpair where short = '{}'".format(short)).fetchall()
        if len(result) == 1:
            self.con.sql("UPDATE urlpair SET original = '{}', count = 1 WHERE short = '{}'".format(url, short))
        elif len(result) == 0:
            self.con.sql("INSERT INTO urlpair VALUES ('{}', '{}', 1)".format(short, url))
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

    def put(self, url, short):
        """ This is for put /:id
        When the given id is in the database, it will change the mapping to the new url
        otherwise, it will return None
        """
        result = self.con.sql("select original from urlpair where short = '{}'".format(short)).fetchall()
        if len(result) == 1:
            self.con.sql("UPDATE urlpair SET original = '{}', count = 0 WHERE short = '{}'".format(url, short))
            return url
        elif len(result) == 0:
            return None
        else:
            raise Exception("got more than one results")

    def delete(self, short):
        """ This is for delete /:id
        """
        result = self.con.sql("select original from urlpair where short = '{}'".format(short)).fetchall()
        if len(result) == 1:
            self.con.sql("delete from urlpair where short = '{}'".format(short))
            return result[0][0]
        elif len(result) == 0:
            return None
        else:
            raise Exception("got more than one results")

    def clear(self):
        """ this is for DELETE /, which will clear the table.
        """
        self.con.sql("delete from urlpair")
        return True

    def getAllKeys(self):
        """ This is for GET /, which will return all the short IDs.
        """
        result = self.con.sql("select short from urlpair").fetchall()
        # we need to flat the result.
        flat = [key for z in result for key in z]
        return " ".join(flat)

    def stat(self, n = None):
        """ This is for GET /stat and GET /stat/n
        """
        result = self.con.sql("select short, original, count from urlpair order by count desc;").fetchall()
        if n:
            result = result[:n]
        resp = " \n".join("{}=>{}: {}".format(i[0], i[1], i[2]) for i in result)
        return resp

# init the Shortner
shortner = Shortner()

def require_auth(f):
    def inner(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return make_response("forbidden", 403)
        http = urllib3.PoolManager()
        headers = {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
                }
        r = http.request('GET', AUTH_URL, headers=headers)
        if r.status == 200:
            return f(*args, **kwargs)
        else:
            return make_response("forbidden", 403)
    return inner

# GET /
@app.get('/')
def getIndex():
    return make_response(shortner.getAllKeys(), 200)

# POST /
@app.post('/')
def postIndex():
    url = request.form['url']
    if not check_url(url):
        return make_response("url nor valid", 400)
    try:
        short = shortner.add(url)
        return make_response(short, 200)
    except Exception:
        return make_response("error", 400)

# DELETE /
@app.delete('/')
def deleteIndex():
    shortner.clear()
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
def putID(id):
    try:
        url = request.form['url']
        if not check_url(url):
            return make_response("url nor valid", 400)
        url = shortner.put(url, id)
        if url:
            return make_response(url + "=> " + id, 200)
        else:
            return make_response("not found", 404)
    except Exception:
        return make_response("error", 400)

# DELETE /:id
@app.delete('/<id>')
def deleteID(id):
    url = shortner.delete(id)
    if url:
        resp = make_response(url, 204)
        return resp
    else:
        abort(404)

# GET /stat
@app.get('/stat')
@require_auth
def getStat():
    return shortner.stat()

# GET /stat/:n
@app.get('/stat/<n>')
def getNStat(n):
    return shortner.stat(int(n))

if __name__ == '__main__':
    # listen not only the localhost
    app.run(host="0.0.0.0", port = 12345)
