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

import os
import stat
import socket
import subprocess

import twisted

from twisted.web.server import NOT_DONE_YET
from twisted.web import proxy, server, client
from twisted.python import log, failure
from twisted.internet import reactor, defer
from twisted.internet.task import LoopingCall
from twisted.internet.error import ConnectionRefusedError
from twisted.internet.defer import Deferred, inlineCallbacks


log.info = lambda s:log.msg("INFO: %s" % (s,))
log.debug = lambda s:log.msg("DEBUG: %s" % (s,))
log.error = lambda s:log.msg("ERROR: %s" % (s,))

class Server(object):
    def __init__(self, hostname, port=None, proc=None):
        self.hostname = hostname
        self.port = port
        self.proc = proc

    def __repr__(self):
        return "Server %s:%d PID:%s" % (self.hostname, self.port, self.proc.pid)

    def __eq__(self, value):
        return self.hostname == value

    def __ne__(self, value):
        return self.hostname != value


class ServerPool(object):
    alive = []
    waking_up = set()
    ports_in_use = set()
    MAX_SERVERS = 10

    @classmethod
    def update(cls):
        if len(cls.alive) > cls.MAX_SERVERS:
            server = cls.alive.pop(0)
            server.proc.terminate()
            server.proc.wait()
            cls.ports_in_use.discard(server.port)
    @classmethod
    def stop_all(cls):
        for server in cls.alive:
            server.proc.terminate()
            server.proc.wait()
        cls.alive = []

    @classmethod
    def is_alive(cls, hostname):
        return hostname in cls.alive

    @classmethod
    def is_waking_up(cls, hostname):
        return hostname in cls.waking_up


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
    d = Deferred()
    reactor.callLater(x, d.callback, None)
    return d


class TimeoutError(Exception):
    pass

@inlineCallbacks
def wait_open(port):
    # servers don't start up *quite* right away, so we give it a
    # moment to be ready to accept connections
    SLEEP = 0.2
    WAIT_UP_TO = 5

    for i in range(int(WAIT_UP_TO/SLEEP)):
        try:
            yield client.getPage("http://127.0.0.1:%s/" % port, followRedirect=False)
        except twisted.web.error.Error, e:
            # This could be that the server is geting 404, 500, etc so server is up
            # and running.
            return

        except ConnectionRefusedError:
            yield wait_for(SLEEP)
        else:
            return
    raise TimeoutError

@inlineCallbacks
def wait_alive(hostname):
    # servers don't start up *quite* right away, so we give it a
    # moment to be ready to accept connections
    SLEEP = 0.2
    WAIT_UP_TO = 5+SLEEP

    yield wait_for(SLEEP)
    for i in range(int(WAIT_UP_TO/SLEEP)):
        if  ServerPool.is_alive(hostname):
            pool = ServerPool.alive
            port = pool[pool.index(hostname)].port
            defer.returnValue(port)
        else:
            yield wait_for(SLEEP)
    raise TimeoutError

class HostBasedResource(proxy.ReverseProxyResource):
    def __init__(self, host, port, path, command, env=None, reactor=reactor):
        proxy.ReverseProxyResource.__init__(self, host, port, path, reactor=reactor)
        self.isLeaf = True
        self.COMMAND = command
        self.ENV = env

    def _connect(self, r, port, clientFactory):
        self.reactor.connectTCP(host="127.0.0.1", port=port, factory=clientFactory)

    def _failed_connect(self, f, request, reason="", requested_host=None, port=None):
        ServerPool.waking_up.discard(requested_host)
        if port is not None:
            ServerPool.ports_in_use.discard(port)
        request.setResponseCode(503)
        request.write("503 Error")
        request.finish()
        if reason:
            log.error(reason)
        return f

    def make_command(self, host, port):
        COMMAND = self.COMMAND[:]
        if self.PROJECT_PATH:
            s = os.stat(self.PROJECT_PATH.replace("%HOST", host))
            uid = str(s[stat.ST_UID])
            gid = str(s[stat.ST_GID])
            COMMAND = [item.replace("%UID", uid).replace("%GID", gid) for item in COMMAND]

        return [item.replace("%HOST", host).replace("%PORT", str(port)) for item in COMMAND]

    def render(self, request):
        """
        Render a request by forwarding it to the proxied server.
        """
        requested_host = request.received_headers['host'].partition(":")[0]
        log.info("New request: %s" % (requested_host,))
        request.content.seek(0, 0)
        clientFactory = self.proxyClientFactoryClass(
            request.method, request.uri , request.clientproto,
            request.getAllHeaders(), request.content.read(), request)

        if not (ServerPool.is_alive(requested_host) or ServerPool.is_waking_up(requested_host)):
            ServerPool.waking_up.add(requested_host)
            log.info("requested_host not found in ServerPool.alive nor ServerPool.waking_up")
            log.debug("Adding requested_host to ServerPool.waking_up")
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
                           callbackArgs=(port, clientFactory), errbackArgs=(request, "TimeoutError in wait_open", requested_host, port))
            d.addCallback(lambda _: ServerPool.waking_up.discard(requested_host))
            d.addCallback(lambda _: ServerPool.alive.append(Server(requested_host, port, proc)))
            d.addCallback(lambda _: log.debug("ServerPool.alive: %s" % (ServerPool.alive, )))
        elif requested_host in ServerPool.waking_up:
            log.info("requested_host found in ServerPool.waking_up")
            log.debug("waiting process")
            port = wait_alive(requested_host)
            port.addCallback(lambda port_: self._connect(port, port_, clientFactory))
            port.addErrback(self._failed_connect, request, "TimeoutError in wait_alive", requested_host)
        else:
            if requested_host in ServerPool.waking_up:
                d = wait_alive(requested_host)
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
