#!/usr/bin/env python
"""Receive SMTP messages and route them to S3 storage."""
import signal
import time

from aiosmtpd.controller import Controller

import smtp2s3
from smtp2s3.handler import Handler

config = smtp2s3.EnvironmentConfig()
logger = smtp2s3.get_logger('smtp2s3')
logger.setLevel(config.log_level)


if __name__ == '__main__':
    running = True

    def signal_handler(sig, frame) -> None:
        """Handle signals so that we know when to stop."""
        global running
        running = False

    try:
        handler = Handler(config, logger)
        msg = f'v{smtp2s3.__version__} listening on '
        msg += f'{config.smtp_hostname}:{config.smtp_port}'
        logger.info(msg)

        controller = Controller(
            handler,
            hostname=config.smtp_hostname,
            port=config.smtp_port,
            data_size_limit=config.smtp_data_size_limit
        )
        controller.start()
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    except Exception as ex:
        logger.debug(ex)

    while running:
        time.sleep(1)

    logger.warning('Closing down SMTP.')
    controller.stop()
