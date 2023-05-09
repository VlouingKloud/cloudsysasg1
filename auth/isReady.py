import urllib3
import conf
import os

if os.path.isfile("srvup"):
    exit(0)

try:
        http = urllib3.PoolManager()
        r = http.request('GET', "http://localhost:" + str(conf.PORT) + "/srvstatus")
        if r.status == 200:
            with open("srvup", "w") as f:
                f.write("ok")
            exit(0)
        exit(1)
except Exception:
        exit(2)
