import logging
import os
import pytest
from deployer.exceptions import ( ConfigFileException,
                                  DeploymentException,
                                  EnvironmentNameException,
                                  InvalidCommandException,
                                  MissingConfigurationParameterException,
                                  ShellCommandException)

logger = logging.getLogger(os.path.basename('deployer'))


def test_DeploymentException():
    with pytest.raises(Exception):
        raise DeploymentException("Foo!")


def test_EnvironmentNameException():
    with pytest.raises(Exception):
        raise EnvironmentNameException("Bar!")


def test_ShellCommandException():
    with pytest.raises(Exception):
        raise ShellCommandException("Bif!")


def test_ConfigFileExceptionException():
    with pytest.raises(Exception):
        raise ConfigFileException("Bam!")


def test_MissingConfigurationParameterException():
    with pytest.raises(Exception):
        raise MissingConfigurationParameterException("Bam!")


def test_InvalidCommandException():
    with pytest.raises(Exception):
        raise InvalidCommandException("Bam!")

