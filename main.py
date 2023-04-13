import string
import re
from hashlib import shake_128

from flask import Flask, request, abort, redirect, make_response

# we use duckdb
# the reason is that:
#   1. embedded and analytical
#   2. fast
#   3. no need to do complex configuration
#   4. and of course column storage
#   5. etc.
import duckdb

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
    if re.match(r'^(https?|ftp|file)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]', url):
        return True
    else:
        return False

class Shortner:
    """ This is the class to manage short urls
    """
    def __init__(self, filename = None):
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
        result = self.con.sql("select original from urlpair where short = '{}'".format(short)).fetchall()
        if len(result) == 1:
            self.con.sql("UPDATE urlpair SET count = count + 1 WHERE short = '{}'".format(short))
            return result[0][0]
        elif len(result) == 0:
            return None
        else:
            raise Exception("got more than one results")

    def put(self, url, short):
        result = self.con.sql("select original from urlpair where short = '{}'".format(short)).fetchall()
        if len(result) == 1:
            self.con.sql("UPDATE urlpair SET original = '{}', count = 0 WHERE short = '{}'".format(url, short))
            return url
        elif len(result) == 0:
            return None
        else:
            raise Exception("got more than one results")

    def delete(self, short):
        result = self.con.sql("select original from urlpair where short = '{}'".format(short)).fetchall()
        if len(result) == 1:
            self.con.sql("delete from urlpair where short = '{}'".format(short))
            return result[0][0]
        elif len(result) == 0:
            return None
        else:
            raise Exception("got more than one results")

    def clear(self):
        self.con.sql("delete from urlpair")
        return True

    def getAllKeys(self):
        result = self.con.sql("select short from urlpair").fetchall()
        flat = [key for z in result for key in z]
        return " ".join(flat)

    def stat(self, n = None):
        result = self.con.sql("select short, original, count from urlpair order by count desc;").fetchall()
        if n:
            result = result[:n]
        resp = " \n".join("{}=>{}: {}".format(i[0], i[1], i[2]) for i in result)
        return resp

shortner = Shortner()

@app.get('/')
def getIndex():
    return make_response(shortner.getAllKeys(), 200)

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

@app.delete('/')
def deleteIndex():
    shortner.clear()
    abort(404)


@app.get('/<id>')
def getID(id):
    url = shortner.get(id)
    if url:
        return redirect(location=url, code = 301)
    else:
        abort(404)

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

@app.delete('/<id>')
def deleteID(id):
    url = shortner.delete(id)
    if url:
        resp = make_response(url, 204)
        return resp
    else:
        abort(404)

@app.get('/stat')
def getStat():
    return shortner.stat()

@app.get('/stat/<n>')
def getNStat(n):
    return shortner.stat(int(n))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port = 12345)
