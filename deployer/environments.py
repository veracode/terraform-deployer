# -*- coding: utf-8 -*-
#
# Copyright Veracode Inc., 2014
import json
import logging
import os
from termcolor import colored

from   deployer import aws
from   deployer import s3
from   deployer import utils
import deployer.terraform as tf
from   deployer.exceptions import ( EnvironmentExistsException,
                                    InvalidCommandException)

logger = logging.getLogger(os.path.basename('deployer'))


def _precheck(config, action):
    """
    Run through preflight checklist before running terraform apply/destroy.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

        action: string (create | destroy)

    Returns:
        Nothing

    Raises:
        InvalidCommandException exception on unknown command.
    """
    # Instantiate remote state only if:
    # - the terraform code isn't already checked out
    # - and we haven't already run 'terraform remote config...'
    if not os.path.isfile(os.path.join(config['tf_root'],
                                       '.terraform',
                                       'terraform.tfstate')):
        log_msg = "Configuring terraform remote state in: {}"
        logger.debug(log_msg.format(config['tf_root']))
        tf_command = tf.remote_state(config)
        return_code = utils.run_command(tf_command, cwd=config['tf_root'])
        if return_code != 0:
            raise BaseException("{} failed with code {}.".format(tf_command,
                                                                 return_code))

    # Grab all the tf modules required
    tf_command = tf.get()
    utils.run_command(tf_command, cwd=config['tf_root'])

    # validate env_name
    utils.validate_env_name(config['env_name'])
    tf_command = tf.validate(config)
    utils.run_command(tf_command, cwd=config['tf_root'])

    # Push remote state
    push_or_pull = {
        'create' : tf.remote_push,
        'plan'   : tf.remote_pull,
        'destroy' : tf.remote_pull,
    }
    try:
        tf_command = push_or_pull[action]()
    except KeyError:
        raise InvalidCommandException("Invalid Command: {}".format(action))

    utils.run_command(tf_command, cwd=config['tf_root'])

    # Run Plan
    tf_command = tf.plan(config, action)
    utils.run_command(tf_command, cwd=config['tf_root'])

    return


def plan(config):
    """
    Run 'terraform plan'.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

    Returns:
        True
    """
    (repo, branch, subdir) = utils.parse_git_url(config['terraform'])
    _precheck(config, 'plan')
    return True


def query(config):
    """
    Query AWS to see if an env already exists. If so, provide a list of ARNS.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

    Returns:
        True or False
    """
    # Check if env already exists
    env_name = config['environment'].get('name')
    env_vers = config['environment'].get('version', None)
    env = env_name

    if env_vers:
        env = "-".join([env_name, env_vers])

    product = config['tags'].get('product', None)
    resources = aws.environment_exists(env_name, env_vers, product)

    if product:
        env = "-".join([product, env])

    if resources > 0:
        msg  = "{} exists."
        msg += "\n\n{}"
        resources_json = json.dumps(resources,indent=4)
        message = colored(msg.format(env,resources_json), 'red')
        print message

    return


def create(config):
    """
    Create the environment by running 'terraform apply'.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

    Returns:
        True

    Raises:
        EnvironmentExistsException if environment already exists.
    """
    # Check if env already exists
    env_name = config['environment'].get('name')
    env_vers = config['environment'].get('version', None)
    env = env_name

    if env_vers:
        env = "-".join([env_name, env_vers])

    product = config['tags'].get('product', None)
    resources = aws.environment_exists(env_name, env_vers, product)
    if resources > 0:
        if product:
            env = "-".join([product, env])

        from termcolor import colored

        msg  = "\n\nAn environment with the name {} already exists."
        msg += "\nPlease tear it down before trying to rebuild."
        msg += "\n\n{}"
        resources_json = json.dumps(resources,indent=4)
        message = colored(msg.format(env,resources_json), 'red')
        raise EnvironmentExistsException(message)

    _precheck(config, 'create')

    # Run Apply
    tf_command = tf.apply(config)
    logger.debug("Command: {}".format(" ".join(tf_command)))
    logger.debug("In: {}".format(config['tf_root']))

    try:
        return_code = utils.run_command(tf_command, cwd=config['tf_root'])
    except:
        aws.tag_resources(config)
        return False

    aws.tag_resources(config)
    return True


def destroy(config):
    """
    Destroy the environment by running 'terraform destroy'.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

    Returns:
        True

    Raises:
        EnvironmentExistsException if environment does not exist.
    """

    # Check if env already exists
    env_name = config['environment'].get('name')
    env_vers = config['environment'].get('version', None)
    env = env_name

    if env_vers:
        env = "-".join([env_name, env_vers])

    product = config['tags'].get('product', None)
    if not aws.environment_exists(env_name, env_vers, product):
        msg = "No such environment with the name {} exists."
        if product:
            env = "-".join([product, env])
        raise EnvironmentExistsException(msg.format(env))

    tf_root = _precheck(config, 'destroy')

    # Tag the resources as ready to destroy
    aws.tag_resources(config)

    # Run destroy
    tf_command = tf.destroy(config)
    return_code = utils.run_command(tf_command, cwd=config['tf_root'])

    # Double check the make sure we don't have anything left running
    # before destroying the S3 resources.
    if not aws.environment_exists(env_name, env_vers, product) and return_code == 0:
        # Destroy the per-environment S3 folder in
        msg = "Destroying S3 env folder: {}".format(config['env_folder'])
        logger.debug(msg)
        s3.destroy_folder(config['project_config'],config['env_folder'])

        # Destroy the state file in S3
        msg = "Destroying S3 State file: {}".format(config['tf_state'])
        logger.debug(msg)
        s3.delete_object(config['tf_state_bucket'], config['tf_state'])

    return True


def output(config, tf_var):
    """
    Output the value of the specified variable.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

        tf_var: name of terraform output variable to return the output of.

    Returns:
        True

    """
    tf_command = tf.output(tf_var)
    utils.run_command(tf_command, cwd=config['tf_root'])

    return True


def list_deployed_environment_versions(env):
    """
    Return a list of environemnt versions currently in use.

    Args:
        env: string name of a particular environement to check for
             existing VPCs. e.g. coral, malachite, lapis

    Returns:
        list of version letters in use.

    """
    vpcs = aws.list_vpcs(env)
    versions = [ version.split('-')[1] for version in aws.list_vpcs(env) ]
    versions.sort()
    return versions


def get_next_version(env, ephemeral_env=None):
    """
    Return the next available version letter not currently in use.
    Will skip over letters in use. Will loop back to 'a' if it reaches
    'z'

    Args:
        env: string name of a particular environement to check for
             existing VPCs. e.g. coral, malachite, lapis

    Returns:
        character representing next available, unused environment version.

    """
    next_env = 'a'
    while aws.environment_exists(env, next_env, ephemeral_env):
        # increment to next version.
        # If we're already at 'z', loop back to 'a'
        if ord(next_env.lower()) == 122:
            next_env = 'a'
        else:
            # otherwise increment
            next_env = chr(ord(next_env.lower()) + 1)
    return next_env
