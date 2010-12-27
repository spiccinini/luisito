import os
import sys

from twisted.application import internet, service
from twisted.application.internet import TimerService
from twisted.web import server


sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

from luisito import HostBasedResource, ServerPool
import settings


ServerPool.MAX_SERVERS = settings.MAX_SERVERS

application = service.Application('luisito')
serviceCollection = service.IServiceCollection(application)

time_service = TimerService(0.2, ServerPool.update)
time_service.setServiceParent(serviceCollection)

resource = HostBasedResource("", 80, '', command=settings.CMD, env=settings.ENV)
resource.PROJECT_PATH = settings.PROJECT_PATH
site = server.Site(resource)
tcp_server = internet.TCPServer(interface=settings.HOST, port=settings.PORT, factory=site)
tcp_server.setServiceParent(serviceCollection)

class StartStopService(service.Service):
    def stopService(self):
        service.Service.stopService(self)
        print 'killing workers'
        ServerPool.stop_all()


start_stop = StartStopService()
start_stop.setServiceParent(serviceCollection)

