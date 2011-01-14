
HOST = "0.0.0.0"
PORT = 8080
MAX_SERVERS = 10

# django-cyclope:
CMD = ["/opt/luisito/django_http_server.py", "--host", "127.0.0.1", "--port", "%PORT",
       "--uid", "%UID", "--gid", "%GID",
       "/var/www/%HOST/cyclope_project/"]
 
ENV = {"PATH": "/opt/cyclope_workenv/bin"}


# Change UID and GID to the owners of PROJECT_PATH
PROJECT_PATH = "/var/www/%HOST/cyclope_project/"




# SimpleHTTPServer
# cmd = ["python2", "-m", "SimpleHTTPServer", "%PORT"]


