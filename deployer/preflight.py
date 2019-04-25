# -*- coding: utf-8 -*-
#
# Copyright Veracode Inc., 2014
import boto3
import json
import logging
import os
import uuid
import workdir

from   deployer import s3
import deployer.route53 as r53
from   deployer import utils
from   deployer.exceptions import MissingConfigurationParameterException

logger = logging.getLogger(os.path.basename('deployer'))


def pre_setup(config, sync = True):

    config['public_zone_id'] = config.get('public_zone_id', "<computed>")
    #create tmp dir to stage a deployment from
    config['tmpdir'] = config.get('tmpdir',
                                  os.path.join('/tmp', str(uuid.uuid4())))

    logger.debug("{}: Creating tmpdir: {}".format(__name__, config['tmpdir']))
    workdir.options.path = config['tmpdir']
    workdir.create()

    config['tfvars'] = os.path.join(workdir.options.path,
                                    config.get('tfvars_file', 'vars.tf'))

    config['tf_root'] = config.get('tf_root',
                                   utils.get_tf_location(config))

    # If the tf location is set to a local directory, we need to deal
    # with things like the possibility of the actual tf location being
    # in a subdir and a specified branch.
    if not utils.git_url(config['terraform']):
        (repo, branch, subdir) = utils.parse_git_url(config['terraform'])
        config['tf_root'] = repo
        if branch:
            msg = "Setting branch to: {}".format(branch)
            logger.debug(msg)
            if sync:
                git_pull_cmd = utils.git_pull(repo)
                utils.run_command(git_pull_cmd, repo)
                git_set_branch_cmd = utils.git_set_branch(branch)
                utils.run_command(git_set_branch_cmd, repo)

        if subdir:
            tf_root = os.path.join(config.get('tf_root', repo), subdir)
            msg = "Setting tf_root to: {}".format(tf_root)
            logger.debug(msg)
            config['tf_root'] = tf_root

    return config


def setup(config, sync = True):
    """
    Get ready to run 'terraform apply' for this environment.
    Modifies the dictionary passed in, then returns it.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

        sync: boolean. Toggles setting the branch on/off. Defaults to on.

    Returns:
        config with updated values.

    Raises:
        MissingConfigurationParameterException for missing config file entries.
    """
    # Create the per-environment S3 folder in pre-flight
    logmsg = "{}: Creating per-environment folder : {}:{}"
    logger.debug(logmsg.format(__name__,
                               config['project_config'],
                               config['env_folder']))
    s3.create_folder(config['project_config'],config['env_folder'])

    if not config.get('route53_tld', None):
        msg = "route53_tld variable is not set in config file."
        raise MissingConfigurationParameterException(msg)

    zone_id = r53.get_zone_id(config['route53_tld'])
    if not zone_id:
        msg = "zone_id not set."
        raise MissingConfigurationParameterException(msg)

    config['public_zone_id'] = config.get('public_zone_id', zone_id)

    return config


def teardown(config):
    """
    Teardown the build directory structure created to deploy the environment.
    Modifies the dictionary passed in, then returns it.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with
    Returns:
        config

    Raises:
        MissingConfigurationParameterException if 'tmpdir' is unset.
    """
    logger.debug("Removing tmpdir: {}".format(config['tmpdir']))
    workdir.options.path = config.get('tmpdir')
    if not workdir.options.path:
        msg = "tmpdir variable is not set. Can not destroy tmpdir location"
        raise MissingConfigurationParameterException(msg)

    workdir.remove()

    if not utils.git_url(config['terraform']):
        workdir.options.path = config.get('tf_root')
        workdir.remove()
    
    return config


def write_vars(config, varfile):
    """
    Writes out the modified dict to a location it can be used as a
    terraform vars file.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

        varfile: Path to file to write out to.
    Returns:
        nothing
    """
    # write out the tf_vars file
    logmsg = "{}: Writing out tf vars file: {}"
    logger.debug(logmsg.format(__name__, varfile))
    with open(varfile, 'w') as fp:
        json.dump(config, fp, indent=2)

    logmsg = "{}: Finished writing tf vars file: {}"
    logger.debug(logmsg.format(__name__, varfile))

    return


def download_staged_artifacts(config):
    """
    Downloads staged artifacts from S3 so terraform can use them access
    them for placing in environment-specific staging location.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with
    Returns:
        nothing

    Raises:
        MissingConfigurationParameterException if 'project_config' is undefined.
    """
    s3 = boto3.resource('s3')
    bucket_name = config.get('project_config', None)
    if not bucket_name:
        msg = "project_config bucket is not defined. Can not proceed."
        raise MissingConfigurationParameterException(msg)

    if not config.get('staged_artifacts', None):
        logger.warn("'staged_artifacts' not defined. Nothing to download from S3. ")
        return

    logmsg = "Downloading project files from s3 bucket {}"
    logger.debug(logmsg.format(bucket_name))
    for bucket_key in config['staged_artifacts'].keys():
        s3_file = os.path.basename(bucket_key)
        bucket_file = s3.Object(bucket_name, bucket_key)
        try:
            local_file = os.path.join(config['tmpdir'],s3_file)
            workdir.options.path = os.path.dirname(local_file)
            workdir.create()

            bucket_file.download_file(local_file)
            log_msg = "Downloading {}/{} to {}"
            logger.debug(log_msg.format(config['project_config'],
                                        bucket_key,
                                        local_file))
        except:
            log_msg = "Error downloading {}/{} to {}"
            logger.debug(log_msg.format(config['project_config'],
                                        bucket_key,
                                        local_file))

    return


def sync_terraform(config):
    """
    Clone all terraform git repositories to the workdir.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with
    Returns:
        nothing
    """

    # if we've already run terraform here, we don't need to check it out again.
    if config.get('tf_root') and os.path.isdir(os.path.join(config['tf_root'],
                                                            '.terraform'
                                                            )):
        log_msg = "Terraform code already checked out to this location: {}"
        logger.debug(log_msg.format(config['tf_root']))

        return
    
    workdir.options.path = config['tmpdir']
    workdir.create()
    (repo, branch, subdir) = utils.parse_git_url(config['terraform'])
    clone_cmd = utils.git_clone(repo,branch)
    utils.run_command(clone_cmd, config['tmpdir'])

    return
