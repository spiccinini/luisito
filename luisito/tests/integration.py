#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import socket

from twisted.trial import unittest
from twisted.python import failure
from twisted.internet import defer, reactor

from twisted.web import client
from twisted.web.http_headers import Headers


from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent
from twisted.web.http_headers import Headers

PORT = 8080
DOMAINS = ["http://test%d:%d/" % (i, PORT) for i in range(5, 11)]

agent = client.Agent(reactor)

DOMAINS_TO_QUERY = DOMAINS * 3

deferreds = [agent.request('GET', domain, bodyProducer=None) for domain in DOMAINS_TO_QUERY]

class BeginningPrinter(Protocol):
    def __init__(self, finished):
        self.finished = finished
        self.remaining = 1024 * 10

    def dataReceived(self, bytes):
        if self.remaining:
            display = bytes[:self.remaining]
            print 'Some data received:'
            print display
            self.remaining -= len(display)

    def connectionLost(self, reason):
        print 'Finished receiving body:', reason.getErrorMessage()
        self.finished.callback(None)


def cbResponse(response):
    print response._state
    print response.code
    print response.phrase
    print response.length
    print response._bodyBuffer

    finished = defer.Deferred()
    response.deliverBody(BeginningPrinter(finished))
    return finished

for d in deferreds:
    d.addCallback(cbResponse)

def cbShutdown(ignored):
    reactor.stop()

reactor.run()
