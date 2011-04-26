from twisted.python import log

log.info = lambda s:log.msg("INFO: %s" % (s,))
log.debug = lambda s:log.msg("DEBUG: %s" % (s,))
log.error = lambda s:log.msg("ERROR: %s" % (s,))
log.warn = lambda s:log.msg("WARNING: %s" % (s,))
