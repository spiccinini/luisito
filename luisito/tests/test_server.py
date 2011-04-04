#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import socket

from twisted.trial import unittest
from twisted.python import failure
from twisted.internet import defer, reactor

from luisito.server import Server, ServerPool, find_open_port


class ServerTestCase(unittest.TestCase):
    """
    Test Server.
    """
    tmp_file = "test_file"

    def testServerSimpleCMD(self):
        server = Server(hostname="localhost", port=None, cmd=["touch", self.tmp_file], env=None)
        d = defer.Deferred()
        reactor.callLater(0.1, d.callback, None)
        return d.addCallback(lambda _: self.assertTrue(os.path.exists(self.tmp_file)))

    def testFindOpenPort(self):
        """
        Test requesting an open port, binding to it, and then requesting
        another.
        """
        port = find_open_port(9000)
        self.assertTrue(port >= 9000)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("localhost", port))

        another_port = find_open_port(9000)
        self.assertTrue(another_port > port)
        s.close()


    def tearDown(self):
        if os.path.exists(self.tmp_file):
            os.remove(self.tmp_file)


class ServerPoolTestCase(unittest.TestCase):
    pass
    #def testAddServer(self):
    #    server_pool = ServerPool(cmd_tpl=["echo", "test"])
    #    import subprocess
    #    subprocess.Popen = Popen
    #    server_pool.get_server("test.luisito.org")

