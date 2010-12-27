
HOST = "127.0.0.1"
PORT = 8080
MAX_SERVERS = 10

# django-cyclope:
CMD = ["./django_http_server.py", "--host", "127.0.0.1", "--port", "%PORT", "--uid",
       "%UID", "--gid", "%GID",
       "/home/san/somecode/cyclope/cyclope_workenv/src/cyclope/%HOST/cyclope_project/"]

ENV = {"PATH": "/home/san/somecode/cyclope/cyclope_workenv/bin/"}

# Change UID and GID to the owners of PROJECT_PATH
PROJECT_PATH = "/home/san/somecode/cyclope/cyclope_workenv/src/cyclope/%HOST/cyclope_project/"




# SimpleHTTPServer
# cmd = ["python2", "-m", "SimpleHTTPServer", "%PORT"]


