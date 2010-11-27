#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010 Santiago Piccinini.
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
import sys
import argparse

from wsgiref.simple_server import make_server
from django.core.handlers.wsgi import WSGIHandler


parser = argparse.ArgumentParser(description='Serve django using wsgiref.simple_server',
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('PATH', help='absolute path to Django project')
parser.add_argument('--host', default="0.0.0.0", help='server hostname.')
parser.add_argument('--port', default=8000, type=int,
                    help='server port')
parser.add_argument('--settings', default="settings",
                    help='Django settings, relative to PATH')

args = parser.parse_args()
sys.path.insert(0, args.PATH)

base_path = os.path.split(os.path.normpath(args.PATH))[0]
sys.path.insert(0, base_path) # FIXME: django import project.urls, how to get project in sys.path?

os.environ['DJANGO_SETTINGS_MODULE'] = args.settings

#import pdb;pdb.set_trace()
httpd = make_server(args.host, args.port, WSGIHandler())
httpd.serve_forever()
