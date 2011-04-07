=======
Luisito
=======

Luisito is a reverse proxy that spawns application servers on demand. It should
be used when a lot (maybe thousands) of low traffic sites are deployed.

Luisito is written in Python using the Twisted framework and should scale nicely.
It's tested in Python 2.6 and 2.7.

This software is GPLv3, see LICENSE.txt.

Rationale
=========

Sometimes you need to deploy a lot of low traffic sites that need an application server
(no multi tenancy), like Django's or Ruby on Rails's sites. Conservatively, each of
this servers usually need between 15 and 50 MB of RAM. So, for 200 simple forum
sites with only a few requests a day, you spend ~5GB of RAM.

It's insane to keep all servers alive all the time!.

How it works
============

When Luisito gets a request, it will spawn an application server based on the
domain and a command template that's rendered using the domain. To get an idea,
a template should look like:

Paragraph::

  CMD_TPL = ["/bin/django_http_server.py", "--host", "127.0.0.1", "--port", "%PORT",
             "/var/www/%HOST/django_project/"]

``%HOST`` and ``%PORT`` are replaced by the domain name and a free available
port at the time.

So Luisito will spawn the server and save the PID of the process and domain name
in a LRU cache. Then it will pass the request and return the response like a normal
reverse proxy.

When a new request arrive, Luisito looks at it cache, if the domain is alive
it will pass the request. Otherwise it will spawn it and cache it like before.

If more than ``MAX_SERVERS`` are alive, Luisito will kill the least recent used.
So in normal conditions there should be always ``MAX_SERVERS`` alive.

Features
========

* Asynchronous
* Django works out of the box.
* Configurable environmental variables (to work with virtualenv, etc).
* Can change uid an gid of spawned server.
* It looks in a configurable header so the frontend server can write the canonical
  domain name. Eg: www.domain.com -> domain.com


Deploy
======

Luisito should be deployed behind a reverse proxy, like Nginx, Apache, HAProxy,
so only application request get to it. All media, and static files should be
handled by a real web server (nginx, apache, etc).

There's a .tac file to use with twistd command to demonize Luisito. This
.tac looks for a settings.py file. Luisito comes with that settings file with
some examples.

wsgiref
-------

Django
~~~~~~

Luisito comes with a http server (``luisito/utils/django_http_server.py``) that runs Django
using ``wsgiref.simple_server``. This is currently the recommended way of running a
Django site, mostly because other ways were not yet investigated deeply.

gunicorn
--------

This kind of application servers that spawns it's own processes are not encouraged
because more RAM will be spent and no testing was made. It could be used in cases
where you have lot of requests for a single domain at a time, configuring gunicorn
to spawn more than one worker.


Your App Server (Mongrel, Unicorn, Gevent, etc)
-----------------------------------------------

It's recommended to run an application server that could handle more than one request
at a time in an asynchronous way. Theoretically it should work better than a blocking
one. Also threaded servers are encouraged instead of forking servers.


SimpleHTTPServer
----------------

For testing could be used Python's built in ``SimpleHTTPServer``. Take a look at
``settings.py.example``

How to run
==========

twistd
------

Edit ``settings.py.sample`` and save it to ``settings.py``.

Demonized
~~~~~~~~~

``twistd -y luisito.tac``

Not demonized
~~~~~~~~~~~~~

``twistd -y luisito.tac -n``

Standalone
----------

``./run.py  SimpleHTTPServer``


Todo
====

* Investigate async applications servers, like Gevent, Tornado, Twisted web, etc.
* Add a Gevent or any other async server example to handle Django, etc.
* Decouple gathering of uid and gid from ServerPool and provide a way to customize
  this functionality.
* Provide a way to configure allowed domains to forward.
* Add alias capability to domains.
* Command template should be customizable by domain.
* Tries to get a spawning server should use a time factor to try geometrically and not
  spaced in constant time.
* ENV should be configurable so each domain could have it's own virtualenv.
* Add setup.py and upload to pypi.

Authors
=======

Luisito main developer is Santiago Piccinini: piccinini <dot> santiago <at> gmail.
Initial code was written by Nicolás Echániz and Santiago Piccinini.

Many thanks to all pythonistas at PyAr that stretched it's heads at PyCon Argentina
2010 on this issue. Special thanks to Roberto Alsina, Facundo Batista,
Alejando J. Cura, Diego Mascialino and Lucio Torre for brainstorming and/or
Twisted support.
