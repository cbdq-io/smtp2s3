"""Verify the container."""
import testinfra_bdd
from pytest_bdd import scenario


@scenario('../features/container.feature', 'Verify the container')
def test_default_values():
    """Default Values."""


# Ensure that the PyTest fixtures provided in testinfra-bdd are available to
# your test suite.
pytest_plugins = testinfra_bdd.PYTEST_MODULES
