
from twisted.application import internet, service
from twisted.application.internet import TimerService
from twisted.web import server

from luisito import HostBasedResource, ServerPool
import settings


ServerPool.MAX_SERVERS = settings.MAX_SERVERS

application = service.Application('luisito')
serviceCollection = service.IServiceCollection(application)

time_service = TimerService(0.2, ServerPool.update)
time_service.setServiceParent(serviceCollection)

site = server.Site(HostBasedResource("", 80, '', command=settings.CMD))
tcp_server = internet.TCPServer(interface=settings.HOST, port=settings.PORT, factory=site)
tcp_server.setServiceParent(serviceCollection)