
HOST = "127.0.0.1"
PORT = 8080
MAX_SERVERS = 10

# Django:
CMD = ["./django_http_server.py", "--host", "127.0.0.1", "--port", "%PORT",
       "/home/san/somecode/luisito/django_projects/%HOST/project/"]

# SimpleHTTPServer
# cmd = ["python2", "-m", "SimpleHTTPServer", "%PORT"]

