"""A module for receiving SMTP messages and loading onto S3."""
import logging
import os

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

    smtp_hostname : str
        The hostname to listen on for SMTPD.

    smtp_port : int
        The port number to listen on for SMTPD.

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
        self.smtp_hostname = environ.get('SMTP_HOSTNAME', '127.0.0.1')
        self.smtp_port = int(environ.get('SMTP_PORT', '8025'))

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
