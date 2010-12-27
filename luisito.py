#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010 Nicolás Echániz, Santiago Piccinini.
# All rights reserved.
#
#
# luisito is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# luisito is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time
import socket
import urlparse
import subprocess
from urllib import quote as urlquote

import twisted

from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from twisted.web import proxy, server, client
from twisted.web.http import HTTPClient, Request, HTTPChannel
from twisted.python.failure import Failure
from twisted.python import log
from twisted.internet import reactor, tcp
from twisted.internet.task import LoopingCall
from twisted.internet.protocol import ClientFactory
from twisted.internet.error import ConnectionRefusedError
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue


log.info = lambda s:log.msg("INFO: %s" % (s,))
log.debug = lambda s:log.msg("DEBUG: %s" % (s,))

class Server(object):
    def __init__(self, hostname, port=None, proc=None):
        self.hostname = hostname
        self.port = port
        self.proc = proc
    def __repr__(self): return "Server %s:%d PID:%s" % (self.hostname, self.port, self.proc.pid)

    def __eq__(self, value): return self.hostname == value
    def __ne__(self, value): return self.hostname != value


class ServerPool(object):
    alive = []
    ports_in_use = set()
    MAX_SERVERS = 10

    @classmethod
    def update(cls):
        #print cls.alive, cls.ports_in_use
        if len(cls.alive) > cls.MAX_SERVERS:
            server = cls.alive.pop(0)
            server.proc.terminate()
            cls.ports_in_use.discard(server.port)
    @classmethod
    def stop_all(cls):
        for server in cls.alive:
            server.proc.terminate()
        cls.alive = []


def find_open_port(starting_from=9000):
    """
    Finds a free port.
    """
    host = '127.0.0.1'
    port = starting_from
    while 1:
        if port in ServerPool.ports_in_use:
            port += 1
            continue
        s = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind((host, port))
        except socket.error, e:
            port += 1
        else:
            s.close()
            return port

def wait_for(x):
    #print "waiting for"
    d = Deferred()
    reactor.callLater(x, d.callback, None)
    return d


class TimoutError(Exception):
    pass

@inlineCallbacks
def wait_open(port):
    # servers don't start up *quite* right away, so we give it a
    # moment to be ready to accept connections
    SLEEP = 0.2
    WAIT_UP_TO = 5

    for i in range(int(WAIT_UP_TO/SLEEP)):
        try:
            yield client.getPage("http://127.0.0.1:%s/" % port)
        except twisted.web.error.Error, e:
            # This could be that the server is geting 404, 500, etc so server is up
            # and running.
            return
        except ConnectionRefusedError:
            yield wait_for(SLEEP)
        else:
            return
    raise TimoutError

class HostBasedResource(proxy.ReverseProxyResource):
    def __init__(self, host, port, path, command, env=None, reactor=reactor):
        proxy.ReverseProxyResource.__init__(self, host, port, path, reactor=reactor)
        self.isLeaf = True
        self.COMMAND = command
        self.ENV = env

    def _connect(self, r, port, clientFactory):
        self.reactor.connectTCP(host="127.0.0.1", port=port, factory=clientFactory)

    def _failed_connect(self, f, port, reason, request):
        ServerPool.ports_in_use.discard(port)
        log.err(reason)
        request.write("505 Error")
        request.finish()
        return f

    def make_command(self, host, port):
        return [item.replace("%HOST", host).replace("%PORT", str(port)) for item in self.COMMAND]

    def render(self, request):
        """
        Render a request by forwarding it to the proxied server.
        """
        requested_host = request.received_headers['host'].partition(":")[0]
        log.info("New request: %s" % (requested_host,))
        request.content.seek(0, 0)
        clientFactory = self.proxyClientFactoryClass(
            request.method, request.path , request.clientproto,
            request.getAllHeaders(), request.content.read(), request)
        if not requested_host in ServerPool.alive:
            log.info("requested_host not found in ServerPool.alive")
            log.info("Spawning server")
            log.debug("Finding port")
            port = find_open_port()
            log.debug("Port: %d" % (port, ))
            command = self.make_command(requested_host, port)
            log.debug("command: %s" % (command, ))
            proc = subprocess.Popen(command, env=self.ENV)
            log.debug("proc: %s" % (proc.pid, ))
            log.debug("waiting process")
            d = wait_open(port)
            ServerPool.ports_in_use.add(port)
            d.addCallbacks(callback=self._connect, errback=self._failed_connect,
                           callbackArgs=(port, clientFactory), errbackArgs=(port, "TimeoutError", request))
            d.addCallback(lambda _: ServerPool.alive.append(Server(requested_host, port, proc)))
            d.addCallback(lambda _: log.debug("ServerPool.alive: %s" % (ServerPool.alive, )))
        else:
            log.info("requested_host found in ServerPool.alive")
            log.debug("Updating ServerPool.alive indexes")
            log.debug("old: ServerPool.alive: %s" % (ServerPool.alive, ))
            actual_index = ServerPool.alive.index(requested_host)
            server = ServerPool.alive.pop(actual_index)
            ServerPool.alive.append(server)
            log.debug("new: ServerPool.alive: %s" % (ServerPool.alive, ))
            self.reactor.connectTCP("127.0.0.1", server.port, clientFactory)

        return NOT_DONE_YET

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description='',
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('server', choices=('django', 'SimpleHTTPServer'), help='server type to proxy')
    parser.add_argument('--host', default="", help='server hostname.')
    parser.add_argument('--port', default=8080, type=int, help='server port')
    parser.add_argument('--workers', default=10, type=int)

    args = parser.parse_args()

    if args.server == "django":
        cmd = ["./django_http_server.py", "--host", "127.0.0.1", "--port", "%PORT",
               "/home/san/somecode/luisito/django_projects/%HOST/project/"]
    elif args.server == "SimpleHTTPServer":
        cmd = ["python2", "-m", "SimpleHTTPServer", "%PORT"]

    ServerPool.MAX_SERVERS = args.workers

    site = server.Site(HostBasedResource("", 80, '', command=cmd))

    reactor.listenTCP(interface=args.host, port=args.port, factory=site)

    lp = LoopingCall(ServerPool.update)
    lp.start(2.0)

    log.startLogging(open('luisito.log', 'a'))

    reactor.run()

    ServerPool.stop_all()
