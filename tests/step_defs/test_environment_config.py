"""Environment Config feature tests."""
import os

from pytest_bdd import given, parsers, scenario, then, when

from smtp2s3 import EnvironmentConfig


@scenario('../features/environment_config.feature', 'Default Values')
def test_default_values():
    """Default Values."""


@scenario('../features/environment_config.feature', 'Invalid Values')
def test_invalid_values():
    """Invalid Values."""


@given('the Environment Config', target_fixture='environment_config')
def _():
    """the Environment Config."""
    return {}


@when('default Environment Config values are used')
def _():
    """default Environment Config values are used."""
    pass


@when(parsers.parse('the Environment Variable {variable} is set to {value}'))
def _(variable: str, value: str, environment_config: dict):
    """the Environment Variable <variable> is set to <value>."""
    environment_config[variable] = value


@when(parsers.parse('the {key} environment variable is set to {value}'))
def _(key: str, value: str):
    """the S3_PREFIX_PATTERN environment variable is set to 's3://mybucket'."""
    os.environ[key] = value


@then(
        parsers.parse(
            'Environment Config attribute {attribute} is {expected_value}'
        )
)
def _(attribute: str, expected_value: str,
      environment_config: dict):
    """Environment Config attribute <attribute> is <value>."""
    environment_config = EnvironmentConfig(environment_config)
    actual_value = str(getattr(environment_config, attribute))
    assert actual_value == expected_value


@then('a Value Error Exception is Raised')
def _(environment_config: dict):
    """a Value Error Exception is Raised."""
    exception_raised = False

    try:
        environment_config = EnvironmentConfig(environment_config)
    except ValueError:
        exception_raised = True

    assert exception_raised
