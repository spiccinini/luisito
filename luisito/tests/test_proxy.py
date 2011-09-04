#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import socket

from twisted.trial import unittest
from twisted.python import failure
from twisted.internet import defer, reactor
from twisted.web import server, client
from twisted.web.client import Agent
from twisted.web.http_headers import Headers

from luisito.server import Server, ServerPool
from luisito.proxy import MultiHostBasedResource, MyProxyClientFactory

class MultiHostTestCase(unittest.TestCase):

    def testMultiHost(self):
        cmd_tpl = ["python", "-m", "SimpleHTTPServer", "%PORT"]
        server_pool = ServerPool(cmd_tpl=cmd_tpl)

        multi_host = MultiHostBasedResource(server_pool=server_pool, config=None)

        site = server.Site(multi_host)

        reactor.listenTCP(interface="127.0.0.1", port=8000, factory=site)

        agent = Agent(reactor)
        d = agent.request(
            'GET',
            'http://127.0.0.1:8000/',
            Headers({'User-Agent': ['Twisted Web Client Example']}),
            None)

        def cbResponse(ignored):
            print 'Response received'
        d.addCallback(cbResponse)


        d.addCallback(reactor.stopListening(8000))
        return d

    def testGetPage(self):
        pass

