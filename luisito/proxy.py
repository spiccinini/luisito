#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010, 2011 Nicolás Echániz, Santiago Piccinini.
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

from twisted.python import log
from twisted.internet import reactor, defer
from twisted.internet.defer import Deferred, inlineCallbacks
from twisted.web.proxy import ProxyClientFactory, ReverseProxyResource
from twisted.web.server import NOT_DONE_YET

DEFAULT_CONFIG = {"host_header":None, "sleep":0.2, "wait_up_to":5}

def wait_for(x):
    d = Deferred()
    reactor.callLater(x, d.callback, None)
    return d


class MHProxyClientFactory(ProxyClientFactory):
    def __init__(self, command, rest, version, headers, data, father, d):
        ProxyClientFactory.__init__(self, command, rest, version, headers, data, father)
        self.d = d

    def buildProtocol(self, addr):
        self.d.callback(True)
        return ProxyClientFactory.buildProtocol(self, addr)

    def clientConnectionFailed(self, connector, reason):
        self.d.errback(reason)


class MultiHostBasedResource(ReverseProxyResource):

    proxyClientFactoryClass = MHProxyClientFactory

    def __init__(self, server_pool, config=None, reactor=reactor):
        ReverseProxyResource.__init__(self, host="", port=80, path="", reactor=reactor)
        self.isLeaf = True
        self.server_pool = server_pool
        if config is None:
            config = DEFAULT_CONFIG
        else:
            aux = DEFAULT_CONFIG.copy()
            aux.update(config)
            config = aux
        self.config = config

    def render(self, request):
        if self.config["host_header"] is None:
            requested_host = request.received_headers['host'].partition(":")[0]
        else:
            requested_host = request.requestHeaders.getRawHeaders(self.config["host_header"])[0]
        log.info(u"new_request|%s|%s|%s" % (requested_host, request.method, request.uri))
        request.content.seek(0, 0)

        server = self.server_pool.get_server(requested_host)

        self.retry(request, server)

        return NOT_DONE_YET

    def get_page(self, request, server):
        d = defer.Deferred()
        content = getattr(request, "_content_cache", None)
        if content is None:
            content = request.content.read()
            request._content_cache = content

        clientFactory = self.proxyClientFactoryClass(
                request.method, request.uri , request.clientproto,
                request.getAllHeaders(), content, request, d)
        clientFactory.noisy = False
        reactor.connectTCP("127.0.0.1", server.port, clientFactory)
        return d

    @inlineCallbacks
    def retry(self, request, server):
        # servers don't start up *quite* right away, so we give it a
        # moment to be ready to accept connections
        sleep = self.config.get("sleep")
        wait_up_to = self.config.get("wait_up_to")
        for i in range(int(wait_up_to/sleep)):
            try:
                yield self.get_page(request, server)
                return
            except Exception,e:
                log.warn(e)
                yield wait_for(sleep)

        request.setResponseCode(501, "Gateway error")
        request.responseHeaders.addRawHeader("Content-Type", "text/html")
        request.write("<H1>Could not connect</H1>")
        request.finish()
