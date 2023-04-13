"""
This script is used to demostrate our service.
"""

import random
import string
import urllib3

http = urllib3.PoolManager()
addr = "http://172.17.0.3:12345"

def genURLList(n = 100000):
    top_lvl = (".com", ".org", ".net", ".int", ".edu", ".gov", ".mil")
    snd_lvl = (".cn", ".nl", ".eu", ".at", ".ch", ".uk", "","","","","","","","")
    alphabet = string.ascii_letters + string.digits
    urlbase = "https://www.{}{}{}"
    postfix = "/{}"
    res = []
    for i in range(n):
        len1 = random.randint(1, 20)
        len2 = random.randint(0, 30)
        dn = ''.join(random.choices(string.ascii_lowercase + string.digits, k=len1))
        temp = urlbase.format(dn, random.choice(top_lvl), random.choice(snd_lvl))
        if len2 > 0:
            temp += postfix.format(''.join(random.choices(alphabet, k=len2)))
        res.append(temp)
    return res

def testGetID(id, expected = 200):
    r = http.request("GET", addr + "/" + id)
    assert(r.status == expected)
    return r

def testPutID(id, url, expected = 200):
    r = http.request("PUT", addr + "/" + id, fields={'url': url})
    assert(r.status == expected)
    return r.data.decode()

def testDeleteID(id, expected = 204):
    r = http.request("DELETE", addr + "/" + id)
    assert(r.status == expected)
    return r.data.decode()

def testDelete(expected = 404):
    r = http.request("DELETE", addr)
    assert(r.status == expected)
    return r.data.decode()

def testGet(expected = 200):
    r = http.request("GET", addr)
    assert(r.status == expected)
    return r.data.decode()

def testPost(url, expected = 200):
     r = http.request("POST", addr, fields={'url': url})
     assert(r.status == expected)
     return r.data.decode()

def testStat(expected = 200):
    r = http.request("GET", addr + "/" + "stat")
    assert(r.status == expected)
    return r.data.decode()

def main(n = 20000):
    # lets start with a few real URLs
    urls = ["https://en.wikipedia.org/wiki/URL",
            "https://github.com/VlouingKloud/websysasg1",
            "https://duckdb.org/internals/storage",
            "https://urllib3.readthedocs.io/en/stable/",
            "https://www.uva.nl/en",
            "https://app.diagrams.net/"]

    # now lets post them to / to generate shorts
    for url in urls:
        res = testPost(url, 200)
    # maybe lets print just one result?
    print("--> The result of post {} to /".format(urls[-1]))
    print(res)

    # let's do a get /
    res = testGet()
    print("--> The result of get /")
    print(res)

    # time to resolve an ID
    selectedID = random.choice(res.split())
    url = testGetID(selectedID)
    print("--> The result of get /{}".format(selectedID))
    print(url.geturl())

    # put time
    url = "https://quanjude.com.cn/"
    r = testPutID(selectedID, url)
    print("--> The result of put /{}".format(selectedID))
    print(r)

    # resolve again?
    url = testGetID(selectedID)
    print("--> The result of get /{}".format(selectedID))
    print(url.geturl())

    # delete an ID
    r = testDeleteID(selectedID)
    print("--> The result of delete /{}".format(selectedID))
    print(r)

    # get the deleted ID
    url = testGetID(selectedID, 404)
    print("--> The result of get /{}".format(selectedID))
    print(url.status)

    # do some stat
    url = testStat()
    print("--> The result of get /stat")
    print(url)

    # uo, delete all? danger! danger! danger!
    url = testDelete()
    print("--> The result of delete /")
    print(url)

    # do some stat
    url = testStat()
    print("--> The result of get /stat")
    print(url)

    z = input("--> do something interesting?")
    if z != "y":
        return 0

    print("generating {} urls".format(n))

    urls = genURLList(n)

    print("posting to /")
    for url in urls:
        r = http.request("POST", addr, fields={'url': url})

    print("getting keys")

    r = http.request("GET", addr)
    shorts = r.data.decode().split()
    print("Generated {} short IDs from {} URLs".format(len(shorts), n))

    c = 7

    print("selecting {} keys".format(c))
    selectedID = random.choices(shorts, k = c)
    print("they are")
    print(selectedID)

    for i in range(500):
        r = http.request("GET", addr + "/" + random.choice(selectedID), redirect = False)

    r = http.request("GET", addr + "/" + "stat/{}".format(c+ 5))
    print(r.data.decode())


main()
