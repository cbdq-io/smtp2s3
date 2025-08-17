"""Verify the container."""
import testinfra_bdd
import yaml
from pytest_bdd import given, scenario, then, when

import smtp2s3


@scenario('../features/container.feature', 'Verify the Chart appVersion')
def test_verify_the_chart_appversion():
    """Verify the Chart appVersion."""


@scenario('../features/container.feature', 'Verify the container')
def test_default_values():
    """Default Values."""


@given('the smtp2s3 version', target_fixture='module_version')
def _():
    """the smtp2s3 version."""
    return smtp2s3.__version__


@when('compared to the chart appVersion', target_fixture='app_version')
def _():
    """compared to the chart appVersion."""
    with open('charts/smtp2s3/Chart.yaml', 'r') as stream:
        data = yaml.safe_load(stream)

    return data['appVersion']


@when('the chart version', target_fixture='chart_version')
def _():
    """the chart version."""
    with open('charts/smtp2s3/Chart.yaml', 'r') as stream:
        data = yaml.safe_load(stream)

    return data['version']


@then('the versions match')
def _(app_version: str, chart_version: str, module_version: str):
    """the versions match."""
    msg = f'Expecting Helm chart app_version to be {module_version} '
    msg += f'but it is {app_version}.'
    assert app_version == module_version, msg
    msg = f'Expecting Helm chart version to be {module_version} '
    msg += f'but it is {chart_version}.'
    assert chart_version == module_version, msg


# Ensure that the PyTest fixtures provided in testinfra-bdd are available to
# your test suite.
pytest_plugins = testinfra_bdd.PYTEST_MODULES
