"""A handler for use with aiosmtpd."""
import asyncio
import datetime
import hashlib
import ipaddress
import json
import socket
import uuid
from email import message_from_bytes
from email.message import Message
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
        self._dnsbl_zones = list(filter(None, config.dnsbl_zones))
        logger.debug(f'DNSBL zones are {self._dnsbl_zones}.')

    def get_message_id(self, msg: Message) -> str:
        """
        Get a usage message ID for a message..

        Only used of the message itself doesn't have an ID.
        """
        msg_id = msg.get('Message-ID')

        if not msg_id:
            return str(uuid.uuid4())

        h = hashlib.sha256(msg_id.encode(errors='ignore')).hexdigest()[:10]
        return f'{uuid.uuid4().hex}-{h}'

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
        eml_path = json_path = '<unset>'

        try:
            msg = message_from_bytes(envelope.content)
            msg_id_header = msg.get('Message-ID')
            msg_id = self.get_message_id(msg)
            eml_path = f'{self.object_prefix}{msg_id}.eml.gz'
            metadata = {
                'mail_from': envelope.mail_from,
                'mail_options': envelope.mail_options,
                'message_id': msg_id_header,
                'path': eml_path,
                'rcpt_options': envelope.rcpt_options,
                'rcpt_tos': envelope.rcpt_tos,
                'session_ip': session.peer[0],
                'smtp_utf8': envelope.smtp_utf8
            }
            content = envelope.content or b''

            with smart_open.open(eml_path,
                                 'wb',
                                 transport_params=self.transport_params
                                 ) as stream:
                stream.write(content)

            json_path = f'{self.object_prefix}{msg_id}.json'

            with smart_open.open(json_path, 'w',
                                 transport_params=self.transport_params
                                 ) as stream:
                json.dump(metadata, stream, separators=(',', ':'))

            self._logger.debug(metadata)
        except Exception as ex:
            response = '451 4.3.0 Temporary failure storing message.'
            self._logger.error(f'{response} {ex} "{eml_path}/{json_path}".')
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
        peer_ip = session.peer[0]
        self._logger.debug(f'Peer IP address is {peer_ip}')

        if len(self._dnsbl_zones):
            if await self.is_ip_on_dns_blocked_list(peer_ip):
                response = '554 5.7.1 Service unavailable; '
                response += 'Client host blocked by policy'
                self._logger.error(f'{response} "{peer_ip}".')
                return response

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
        if not self._rcpt_pattern.fullmatch(address):
            response = '550 5.1.1 No such user'
            self._logger.error(f'{response} <{address}>.')
            return response

        envelope.rcpt_tos.append(address)
        return '250 OK'

    async def is_ip_on_dns_blocked_list(self, ipaddr: str) -> bool:
        """
        Check if the peer IP address is on a blocked list.

        Parameters
        ----------
        ipaddr : str
            The IP address to be checked.

        Returns
        -------
        bool
            True if the IP is on a blocked list.
        """
        try:
            ip = ipaddress.ip_address(ipaddr)
        except ValueError:
            return False

        if ip.version != 4:
            return False
        else:
            parts = reversed(ipaddr.split('.'))
            rip = '.'.join(parts)

        for zone in self._dnsbl_zones:
            qname = f'{rip}.{zone}'

            try:
                await asyncio.to_thread(socket.gethostbyname(qname))
                return True
            except socket.gaierror:
                continue

        return False

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
