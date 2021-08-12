#!/usr/bin/env python
# encoding: utf-8
import time
import sys
from logging import DEBUG

from yat.settingsWatcher import settingsWatcher
from payload.runner import Runner
from yat import logger

watcher = settingsWatcher()
settings = watcher.settings

logger = logger.setup_custom_logger('Rebalancer', log_level=DEBUG)


if __name__ == '__main__':
    start = time.time()
    try:
        market1 = Runner(logger=logger, watcher=watcher, **settings)
    except Exception:
        logger.error("Stop main loop for next reason:", exc_info=True)
    except (KeyboardInterrupt, SystemExit):
        logger.info('Rebalancer stop working after %.2f minutes'.format(((time.time() - start) / 60)))
    sys.exit()
