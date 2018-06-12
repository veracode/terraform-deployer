import logging
import os

logger = logging.getLogger(os.path.basename('deployer'))


class DeploymentException(Exception):
    """
    Error with environment name.

    """
    pass


class EnvironmentNameException(Exception):
    """
    Error with environment name.

    """
    pass


class MissingConfigurationParameterException(Exception):
    """
    Missing required configuration parameter.
    """


class ShellCommandException(Exception):
    """
    Error running a shell command.
    """
    pass


class ConfigFileException(Exception):
    """
    Error running a shell command.
    """
    pass


class EnvironmentExistsException(Exception):
    """
    Self-explanatory
    """
    pass


class InvalidCommandException(Exception):
    """
    An invalid command was issued to the deployer.
    """
    pass
