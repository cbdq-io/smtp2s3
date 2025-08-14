"""SMTPD Handler feature tests."""
import datetime
import os
from smtplib import SMTP as Client
from smtplib import SMTPRecipientsRefused, SMTPSenderRefused

import boto3
from pytest_bdd import given, parsers, scenario, then, when

from smtp2s3 import get_logger
from smtp2s3.handler import EnvironmentConfig, Handler

logger = get_logger('Testing')
logger.setLevel('DEBUG')


@scenario('../features/handler.feature', 'Email Handler')
def test_email_handler():
    """Email Handler."""
    os.environ['S3_PREFIX_PATTERN'] = 's3://mybucket'
    os.environ['S3_ENDPOINT_URL'] = 'http://minio:9000'


@scenario('../features/handler.feature', 'Invalid Path Prefix')
def test_invalid_path_prefix():
    """Invalid Path Prefix."""
    os.environ['S3_PREFIX_PATTERN'] = 's3://mybucket'


@scenario('../features/handler.feature', 'Valid Path Prefix')
def test_valid_path_prefix():
    """Valid Path Prefix."""
    os.environ['S3_PREFIX_PATTERN'] = 's3://mybucket'


@given('SMTP hostname is localhost', target_fixture='hostname')
def _():
    """SMTP hostname is localhost."""
    return 'localhost'


@given('SMTP port is 8025', target_fixture='client')
def _(hostname):
    """SMTP port is 8025."""
    return Client(host=hostname, port=8025)


@given(parsers.parse('the prefix pattern is {prefix_pattern}'),
       target_fixture='prefix_pattern')
def _(prefix_pattern: str):
    """the prefix pattern is <prefix_pattern>."""
    return prefix_pattern


@when('from address is anne@example.com', target_fixture='from_address')
def _():
    """from address is anne@example.com."""
    return 'anne@example.com'


@when('from name is Anne Person', target_fixture='from_name')
def _():
    """from name is Anne Person."""
    return 'Anne Person'


@when(parsers.parse('the message size is {message_size}'),
      target_fixture='message_size')
def _(message_size: str):
    """the message size is <message_size>."""
    return message_size


@when(parsers.parse('the timestamp is {timestamp}'), target_fixture='timestamp')
def _(timestamp: str):
    """the timestamp is <timestamp>."""
    return datetime.datetime.fromisoformat(timestamp)


@when(parsers.parse('to address is {to_address}'),
      target_fixture='smtp_response')
def _(to_address: str, client: Client, from_name: str, from_address: str,
      message_size: str):
    """to address is <to_address>."""
    content = {
        'tiny': 'Hello, world!',
        'larger': """
        In The Crying of Lot 49, Oedipa Maas, a California housewife, is named
        executor of her ex-boyfriend Pierce Inverarity’s estate and stumbles
        into what may be a centuries-old underground postal system called the
        Trystero. As she investigates, she encounters cryptic symbols,
        strange coincidences, and a tangle of conspiracy theories that blur the
        line between reality and paranoia. The novel leaves readers uncertain
        whether Oedipa has uncovered a genuine hidden network or is succumbing
        to delusion, making it both a satirical detective story and a
        meditation on meaning in a chaotic world.
        """
    }
    client.set_debuglevel(1)
    message = f'Subject: Test Message\r\n\r\n{content[message_size]}'

    try:
        client.sendmail(
            from_addr=f'{from_name} <{from_address}>',
            to_addrs=to_address,
            msg=message.encode()
        )
        response_code = 205
    except SMTPSenderRefused as ex:
        logger.error(f'{ex.smtp_error}')
        response_code = ex.smtp_code
    except SMTPRecipientsRefused as ex:
        logger.error(ex)
        response_code = 550

    return response_code


@then(parsers.parse('message response is {expected_smtp_response:d}'))
def _(expected_smtp_response: int, smtp_response: int):
    """Message response is <smtp_response>."""
    assert expected_smtp_response == smtp_response


@then(parsers.parse('s3 object count is {s3_object_count:d}'))
def _(s3_object_count: int):
    """s3 object count is <s3_object_count>."""
    session = boto3.Session(
        aws_access_key_id='minioadminid',
        aws_secret_access_key='minioadminsec'
    )
    s3 = session.client('s3', endpoint_url='http://localhost:9000',
                        use_ssl=False)
    paginator = s3.get_paginator('list_objects_v2')
    actual_object_count = 0

    for page in paginator.paginate(Bucket='mybucket', Prefix='emails/'):
        actual_object_count += len(page.get('Contents', []))

    assert actual_object_count == s3_object_count


@then('the handler.path_prefix method raised ValueError')
def _(prefix_pattern: str, timestamp: datetime.datetime):
    """the handler.path_prefix method raised ValueError."""
    value_error_exception_raised = False

    try:
        handler = Handler(EnvironmentConfig(), logger)
        handler.path_prefix(prefix_pattern, timestamp)
    except ValueError:
        value_error_exception_raised = True

    assert value_error_exception_raised


@then(parsers.parse('the path prefix is {expected_path_prefix}'))
def _(expected_path_prefix: str, prefix_pattern: str,
      timestamp: datetime.datetime):
    """the path prefix is <path_prefix>."""
    handler = Handler(EnvironmentConfig(), logger)
    actual_path_prefix = handler.path_prefix(prefix_pattern, timestamp)
    assert actual_path_prefix == expected_path_prefix
    handler.generate_own_id()
