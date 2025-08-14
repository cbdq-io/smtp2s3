"""A handler for use with aiosmtpd."""
import datetime
import json
import uuid
from email import message_from_bytes
from logging import Logger
from urllib.parse import urlparse

import boto3
import smart_open
from aiosmtpd.smtp import SMTP, Envelope, Session

from smtp2s3 import EnvironmentConfig

utc = datetime.timezone.utc


class Handler:
    """
    A custom SMTPD handler.

    Parameters
    ----------
    config : EnvironmentConfig
        The config is extracted from the environment variables.
    logger : logging.Logger
        A logger to be used.
    """

    def __init__(self, config: EnvironmentConfig, logger: Logger) -> None:
        session = boto3.Session(
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key
        )
        endpoint = config.s3_endpoint_url

        if endpoint:
            logger.debug(f'S3 endpoint is "{endpoint}".')
            use_ssl = True

            if endpoint.startswith('http:'):
                use_ssl = False

            s3client = session.client(
                's3',
                endpoint_url=endpoint,
                use_ssl=use_ssl
            )
        else:
            s3client = session.client('s3')

        self.transport_params = {
            'client': s3client
        }
        self._logger = logger

        if config.s3_prefix_pattern is None:
            raise KeyError(
                'Require S3_PREFIX_PATTERN to be set in the environment.')
        else:
            self.object_prefix = self.path_prefix(config.s3_prefix_pattern)

        self._rcpt_pattern = config.smtp_rcpt_regex

    def generate_own_id(self) -> str:
        """
        Generate a UUID for the message.

        Only used of the message itself doesn't have an ID.
        """
        return str(uuid.uuid4())

    async def handle_DATA(self, server: SMTP, session: Session,
                          envelope: Envelope) -> str:
        """
        Implement a hook that will be called after a message has been received.

        Parameters
        ----------
        server : SMTP
            The SMTP server instance.
        session : Session
            The session instance currently being handled.
        envelope : Envelope
            The envelope instance of the current SMTP transaction.

        Returns
        -------
        str
            A status string indicating the outcome.
        """
        try:
            msg = message_from_bytes(envelope.content)
            msg_id = msg.get('Message-ID')

            if not msg_id:
                msg_id = self.generate_own_id()

            path = f'{self.object_prefix}{msg_id}.json.gz'
            payload = {
                'mail_from': envelope.mail_from,
                'mail_options': envelope.mail_options,
                'content': envelope.original_content.decode(),
                'rcpt_options': envelope.rcpt_options,
                'rcpt_tos': envelope.rcpt_tos,
                'smtp_utf8': envelope.smtp_utf8
            }
            payload = json.dumps(payload)

            with smart_open.open(path,
                                 'wb',
                                 transport_params=self.transport_params
                                 ) as stream:
                stream.write(payload.encode())

            self._logger.debug(payload)
        except Exception as ex:
            response = '451 4.3.0 Temporary failure storing message.'
            self._logger.error(f'{response} {ex} "{path}".')
            return response

        return '250 OK'

    async def handle_MAIL(self, server: SMTP, session: Session,
                          envelope: Envelope, address: str,
                          mail_options: list[str]) -> str:
        """
        Handle MAIL_FROM events.

        If implemented, this hook MUST also set the envelope.mail_from
        attribute and it MAY extend envelope.mail_options

        Parameters
        ----------
        server : SMTP
            The SMTP server instance.
        session : Session
            The session instance currently being handled.
        envelop : Envelope
            The envelope instance of the current SMTP transaction.
        address : str
            The parsed email address given by the client in the MAIL FROM
            command.
        mail_options : list[str]
            Additional ESMTP MAIL options provided by the client.

        Returns
        -------
        str
            Response message to be sent to the client.
        """
        envelope.mail_from = address
        return '250 OK'

    async def handle_RCPT(self, server: SMTP, session: Session,
                          envelope: Envelope, address: str,
                          rcpt_options: list[str]) -> str:
        """
        Handle RCPT TO events.

        If implemented, this hook SHOULD append the address to
        envelope.rcpt_tos and it MAY extend envelope.rcpt_options (both of
        which are always Python lists).

        Parameters
        ----------
        server : SMTP
            The SMTP server instance.
        session : Session
            The session instance currently being handled.
        envelope : Envelope
            The envelope instance of the current SMTP transaction.
        address : str
            The parsed email address given by the client in the RCPT TO command.
        rcpt_options : list[str]
            Additional ESMTP RCPT options provided by the client.

        Returns
        -------
        str
            Response message to be sent to the client.
        """
        envelope.rcpt_tos.append(address)

        if not self._rcpt_pattern.match(address):
            response = '550 5.1.1 No such user'
            self._logger.error(f'{response} <{address}>.')
            return response

        return '250 OK'

    def path_prefix(
            self, prefix_pattern: str,
            timestamp: datetime.datetime = datetime.datetime.now(utc)) -> str:
        """
        Construct a path from the pattern based upon the timestamp.

        Parameters
        ----------
        prefix_pattern : str
            The pattern of the path with variables substituted based on the
            timestamp.  Substitutions will be:
                - {YYYY} for the year.
                - {MM} for the month (zero padded).
                - {dd} for the day (zero padded).
                - {HH} for the hour (zero padded).
                - {mm} for the minute (zero padded).

        timestamp : datetime.datetime, optional
            The timestamp to use when constructing the path, by default
            datetime.datetime.now().

        Returns
        -------
        str
            The path for the data to be written to.

        Raises
        ------
        ValueError
            If the provided pattern would not produce a valid path
            name.
        """
        prefix = prefix_pattern.removesuffix('/')

        YYYY = str(timestamp.year)
        prefix = prefix.replace('{YYYY}', YYYY)

        MM = f'{timestamp.month:02}'
        prefix = prefix.replace('{MM}', MM)

        dd = f'{timestamp.day:02}'
        prefix = prefix.replace('{dd}', dd)

        HH = f'{timestamp.hour:02}'
        prefix = prefix.replace('{HH}', HH)

        mm = f'{timestamp.minute:02}'
        prefix = prefix.replace('{mm}', mm)

        prefix += '/'
        parse_result = urlparse(prefix)

        try:
            assert parse_result.scheme == 's3', 'URL scheme must be "s3".'
            bucket_name = parse_result.netloc
            assert len(bucket_name), 'Bucket name not specified.'
        except AssertionError as ex:
            raise ValueError(ex)

        return prefix
