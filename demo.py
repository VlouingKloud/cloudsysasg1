"""
This script is used to demostrate our service.
"""

import random
import string
import urllib3

http = urllib3.PoolManager()

# server address
shortner = "http://172.22.0.3:12357"
auth = "http://172.22.0.2:12356"

def testPostUsers():
    """ return 201 or 409
    """
    # create user z
    fields = {"username": "z", "password": "zzz"}
    r = http.request("POST", auth + "/users", fields = fields)
    assert(r.status == 201)
    print(r.status, r.data.decode())

    # create user x
    fields = {"username": "x", "password": "xxx"}
    r = http.request("POST", auth + "/users", fields = fields)
    assert(r.status == 201)
    print(r.status, r.data.decode())

    # create user z again, return 409
    fields = {"username": "z", "password": "zzz"}
    r = http.request("POST", auth + "/users", fields = fields)
    assert(r.status == 409)
    print(r.status, r.data.decode())

def testPutUser():
    """ return 200 or 403
    """
    fields = {"username": "z", "old-password": "zzz", "new-password": "123"}
    r = http.request("PUT", auth + "/users", fields = fields)
    assert(r.status == 200)
    print(r.status, r.data.decode())

    # return 403
    fields = {"username": "z", "old-password": "zzz", "new-password": "123"}
    r = http.request("PUT", auth + "/users", fields = fields)
    assert(r.status == 403)
    print(r.status, r.data.decode())

def testPostLogin():
    """ return 200 or 403
    """
    fields = {"username": "z", "password": "zzz"}
    r = http.request("POST", auth + "/users/login", fields = fields)
    assert(r.status == 403)
    print(r.status, r.data.decode())

    # return 200
    fields = {"username": "z", "password": "123"}
    r = http.request("POST", auth + "/users/login", fields = fields)
    assert(r.status == 200)
    print(r.status, r.data.decode())

def testPostUrl():
    """ return 201, 400, 403
    """
    # login as z
    fields = {"username": "z", "password": "123"}
    r = http.request("POST", auth + "/users/login", fields = fields)
    assert(r.status == 200)
    #print(r.status, r.data.decode())
    token = r.data.decode("utf-8")

    # we post some url, return 201
    headers = {"Authorization": "Bearer " + token}
    r = http.request("POST", shortner, headers = headers, fields = {"url": "https://en.wikipedia.org/wiki/URL"})
    assert(r.status == 201)
    print(r.status, r.data.decode())

    # return 403
    headers = {"Authorization": "Bearer " + token[:-2]}
    r = http.request("POST", shortner, headers = headers, fields = {"url": "https://en.wikipedia.org/wiki/Linux"})
    assert(r.status == 403)
    print(r.status, r.data.decode())

def testPutUrl():
    """ return 200, 400, 404, 403
    """
    # login as z
    fields = {"username": "z", "password": "123"}
    r = http.request("POST", auth + "/users/login", fields = fields)
    assert(r.status == 200)
    #print(r.status, r.data.decode())
    token = r.data.decode()

    # put, return 201
    headers = {"Authorization": "Bearer " + token}
    r = http.request("PUT", shortner, headers = headers, fields = {"url": "https://en.wikipedia.org/wiki/Linux"})
    assert(r.status == 200)
    print(r.status, r.data.decode())

    # put, return 201
    headers = {"Authorization": "Bearer " + token[:-2]}
    r = http.request("PUT", shortner, headers = headers, fields = {"url": "https://en.wikipedia.org/wiki/Linux"})
    assert(r.status == 200)
    print(r.status, r.data.decode())

def testDelete():
    """ return 204, 404, 403
    """
    # login as z
    fields = {"username": "z", "password": "123"}
    r = http.request("POST", auth + "/users/login", fields = fields)
    assert(r.status == 200)
    #print(r.status, r.data.decode())
    token = r.data.decode()

    # we post some url, return 201
    headers = {"Authorization": "Bearer " + token}
    r = http.request("POST", shortner, headers = headers, fields = {"url": "https://github.com/VlouingKloud/websysasg1"})
    assert(r.status == 201)
    print(r.status, r.data.decode())

    short = r.data.decode()

    # delete, return 204
    headers = {"Authorization": "Bearer " + token}
    r = http.request("DELETE", shortner + "/" + short, headers=headers)
    assert(r.status == 204)

    # return 403
    headers = {"Authorization": "Bearer " + "z.z.z"}
    r = http.request("DELETE", shortner + "/" + short, headers=headers)
    assert(r.status == 403)
    print(r.status, r.data.decode())

def testPut():
    """ return 200, 403, 404, 400
    """
    # login as z
    fields = {"username": "z", "password": "123"}
    r = http.request("POST", auth + "/users/login", fields = fields)
    assert(r.status == 200)
    #print(r.status, r.data.decode())
    token = r.data.decode()

    # we post some url, return 201
    headers = {"Authorization": "Bearer " + token}
    r = http.request("POST", shortner, headers = headers, fields = {"url": "https://github.com/VlouingKloud/websysasg1"})
    assert(r.status == 201)
    print(r.status, r.data.decode())

    short = r.data.decode()

    # put, return 200
    headers = {"Authorization": "Bearer " + token}
    r = http.request("PUT", shortner + "/" + short, headers=headers, fields = {"url": "https://urllib3.readthedocs.io/en/stable/"})
    assert(r.status == 200)
    print(r.status, r.data.decode())

    headers = {"Authorization": "Bearer " + "z.z.z"}
    r = http.request("PUT", shortner + "/" + short, headers=headers, fields = {"url": "https://urllib3.readthedocs.io/en/stable/"})
    assert(r.status == 403)
    print(r.status, r.data.decode())

def testGet():
    """ return 200, 403
    """
    # login as z
    fields = {"username": "z", "password": "123"}
    r = http.request("POST", auth + "/users/login", fields = fields)
    assert(r.status == 200)
    #print(r.status, r.data.decode())
    token = r.data.decode()

    # we post some url, return 201
    headers = {"Authorization": "Bearer " + token}
    r = http.request("POST", shortner, headers = headers, fields = {"url": "https://github.com"})
    assert(r.status == 201)
    print(r.status, r.data.decode())

    # return 200
    headers = {"Authorization": "Bearer " + token}
    r = http.request("GET", shortner, headers=headers)
    assert(r.status == 200)
    print(r.status, r.data.decode())

    # return 403
    headers = {"Authorization": "Bearer " + "z.z.z"}
    r = http.request("GET", shortner, headers=headers)
    assert(r.status == 403)
    print(r.status, r.data.decode())

import os
import time

def main():
    # lets start with a few real URLs
    urls = ["https://en.wikipedia.org/wiki/URL",
            "https://github.com/VlouingKloud/websysasg1",
            "https://duckdb.org/internals/storage",
            "https://urllib3.readthedocs.io/en/stable/",
            "https://www.uva.nl/en",
            "https://app.diagrams.net/"]

    tests = [testPostUsers, testPutUser, testPostLogin, testPostUrl, testDelete, testPut, testGet]
    for f in tests:
        print(">>> running ", f.__name__)
        f()
        print(">>> okay")
        input()
        os.system("clear")

main()
