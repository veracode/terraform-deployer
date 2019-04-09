# -*- coding: utf-8 -*-
#
# Copyright Veracode Inc., 2014

from jinja2 import Environment
import json
from   jsonschema import validate
from   jsonschema.exceptions import ValidationError
import logging
import os
from   subprocess import (STDOUT,
                          Popen )
import sys

from   deployer.exceptions import EnvironmentNameException

logger = logging.getLogger('deployer')


def load_vars(varfile):
    """
    Load a specified variables file.

    Args:
        varfile: string (file path) location of the deployer config file.

    Returns:
        data: dict. This becomes the 'config' dict that gets passed around.
    """
    with open(varfile) as data_file:
        data = json.load(data_file)
    return data


def eval_config(config):
    """
    Use the passed config dict as a template and return the fully
    evaluated config back to the caller.

    Args:
        config: dict containing a deployer configuration

    Returns:
        data: dict. This becomes the 'config' dict that gets passed around/
    """
    # Convert the dict back to a string, eval the tempplate, then
    # convert it back to a dict.
    config_str = json.dumps(config)
    env = Environment()
    template = env.from_string(config_str)
    data = json.loads(template.render(config = config))
    data2 = json.loads(template.render(config = data))
    
    return data2


def load_schema(schema):
    """
    Load a specified variables file.

    Args:
        schema: string (file path) location of a schema file to use
                in validations.

    Returns:
        dict via a call to load_vars()
    """
    f = os.path.join(os.path.dirname(__file__), schema)
    return load_vars(f)


def validate_env_name(env_name):
    """
    Ensure environment name follows various rules and conventions,
    both local, and imposed by AWS.

    Args:
        env_name: string representing an environment name

    Returns:
        True on success

    Raises:
      EnvironmentNameException on failure.
    """

    if len(env_name) <= 0:
        msg = "Incorrect number of tokens. "
        msg += "Environment name can not be undefined"
        raise EnvironmentNameException(msg)

    if len(env_name) > 20:
        msg = "Environment Name too long: {} characters. Limit: 20."
        raise EnvironmentNameException(msg.format(len(env_name)))

    # environment name must be at least 1 token
    # Single token environment names are typically shared/master environments
    # Double token environment names are typically ephemeral environments
    parsed_name = []
    parsed_name = env_name.split('-')
    if len(parsed_name) > 2:
        msg = "Incorrect number of tokens. "
        msg += "Should be 1 or 2 tokens, not {}".format(len(parsed_name))
        raise EnvironmentNameException(msg)

    if (len(parsed_name) == 2):
        if parsed_name[1].isalpha():
            if (len(parsed_name[1]) != 1):
                msg = "Environment version is limited to a single character: {}"
                raise EnvironmentNameException(msg.format(parsed_name[-1]))
        else:
            msg = "Environment version is limited to a single character: {}"
            raise EnvironmentNameException(msg.format(parsed_name[-1]))

    return True


def validate_schema(config, schema_file):
    """
    Validate the config based on a defined schema.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

        schema_file: string (file path) location of a schema file to use
                     to validate the config dict.

    Returns:
         nothing on success

    Raises:
         ValidationError on failure.
    """
    try:
        schema = load_schema(schema_file)
        validate(config, schema)
    except ValidationError:
        raise


def run_command(command, cwd=None):
    """
    Runs a command "on the command line" and returns stdout/stderr in
    real time.

    Args:
        command: list of command line arguments to run.
        cwd    : string (path) representing the location of where to run the
                 command from.
    Returns:
        out: out put of the command run.
    """
    logger.debug("{}: Running command: '{}' in {}".format(__name__,
                                                          " ".join(command),
                                                          cwd ))
    cmd = Popen(command, shell=False, bufsize=0, stderr=STDOUT, cwd=cwd)
    (out, err) = cmd.communicate()
    if err:
        sys.exit(err)
        print(out)
        
    if cmd.returncode != 0:
        logger.error("{} failed with code {}.".format(command, cmd.returncode))
                                 
    return cmd.returncode


def git_clone(repo, branch=None):
    """
    Return the git command to clone a specified repository.

    Args:
        repo: string representing a git repo.
        branch: string representing a branch name.

    Returns:
        cmd: list containing the command line arguments to clone a git repo.
    """
    cmd = ['git', 'clone', '--recursive']
    if branch:
        cmd += ['-b', branch]
    cmd.append(repo)

    return cmd


def git_pull(repo):
    """
    Return the git command to update an existing repo

    Args:
        repo: string representing a git repo.

    Returns:
        cmd: list containing the command line arguments to clone a git repo.
    """
    cmd = ['git', 'pull']

    return cmd


def git_set_branch(branch):
    """
    Change to a given branch in a local copy of the checked out repository

    Args:
        branch: string representing the branch to change to.

    Returns:
        cmd: list containing the command line arguments to set a git repo to
    """

    return ['git', 'checkout', branch]


def parse_git_url(url):
    """
    Parse the provided git URL into components to operate on independently.

    Args:
        url: string representing a gitlab url for a git repo.

    Returns:
        repo, branch: tuple of strings representing a git repo and a
                      branch name.
    """
    repo = None
    branch = None
    subdir = None
    if 'http' in url:
        (repo, branch, subdir) = parse_http_git_url(url)
    elif "?" in url:
        (repo,branch) = url.split('?')
        branch = branch.split('=')[1]
        if '//' in branch:
            (branch,subdir) = branch.split('//')
    elif '//' in url:
        (repo, subdir) = url.split('//')
    else:
        repo = url
    return (repo, branch, subdir)


def parse_http_git_url(url):
    repo = None
    branch = None
    subdir = None

    if "?" in url:
        (repo,branch) = url.split('?')
        branch = branch.split('=')[1]
        if '//' in branch:
            (branch,subdir) = branch.split('//')
    elif len(url.split('//')) > 2:
        subdir = url.split('//')[-1]
        repo = '//'.join(url.split('//')[0:2])
    else:
        repo = url

    return (repo, branch, subdir)


def git_url(url):
    return url.endswith('.git') or '.git' in url


def local_dir_from_git_repo(url):
    """
    Determine the name of the directory we checked out based on the URL.

    Args:
        url: string representng the git url for the terraform code repo.
    Returns:
        project: string represeting just the project name, stripped of '.git'.
    """
    repo = url
    branch = None
    subdir = None
    if '?' in url or '//' in url:
        (repo,branch,subdir) = parse_git_url(url)
      
    repo_name = repo.split('/')[-1]
    project = repo_name.replace('.git','')
    if subdir:
        project = os.path.join(project, subdir)
        
    return project


def get_tf_location(config):
    """
    Return the location of where terraform lives locally by parsing
    the config['terraform'] value.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

    Returns:
        Local path indicating where the terraform infrastructure code
        lives on the "local disk"
    """

    if config.get('terraform'):
        # If tf code is in a git repo, check it out under config['tmp_dir']
        if git_url(config['terraform']):
            project = local_dir_from_git_repo(config['terraform'])
            tf_root = config.get('tf_root',
                                 os.path.join(config['tmpdir'], project))

        # If we've provided a specific location, just use that location.
        if not git_url(config['terraform']):
            tf_root = config['terraform']

        return tf_root


def parseConfigOpts(configVars):
    newConfigVars = {}
    for item in configVars:
        try:
            value = json.loads(item)
            newConfigVars = { **newConfigVars, **value }
        except ValueError as e:
            k,v = item.split('=')
            newConfigVars[k] = v

    return newConfigVars

