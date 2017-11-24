import os, json, errno
import logging

""" NULLHANDLER instead of logging.NullHandler in python ver < 2.7
"""
# set a manual handler for elasticsearch.trace.
# below is just a hack to ignore trace logs. Tracing is enabled with DEBUG level in main logger.
# Python 2.6 does not have logging.NullHandler. It is available from Python 2.7.
# defining a manual class until Python <= 2.7
try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

tracer = logging.getLogger('elasticsearch.trace')
#tracer.setLevel(logging.CRITICAL)
tracer.addHandler(NullHandler())

""" LOGGER intialization. Main configuration for script logs.
"""
class Logger:
  def setup_logging(self,
      defaultLogConfFile='logging.config',
      defaultLevel=logging.INFO,
      envKey='LOG_CFG'
                   ):
      """Setup logging configuration
      """
      path = defaultLogConfFile
      value = os.getenv(envKey, None)
      if value:
         path = value
      try:
          os.makedirs('logs')
      except OSError as exception:
         if exception.errno != errno.EEXIST:
            raise exception

      if os.path.exists(path):
         with open(path, 'rt') as f:
              config = json.load(f)
         # for backward compatibility
         # using external logutils.dictconfig for python < 2.6
         try:
           from logging.config import dictConfig
           dictConfig(config)
         except Exception,e:
           from logutils.dictconfig import dictConfig
           dictConfig(config)
      else:
         logging.basicConfig(level=defaultLevel)
  # DECORATOR for a logger functionality
  def logwrap(self,actualFunction):
     def loggerLocal(*args,**kwargs):
         self.setup_logging()
         return actualFunction(*args,**kwargs)
     return loggerLocal
