import random
import string
import urllib3

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


def testHashUniformity(n = 100000):
    urls = genURLList(n)
    http = urllib3.PoolManager()
    for url in urls:
        r = http.request("POST", "http://127.0.0.1:5000", fields={'url': url})

    r = http.request("GET", "http://127.0.0.1:5000")
    print(len(r.data.decode().split())/n)
