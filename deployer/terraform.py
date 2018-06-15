# -*- coding: utf-8 -*-
#
# Copyright Veracode Inc., 2014

import logging
import os

logger = logging.getLogger(os.path.basename('deployer'))


def apply(config):
    """
    Generate command for 'terraform apply'.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

    Returns:
        tf_command: list of command-line arguments to run terraform with.
    """
    tf_command = ['terraform', 'apply']
    tf_command += default_cmdline_options(config)

    return tf_command


def destroy(config):
    """
    Generate command for 'terraform destroy'.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

    Returns:
        tf_command: list of command-line arguments to run terraform with.
    """
    tf_command = ['terraform', 'destroy', '-force']
    tf_command += default_cmdline_options(config)

    return tf_command


def get():
    """Generate command for 'terraform get'.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

    Returns:
        tf_command: list of command-line arguments to run terraform with.
    """
    return ['terraform', 'get']


def plan(config, action):
    """Generate command for 'terraform plan'.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with
        action: one of: 'create', 'destroy', or 'plan'

    Returns:
        tf_command: list of command-line arguments to run terraform with.
    """
    tf_command = ['terraform', 'plan']
    if action == 'destroy':
            tf_command = ['terraform', 'plan', '-destroy']

    tf_command += default_cmdline_options(config)
    return tf_command


def remote_state(config):
    """
    Generate command for 'terraform remote config ...'.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

    Returns:
        tf_command: list of command-line arguments to run terraform with.
    """

    remote_cmd = ['terraform',
                  'init',
                  '-backend=true',
                  '-backend-config=bucket={}'.format(config['tf_state_bucket']),
                  '-backend-config=key={}'.format(config['tf_state']),
                  '-backend-config=region={}'.format(config['aws_region']),
                  '-backend-config=profile={}'.format(config['aws_profile'])]

    return remote_cmd


def remote_pull():
    """
    Generate command for 'terraform remote pull'.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

    Returns:
        tf_command: list of command-line arguments to run terraform with.
    """
    return ['terraform', 'state', 'pull']


def remote_push():
    """
    Generate command for 'terraform remote push'.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

    Returns:
        tf_command: list of command-line arguments to run terraform with.
    """
    return ['terraform', 'state', 'push', '.terraform/terraform.tfstate']


def validate(config):
    """
    Generate command for 'terraform validate'.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

    Returns:
        tf_command: list of command-line arguments to run terraform with.
    """
    tf_command = ['terraform', 'validate']
    tf_command += default_cmdline_options(config)

    return tf_command


def default_cmdline_options(config):
    """
    Return default command line options required for every run of terraform.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

    Returns:
        cmdline_options: list of command-line arguments to run
                         all terraform commands should be run with.
    """

    cmdline_options = ['-var=\'aws_region={}\''.format(config['aws_region']),
                       '-var-file={}'.format(config['tfvars']) ]

    return cmdline_options


def output(tf_var):
    """
    Generate command for 'terraform output <tfvar>'.

    Args:
        tf_var: name of terraform output variable to return the output of.

    Returns:
        tf_command: list of command-line arguments to run terraform with.
    """
    tf_command = ['terraform', 'output', tf_var]

    return tf_command

