# -*- coding: utf-8 -*-
#
# Copyright Veracode Inc., 2014
import boto3
import logging
import os
from botocore.exceptions import ClientError

import deployer.utils as utils
import deployer.s3

logger = logging.getLogger(os.path.basename('deployer'))


def configure(config):
    """
    Configure the environment for both Terraform & boto3 to operate
    via the AWS API.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

    Returns:
        config
    """
    # Clear out AWS_* vars from the environment if they exist
    try:
        os.environ.pop('AWS_DEFAULT_PROFILE')
        os.environ.pop('AWS_SECRET_ACCESS_KEY')
        os.environ.pop('AWS_ACCESS_KEY_ID')
        os.environ.pop('AWS_DEFAULT_REGION')
    except KeyError:
        # They weren't set, so move on
        pass

    # Set the default profile
    os.environ['AWS_DEFAULT_PROFILE'] = config['aws_profile']
    os.environ['AWS_PROFILE'] = config['aws_profile']
    os.environ['AWS_DEFAULT_REGION'] = config['aws_region']

    if os.environ.get('API_TOKEN') and "API_TOKEN" in config.get('terraform'):
        git_url = config['terraform']
        config['terraform'] = git_url.replace("API_TOKEN",
                                              os.environ['API_TOKEN'])
        config['API_TOKEN'] = os.environ['API_TOKEN']

    boto3.setup_default_session(profile_name=config['aws_profile'])
    boto_profile = get_account_name()
    # Verify the profile name we get back from AWS is the same as we just set
    # otherwise exit now.
    try:
        assert(os.environ.get('AWS_DEFAULT_PROFILE') == config['aws_profile'])
        assert(config['aws_profile'] == boto_profile)
        assert(os.environ.get('AWS_DEFAULT_PROFILE') == boto_profile)
    except AssertionError:
        msg = "AWS_DEFAULT_PROFILE mismatch with reality.\n"
        msg += "\t   AWS_DEFAULT_PROFILE:              {}\n"
        msg += "\t   Profile passed in from config:    {}\n"
        msg += "\t   Profile boto3 thinks we're using: {}\n"
        logger.critical(msg.format(os.environ.get('AWS_DEFAULT_PROFILE'),
                                   config['aws_profile'],
                                   boto_profile))
        raise

    config['availability_zones'] = get_current_az_list(config)
    config['account_id'] = config.get('account_id', get_account_id())

    env_name = "{}".format(config['environment'].get('name'))
    if config['environment'].get('version'):
        env_name = "{}-{}".format(config['environment']['name'],
                                  config['environment']['version'])

    # Add env_name and env_version to tags.
    if 'tags' in config:
        if 'name' in config['environment']:
            config['tags']['env_name'] = config['environment'].get('name')
        if 'version' in config['environment']:
            config['tags']['env_version'] = config['environment'].get('version')

    # Figure out where our buckets are.  This should go in pre-flight,
    # but we haven't established our account_id yet, therefore needs
    # to be here, after we set up the aws stuff.
    config['project_config'] = config.get('project_config',
                                          deployer.s3.get_bucket_name(config,
                                                                      'data'))

    config['env_folder'] = config.get('env_folder', env_name)

    tf_state_bucket_name = deployer.s3.get_bucket_name(config, "tfstate")
    config['tf_state_bucket'] = config.get('tf_state_bucket',
                                           tf_state_bucket_name)
    tf_state = "{}.tfstate".format(env_name)
    config['tf_state'] = config.get('tf_state', tf_state)
    config['env_name'] = config.get('env_name', env_name)
    utils.validate_env_name(config['env_name'])
    config['route53_tld'] = config.get('route53_tld')

    return config


def get_account_name():
    """
    Return the account name we're using based on the value set in the
    deployer config file.

    Args:
         None

    Returns:
         String representing the IAM account name.

    """
    return boto3.client('iam').list_account_aliases()['AccountAliases'][0]


def get_account_id():
    """
    Return the account ID we're using based on the value set in the
    deployer config file.

    Args:
        None

    Returns:
        String representing the IAM account number.
    """
    return boto3.client('sts').get_caller_identity().get('Account')


def get_current_region():
    """
    Return the current region we're using.

    Args:
        None

    Returns:
        String representing the current region.
    """
    return boto3.DEFAULT_SESSION.region_name


def get_current_az_list(config):
    """
    Return the list of available availability_zones for this region.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

    Returns:
        List of strings
    """
    avail_zones = config.get('availability_zones', [])
    if not avail_zones:
        ec2c = boto3.client('ec2')
        for zone in ec2c.describe_availability_zones()['AvailabilityZones']:
            if zone['State'] == 'available':
                avail_zones.append(zone['ZoneName'])

    return avail_zones


def environment_exists(env_name, env_vers=None, ephemeral_env=None):
    """
    Checks to see if this desired environment name already exists.

    Args:
        env_name: string - Name of environment to check
        env_vers: string - Version of environment to check
        ephemeral_env - Name of ephemeral environment based on product tag.
    Returns:
        True:  if the environment exists.
        False: if the environment does not exist.
    """
    client = boto3.client('resourcegroupstaggingapi')
    env_name_filter = { 'Key': 'env_name', 'Values': [ env_name ] }
    env_vers_filter = { 'Key': 'env_version', 'Values': [ env_vers ] }
    ephemeral_filter = { 'Key': 'system_type', 'Values': [ ephemeral_env ] }

    # Search for a value of 'running'. Any other value means the
    # environment doesn't really exist
    state_filter  = { 'Key': 'deployer_state', 'Values': ['running'] }

    tag_filters = [ env_name_filter, state_filter ]
    if env_vers:
        tag_filters.append(env_vers_filter)
    if ephemeral_env:
        tag_filters.append(ephemeral_filter)

    results = client.get_resources(TagFilters = tag_filters)
    resourceArns = []
    for resource in results['ResourceTagMappingList']:
        arn = resource['ResourceARN'].split(':')
        if arn[5].startswith('instance') and not instance_is_running(arn[5]):
            # Don't add an instance ARN if it's not running.
            logger.debug("Skipping instance: Not really running")
            continue
        if arn[5].startswith('nat') and not natgateway_exists(arn[5]):
            # Don't add a natgw ARN if it's not really there
            logger.debug("Skipping nat gw: Not really running")
            continue
            
        # Add non-instance ARN tagged as running and actual running instance
        resourceArns.append(resource['ResourceARN'])

    if len(resourceArns) > 0:
        return resourceArns

    return False


def tag_resources(config):
    """
    Tag resources based on action.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

    Returns: nothing
    """
    client = boto3.client('resourcegroupstaggingapi')
    env_name = config['environment'].get('name')
    env_vers = config['environment'].get('version', None)
    ephemeral_env = config['tags'].get('system_type', None)
        
    # Search for all entities with of a given environment name and
    # version AND the deployer_state. deployer_state value is
    # irrellevant, we're going to set it anyway.
    env_name_filter = { 'Key': 'env_name', 'Values': [ env_name ] }
    query = [ env_name_filter]

    if env_vers:
        env_vers_filter = { 'Key': 'env_version', 'Values': [ env_vers ] }
        query.append(env_vers_filter)

    if ephemeral_env:
        ephemeral_filter = { 'Key': 'system_type', 'Values': [ ephemeral_env ] }
        query.append(ephemeral_filter)
        
    results = client.get_resources(TagFilters = query)
    resourceArns = []
    if len(results['ResourceTagMappingList']) > 0:
        for resource in results['ResourceTagMappingList']:
            arn = resource['ResourceARN'].split(':')
            if ( (arn[5].startswith('instance') and instance_is_running(arn[5]))
                 or (arn[5].startswith('nat') and natgateway_exists(arn[5]))):
                resourceArns.append(resource['ResourceARN'])
            else:
                # If it's not an instance, we'll deal with it anyway.
                resourceArns.append(resource['ResourceARN'])

    if len(resourceArns) > 0:
        # tag_resources() can only handle 20 ARNs at a time.
        stupidAWSlimit = 20
        for arn in (range(0, len(resourceArns), stupidAWSlimit )):
            tag_results = client.tag_resources(
                ResourceARNList = resourceArns[ arn : arn + stupidAWSlimit ],
                Tags = { 'deployer_state' : config['tags']['deployer_state']})
    return


def instance_is_running(arn):
    """
    Checks to see if an instance is running or not.

    Args:
        arn: String representing the ARN of an instance

    Returns:
        True or False based on the state of the instance
    """
    instance = boto3.client('ec2')
    instance_id = arn.split('/')[1]
    try:
        inst = instance.describe_instances(InstanceIds=[ instance_id ])
        if len(inst['Reservations']) > 0:
            state = inst['Reservations'][0]['Instances'][0]['State']['Name']
            # If the ARN is an instance, only append it if it's running
            if state == 'running':
                return True
    except ClientError as e:
        logger.warn("Client: does not exist, skipping\n{}".format(e))
        pass
        
    return False


def natgateway_exists(arn):
    """
    Checks to see if a nat-gateway really exists or not.

    Args:
        arn: String representing the ARN of a nat-gateway

    Returns:
        True or False based on the state of the nat-gateway
    """
    nat = boto3.client('ec2')
    natgw_id = arn.split('/')[1]
    try:
        natgw = nat.describe_nat_gateways(NatGatewayIds=[ natgw_id ])
        if natgw['NatGateways'][0]['State'] == 'deleted':
            return False
    except ClientError as e:
        if e.response['Error']['Code'] == 'NatGatewayNotFound':
            # apparently it's a ghost natgw
            return False

    return True
    

def vpc_exists(config):
    """
    Checks to see if a VPC named for the current environment exists.

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

    Returns:
        True:  if the VPC exists.
        False: if the VPC does not exist.
    """
    vpc_name = '{}-{}'.format(config['project'], config['env_name'])
    vpc_client = boto3.client('ec2')
    filters = [{'Name': 'tag:Name', 'Values': [vpc_name]}]
    vpcs = vpc_client.describe_vpcs(Filters=filters)
    vpc_list = []
    for vpc in vpcs.get("Vpcs", []):
        tags = vpc.get("Tags", [])
        for tag in tags:
            if tag.get("Key") == 'Name':
                vpc_list.append(tag.get("Value"))

    return vpc_name in vpc_list


def list_vpcs(env):
    """
    Return a list of existing environments based on VPC environment tag 'env'

    Args:
        env: string name of a particular environement to check for
             existing VPCs. e.g. coral, malachite, lapis

    Returns:
        list of 'env' tag values. e.g. [ "coral-a", "coral-z", "coral-x" ]

    """

    # Attempting to return something like the output from this CLI command:
    #
    # $ aws ec2 describe-vpcs --filters Name=tag-key,Values=env --output
    # json --query 'Vpcs[*].Tags[?Key == `env`].Value[?contains(@,
    # `coral`)][]'
    # [
    #     "coral-a",
    #     "coral-z",
    #     "coral-x"
    # ]
    vpc_client = boto3.client('ec2')
    filters = [{'Name': 'tag:env',
                'Values': [ '{}-*'.format(env) ] } ]

    vpcs = vpc_client.describe_vpcs(Filters=filters)
    env_list = []
    for vpc in vpcs.get("Vpcs", []):
        tags = vpc.get("Tags", [])
        for tag in tags:
            if tag.get("Key") == 'env':
                env_list.append(tag.get("Value"))

    env_list.sort()
    return env_list


