import sys
from twisted.spread import pb
from twisted.internet import reactor
from twisted.python import util

def call_remote(command, args):
    factory = pb.PBClientFactory()
    reactor.connectTCP("localhost", 4444, factory)
    d = factory.getRootObject()
    d.addCallback(lambda object: object.callRemote(command, *args))
    d.addCallback(lambda cmd: 'Result: ' + cmd)
    d.addErrback(lambda reason: 'error: '+ str(reason.value))
    d.addCallback(util.println)
    d.addCallback(lambda _: reactor.stop())
    reactor.run()

HELP = """luisito_remote runs commands on a luisito server instance.
defined commands:
    * list
    * stop_server hostname

Eg: To stop remote instance
    luisito_remote.py stop_server example.com
"""

if len(sys.argv) == 1:
    print HELP
    sys.exit(1)
else:
    command = sys.argv[1]
    args = sys.argv[2:]
    call_remote(command, args)



