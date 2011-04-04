
HOST = "0.0.0.0"
PORT = 8080
MAX_SERVERS = 10

##################
# SimpleHTTPServer
#
CMD_TPL = ["python2", "-m", "SimpleHTTPServer", "%PORT"]
ENV = {}
MULTIHOST_CONFIG = None
PROJECT_PATH = None

################
# django-cyclope
#
#CMD_TPL = ["/opt/luisito/django_http_server.py", "--host", "127.0.0.1", "--port", "%PORT",
#           "--uid", "%UID", "--gid", "%GID",
#           "/var/www/%HOST/cyclope_project/"]
#
#
#ENV = {
#    "PATH": "/opt/cyclope_workenv/bin",
#}

#MULTIHOST_CONFIG = {
#    "host_header": "x-canonical-host",
#    "sleep":0.2,
#    "wait_up_to":5,
#}

# Change UID and GID to the owners of PROJECT_PATH
#PROJECT_PATH = "/var/www/%HOST/cyclope_project/"




