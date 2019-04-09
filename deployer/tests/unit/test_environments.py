'''
Unit tests for the environments.py module.
'''
import boto3
import json
import pytest
from   mock import patch
from   moto import ( mock_ec2,
                     mock_s3 )

from   deployer.exceptions    import ( EnvironmentExistsException,
                                       InvalidCommandException)
import deployer.environments   as    env

import deployer.tests.MyBoto3 as MyBoto3

fake_boto3 = MyBoto3.MyBoto3()


def mock_run_cmd(args, cwd=None):
    print("CWD: {}, Running command: {}".format(cwd, " ".join(args)))
    return 0


def mock_inst_is_running(instance_id):
    return True


@pytest.fixture
def mock_config(scope="function"):
    return {
        "terraform": "git@gitlab.org:group/project.git?branch=made_up_branch",
        "aws_profile": "tests-random",
        "aws_region": "us-east-1",
        "availability_zones": [
            'us-east-1b',
            'us-east-1c',
            'us-east-1d',
            'us-east-1e'
        ],
        "account_id": "123456789012",
        "environment": {
            "name": "myenvname",
            "version": "a",
        },
        'tags': {
            'system_type' : 'mock_product'
        },
        "env_name": "myenvname-a",
        "tf_state": "myenvname-a.tfstate",
        "tf_state_bucket": "123456789012-myproj-tfstate",
        "project_config": "123456789012-myproj-data",
        "project": 'myproj',
        "tfvars" : '/tmp/test_tmp_dir/vars.tf',
        "tf_root": '/tmp/test_tmp_dir/terraform',
        "tmpdir" : '/tmp/test_tmp_dir'
    }


@mock_ec2
def mock_vpcs(scope="function"):
    ec2c = boto3.client('ec2',
                        region_name='us-east-1',
                        aws_access_key_id='',
                        aws_secret_access_key='',
                        aws_session_token='')
    vpc1 = ec2c.create_vpc(CidrBlock='10.1.0.0/16').get('Vpc').get('VpcId')
    vpc2 = ec2c.create_vpc(CidrBlock='10.2.0.0/16').get('Vpc').get('VpcId')
    vpc3 = ec2c.create_vpc(CidrBlock='10.3.0.0/16').get('Vpc').get('VpcId')
    ec2c.create_tags(Resources = [ vpc1 ],
                     Tags=[ {'Key':'Name',
                             'Value' : 'myproj-myenvname-a'},
                            {'Key':'env',
                             'Value' : 'myenvname-a'} ])
    ec2c.create_tags(Resources = [ vpc2 ],
                     Tags=[ {'Key':'Name',
                             'Value' : 'myproj-myenvname-b'},
                            {'Key':'env',
                             'Value' : 'myenvname-b'} ])
    ec2c.create_tags(Resources = [ vpc3 ],
                     Tags=[ {'Key':'Name',
                             'Value' : 'myproj-myenvname-c'},
                            {'Key':'env',
                             'Value' : 'myenvname-c'} ])
    return ec2c


@mock_s3
@mock_ec2
def test_create_env_exists(mock_config):
    expected_arn = [ "arn:aws:ec2:us-east-1:419934374614:instance/i-c3bef428" ]
    expected_msg = "\n\nAn environment with the name {} already exists."
    expected_msg += "\nPlease tear it down before trying to rebuild."
    expected_msg += "\n\n{}".format(json.dumps(expected_arn, indent=4))
        
    env_name = mock_config['env_name']
    if 'tags' in mock_config and 'system_type' in mock_config['tags']:
        env_name = "-".join([mock_config['tags']['system_type'], env_name ])
        
    s3client = boto3.client('s3')
    s3client.create_bucket(Bucket="123456789012-myproj-tfstate")

    with pytest.raises(EnvironmentExistsException) as e:
        ec2c = boto3.client('ec2')
        vpc1 = ec2c.create_vpc(CidrBlock='10.1.0.0/16').get('Vpc').get('VpcId')
        ec2c.create_tags(Resources = [ vpc1 ],
                         Tags=[ {'Key':'Name',
                                 'Value' : 'myproj-myenvname-a'},
                                {'Key':'env',
                                 'Value' : 'myenvname-a'},
                                {'Key' : 'system_type',
                                 'Value' : 'mock_product'} ])

        with patch('deployer.aws.instance_is_running', mock_inst_is_running):
            with patch('deployer.utils.run_command', mock_run_cmd):
                with patch('deployer.aws.boto3', fake_boto3):
                    env.create(mock_config)

    from termcolor import colored
    assert(e.value.args[0] == colored(expected_msg.format(env_name), 'red'))
    
    return


@mock_s3
@mock_ec2
def test_create_env_does_not_exist(mock_config):
    mock_config['environment']['name'] = 'myotherenvname'
    mock_config['environment']['version'] = 'z'
    s3client = boto3.client('s3')
    s3client.create_bucket(Bucket="123456789012-myproj-tfstate")
    with patch('deployer.utils.run_command', mock_run_cmd):
        with patch('deployer.aws.boto3', fake_boto3):
            assert env.create(mock_config)

    return


def test_precheck_valid_keys(mock_config):
    actions = [ 'create', 'destroy' ]
    for action in actions:
        with patch('deployer.utils.run_command', mock_run_cmd):
            env._precheck(mock_config, action)
    return


def test_precheck_invalid_key(mock_config):
    with patch('deployer.utils.run_command', mock_run_cmd):
        with pytest.raises(InvalidCommandException):
            env._precheck(mock_config, 'invalid_command')
    return


@mock_ec2
def test_list_deployed_environment_versions(mock_config):
    mock_vpcs()
    env_name = mock_config['environment']['name']
    with patch('deployer.aws.boto3', fake_boto3):
        existing_env_versions = env.list_deployed_environment_versions(env_name)

    assert existing_env_versions == [ 'a', 'b', 'c' ]
    return


@mock_ec2
def test_get_next_env_version(mock_config):
    mock_vpcs()
    env_name = mock_config['environment']['name']
    expected = 'd'

    with patch('deployer.aws.boto3', fake_boto3):
        with patch('deployer.aws.instance_is_running', mock_inst_is_running):
            next_version = env.get_next_version(env_name)

    assert expected == next_version
