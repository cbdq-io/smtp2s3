"""A module for receiving SMTP messages and loading onto S3."""
import logging
import os
import re

__version__ = '0.1.0'


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for use in the app.

    Parameters
    ----------
    name : str
        The name of the logger.

    Returns
    -------
    logging.Logger
        A logger than can be used by the app.
    """
    logging.basicConfig()
    return logging.getLogger(name)


class EnvironmentConfig:
    """
    Extract the configuration from environment variables.

    Attributes
    ----------
    log_level : int
        The log level to run at.
    smtp_data_size_limit : int
        The maximum size in bytes for a message to be accepted.
    smtp_hostname : str
        The hostname to listen on for SMTPD.
    smtp_port : int
        The port number to listen on for SMTPD.
    smtp_rcpt_regex : re.Pattern
        The compiled regex to match recipient emails against.

    Parameters
    ----------
    environ : dict, optional
        The dictionary/environment to browse for settings from,
        by default os.environ.
    """

    def __init__(self, environ: dict = os.environ) -> None:
        self._environ = environ
        self.aws_access_key_id = environ.get('AWS_ACCESS_KEY_ID', None)
        self.aws_secret_access_key = environ.get('AWS_SECRET_ACCESS_KEY', None)
        self.log_level = self._get_log_level()
        self.s3_endpoint_url = environ.get('S3_ENDPOINT_URL', None)
        self.s3_prefix_pattern = environ.get('S3_PREFIX_PATTERN')
        self.smtp_data_size_limit = int(
            environ.get(
                'SMTP_DATA_SIZE_LIMIT',
                str(10 * 1024 * 1024)
            )
        )
        self.smtp_hostname = environ.get('SMTP_HOSTNAME', '127.0.0.1')
        self.smtp_port = int(environ.get('SMTP_PORT', '8025'))
        default_regex = """
        (?:[\u00A0-\uD7FF\uE000-\uFFFFa-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\\.[\u00A0-\uD7FF\uE000-\uFFFFa-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[\u00A0-\uD7FF\uE000-\uFFFFa-z0-9](?:[\u00A0-\uD7FF\uE000-\uFFFF-a-z0-9-]*[\u00A0-\uD7FF\uE000-\uFFFFa-z0-9])?\\.)+[\u00A0-\uD7FF\uE000-\uFFFFa-z0-9](?:[\u00A0-\uD7FF\uE000-\uFFFFa-z0-9-]*[\u00A0-\uD7FF\uE000-\uFFFFa-z0-9])?|\\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\\.){3}\\])
        """.replace(' ', '')
        self.smtp_rcpt_regex = re.compile(
            environ.get(
                'SMTP_RECIPIENT_REGEX',
                default_regex
            )
        )

    def _get_log_level(self) -> int:
        """
        Get what the log level should be.

        Returns
        -------
        int
            One of the fixed values from logging.

        Raises
        ------
        ValueError
            If the log level provided is not valid.
        """
        log_level_name = self._environ.get('LOG_LEVEL', 'WARN')
        level_names_mapping = logging.getLevelNamesMapping()

        try:
            log_level = level_names_mapping[log_level_name]
        except KeyError:
            valid_names = ', '.join(level_names_mapping.keys())
            message = f'Environment LOG_LEVEL ("{log_level_name}") is '
            message += f'invalid.  Must be one of {valid_names}.'
            raise ValueError(message)

        return log_level
