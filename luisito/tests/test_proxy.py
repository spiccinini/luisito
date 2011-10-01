#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import socket

from twisted.trial import unittest
from twisted.python import failure
from twisted.internet import defer, reactor
from twisted.web import server, client
from twisted.web.client import Agent, getPage
from twisted.web.http_headers import Headers

from luisito.server import Server, ServerPool
from luisito.proxy import MultiHostBasedResource, MHProxyClientFactory

class MultiHostTestCase(unittest.TestCase):

    def testOneHost(self):
        cmd_tpl = ["python2", "-m", "SimpleHTTPServer", "%PORT"]
        server_pool = ServerPool(cmd_tpl=cmd_tpl)

        multi_host = MultiHostBasedResource(server_pool=server_pool, config=None)

        site = server.Site(multi_host)

        list_port = reactor.listenTCP(interface="127.0.0.1", port=8000, factory=site)

        agent = Agent(reactor)

        d = defer.Deferred()

        d.addCallback(getPage)

        def cbResponse(page_content):
            self.assertTrue("Directory listing for" in page_content)

        d.addCallback(cbResponse)

        d.addCallback(list_port.stopListening)

        def request(d):
            d.callback("http://127.0.0.1:8000")

        reactor.callLater(1, request, d)

        return d

