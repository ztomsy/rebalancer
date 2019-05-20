#!/usr/bin/env python
# encoding: utf-8
import time
import sys

import _settings
from payload.runner import Runner
from core import logger


# Parse settings file for
settings = {attr: getattr(_settings, attr) for attr in dir(_settings) if not callable(getattr(_settings, attr)) and
            not attr.startswith("__")}

# Init logger and define log_level verbosity
logger = logger.setup_custom_logger('Rebalancer', log_level=settings['LOG_LEVEL'])

if __name__ == '__main__':
    start = time.time()
    # Try/except just keeps ctrl-c from printing an ugly stacktrace
    try:
        market1 = Runner(logger=logger, **settings)
    except (KeyboardInterrupt, SystemExit):
        logger.info('Rebalancer stop working after %.2f minutes' % ((time.time() - start) / 60))
    except Exception:
        logger.error("Stop main loop for next reason:", exc_info=True)

    sys.exit()
