import re
import datetime
from collections import defaultdict

TIME_REGEX = re.compile(".*:\d{2}")

ACTIONS = ("new_request", "start_server", "stop_server")

def parse_time(line):
    """
    Returns a datetime of the parsed time in the line. Use in twisted logs.

    >>> import datetime
    >>> orig = datetime.datetime(2011, 4, 26, 19, 6, 1)
    >>> line = "2011-04-26 19:06:01-0300 [-] Main loop terminated."
    >>> parse_time(line) == orig
    True
    """
    m = TIME_REGEX.match(line)
    if m:
        t = datetime.datetime.strptime(m.group(), "%Y-%m-%d %H:%M:%S")
        return t

def parse_action(line):
    """
    >>> line = "2011-04-26 19:02:40-0300 [HTTPChannel,3,127.0.0.1] INFO: new_request|127.0.0.1|GET|/"
    >>> parse_action(line)
    ('new_request', '127.0.0.1')
    """
    for action in ACTIONS:
        if action in line:
            hostname = line.split(action)[1].split("|")[1].strip()
            return (action, hostname)

class Server(object):
    def __init__(self, hostname, start_time):
        self.hostname = hostname
        self.start_time = start_time
        self.stop_time = None
        self.request_count = 0

    def add_request(self):
        self.request_count +=1

    def stop(self, time):
        self.stop_time = time

    def __unicode__(self):
        return self.hostname

    def __repr__(self):
        return "<Server %s>" % self.hostname

    def time_alive(self):
        if self.stop_time:
            return self.stop_time - self.start_time

if __name__ == "__main__":
    import doctest
    doctest.testmod()

    import argparse
    parser = argparse.ArgumentParser(description='',
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('logfile', type=str, help='path to log')

    args = parser.parse_args()

    server_instances = []
    servers_alive = {}

    # Parse log file
    log = open(args.logfile, "r")

    for line in log:
        try:
            time = parse_time(line)
        except ValueError:
            continue
        if "Main loop terminated" in line:
            for server in servers_alive.itervalues():
                server.stop(time)
            servers_alive = {}
        else:
            parsed_action = parse_action(line)
            if parsed_action:
                action, hostname = parsed_action
                if action == "stop_server":
                    server = servers_alive.pop(hostname)
                    server.stop_time = time
                elif action == "new_request":
                    server = servers_alive.get(hostname, None)
                    if server is None:
                        server = Server(hostname, time)
                        server_instances.append(server)
                        servers_alive[hostname] = server
                    servers_alive[hostname].add_request()

    log.close()

    for server in servers_alive.itervalues():
        server.stop(time)

    # Join parsed values
    servers = defaultdict(list)
    for server in server_instances:
        servers[server.hostname].append(server)

    class Stats(object): pass

    server_stats = {}
    # Calculate and print some statistics
    for server in servers:
        stats = Stats()
        server_stats[unicode(server)] = stats
        stats.server_name = unicode(server)
        stats.total_requests = sum([si.request_count for si in servers[server]])
        stats.time_alive = [si.time_alive() for si in servers[server]]
        stats.first_seen = sorted([si.start_time for si in servers[server]])[0]
        stats.working_time = datetime.datetime.now()-stats.first_seen
        stats.requests_per_day = 86400 * stats.total_requests / stats.working_time.total_seconds()

        timedeltas = [si.stop_time - si.start_time for si in servers[server]]
        total_seconds = sum(timedeltas, datetime.timedelta(0)).total_seconds()
        stats.avg_in_pool =  datetime.timedelta(seconds=total_seconds / float(len(timedeltas)))
    #import ipdb;ipdb.set_trace()
    for stats in sorted(server_stats.values(), key=lambda s:-s.total_requests):
        print "-"*50
        print "\t%-20s %s" % ("Server:", stats.server_name)

        # Total requests
        print "\t%-20s %d" % ("Total requests:", stats.total_requests)

        # Time alive
        print "\t%-20s %s" % ("Total time alive:", sum(stats.time_alive, datetime.timedelta(0)))

        # First seen
        print "\t%-20s %s" % ("First seen:", stats.first_seen)

        # Requests per day
        print "\t%-20s %s" % ("Req/day (stat):", stats.requests_per_day)

        # Average time in ServerPool
        print "\t%-20s %s" % ("Avg in Pool:", stats.avg_in_pool)
