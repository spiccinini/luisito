import os
import sys

from twisted.application import internet, service
from twisted.application.internet import TimerService
from twisted.web import server


sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

from luisito.server import ServerPool
from luisito.proxy import MultiHostBasedResource

import settings

application = service.Application('luisito')
serviceCollection = service.IServiceCollection(application)

if not os.path.exists(settings.OUTPUT_LOG_DIR):
    os.makedirs(settings.OUTPUT_LOG_DIR)


server_pool = ServerPool(cmd_tpl=settings.CMD_TPL, env=settings.ENV,
                         project_path_tpl=settings.PROJECT_PATH,
                         max_servers=settings.MAX_SERVERS,
                         output_log_dir=settings.OUTPUT_LOG_DIR)

multi_host = MultiHostBasedResource(server_pool=server_pool, config=settings.MULTIHOST_CONFIG)

site = server.Site(multi_host)

tcp_server = internet.TCPServer(interface=settings.HOST, port=settings.PORT, factory=site)
tcp_server.setServiceParent(serviceCollection)

class StartStopService(service.Service):
    def stopService(self):
        service.Service.stopService(self)
        print 'killing workers'
        server_pool.stop_all()


start_stop = StartStopService()
start_stop.setServiceParent(serviceCollection)

