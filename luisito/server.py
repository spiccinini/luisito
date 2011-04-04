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

import os
import stat
import socket
import subprocess

from twisted.internet import defer, threads
from twisted.python import log

def find_open_port(starting_from=9000, exclude=None):
    """
    Finds a free port.
    """
    host = '127.0.0.1'
    port = starting_from
    while 1:
        if exclude:
            if port in exclude:
                port += 1
                continue
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind((host, port))
        except socket.error, e:
            port += 1
        else:
            s.close()
            return port


class ServerPool(object):
    def __init__(self, cmd_tpl, env=None, project_path_tpl="", max_servers=10):
        self.max_servers = max_servers
        self.cmd_tpl = cmd_tpl
        self.env = env
        self.project_path_tpl = project_path_tpl
        self.alive = []
        self.ports_in_use = set()

    def get_server(self, hostname):
        if self.is_alive(hostname):
            server = self._get_server(hostname)
            actual_index = self.alive.index(server)
            self.alive.pop(actual_index)
            self.alive.append(server)
        else:
            port = find_open_port(exclude=self.ports_in_use)
            self.ports_in_use.add(port)
            cmd = self.make_command(hostname, port)
            server = Server(hostname, port, cmd, self.env)
            self.alive.append(server)
        self.update()
        return server

    def make_command(self, host, port):
        command = self.cmd_tpl[:]
        if self.project_path_tpl:
            s = os.stat(self.project_path_tpl.replace("%HOST", host))
            uid = str(s[stat.ST_UID])
            gid = str(s[stat.ST_GID])
            command = [item.replace("%UID", uid).replace("%GID", gid) for item in command]

        return [item.replace("%HOST", host).replace("%PORT", str(port)) for item in command]

    def update(self):
        if len(self.alive) > self.max_servers:
            server = self.alive.pop(0)
            server.proc.terminate()
            server.proc.wait()
            self.ports_in_use.discard(server.port)
            #threads.deferToThread(ServerPool.terminate_server, server)

    def stop_all(self):
        for server in self.alive:
            server.proc.terminate()
            server.proc.wait()
        self.alive = []

    def is_alive(self, hostname):
        return hostname in (server.hostname for server in self.alive)

    def _get_server(self, hostname):
        for server in self.alive:
            if server.hostname == hostname:
                return server

    def terminate_server(self, server):
        server.proc.terminate()
        server.proc.wait()
        self.ports_in_use.discard(server.port)

    def __repr__(self):
        return repr(self.alive)


class Server(object):
    def __init__(self, hostname, port, cmd, env):
        self.hostname = hostname
        self.port = port
        self.cmd = cmd
        self.env = env
        self.proc = subprocess.Popen(cmd, env=self.env)

    def __repr__(self):
        return "Server %s:%d PID:%s" % (self.hostname, self.port, self.proc.pid)