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

import twisted.web
from twisted.python import log
from twisted.internet import reactor

from luisito.server import ServerPool
from luisito.proxy import MultiHostBasedResource


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description='',
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('server', choices=('django', 'SimpleHTTPServer'), help='server type to proxy')
    parser.add_argument('--host', default="", help='server hostname.')
    parser.add_argument('--port', default=8080, type=int, help='server port')
    parser.add_argument('--max-servers', default=10, type=int)

    args = parser.parse_args()

    if args.server == "django":
        cmd_tpl = ["./luisito/utils/django_http_server.py", "--host", "127.0.0.1", "--port", "%PORT",
               "/home/san/somecode/luisito/django_projects/%HOST/project/"]
    elif args.server == "SimpleHTTPServer":
        cmd_tpl = ["python2", "-m", "SimpleHTTPServer", "%PORT"]

    server_pool = ServerPool(cmd_tpl=cmd_tpl, env=None, project_path_tpl="",
                             max_servers=args.max_servers)


    multi_host = MultiHostBasedResource(server_pool=server_pool, config=None)

    site = twisted.web.server.Site(multi_host)

    reactor.listenTCP(interface=args.host, port=args.port, factory=site)

    log.startLogging(open('luisito.log', 'a'))

    reactor.run()

    server_pool.stop_all()
