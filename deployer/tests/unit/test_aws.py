'''
Unit tests for the aws.py module. Currently we do not test the
validity of anything dependent upon boto3 calls, since we haven't
figured out how to mock those calls out with moto properly.  And,
apparently, the features of boto3 we use have not yet been implemented
in moto yet.
'''
import os
import pytest
import boto3
from mock import patch
from moto import mock_s3
from moto import mock_ec2
from moto import mock_iam
from moto import mock_sts

import deployer.aws as aws
import deployer.tests.MyBoto3 as MyBoto3

_environment = {}
config = {}
expected_config = {}
fake_boto3 = MyBoto3.MyBoto3()


@pytest.fixture
def setup_function(scope="function"):
    # Stash the existing environment here
    _environment = dict(os.environ)
    os.environ = {}
    return


def teardown_function(function):
    os.environ = _environment
    return


@pytest.fixture
def mock_config(scope="function"):
    return { "aws_profile" : "veracode-random",
             "aws_region"  : "us-east-1",
             "environment" : {
                 "name" : "myenvname",
                 "version" : "a",
             },
             "project" : 'myproj',
             "route53_tld" : "my.toplevel.domain" }


@pytest.fixture
def mock_config_with_tags(scope="function"):
    return { "aws_profile" : "veracode-random",
             "aws_region"  : "us-east-1",
             "tags" : {
                 "key1" : "value1",
                 "key2" : "value2"
             },
             "environment" : {
                 "name" : "myenvname",
                 "version" : "a",
             },
             "project" : 'myproj',
             "route53_tld" : "my.toplevel.domain" }


@pytest.fixture
def mock_env(scope="function"):
    return {
        "AWS_DEFAULT_PROFILE" : "veracode-random",
        "AWS_PROFILE" : "veracode-random",
        "AWS_DEFAULT_REGION" : "us-east-1"}


@mock_ec2
def mock_vpcs(scope="function"):
    ec2c = boto3.client('ec2')
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
def test_configure_config(mock_config, setup_function):
    # Make sure we start with an empty environment
    assert dict(os.environ) == {}

    expected_config = {
        "aws_profile" : "veracode-random",
        "aws_region" : "us-east-1",
        "availability_zones"  : [
            'us-east-1a',
            'us-east-1b',
            'us-east-1c'
        ],
        "account_id" : "123456789012",
        "environment" : {
            "name" : "myenvname",
            "version" : "a",
        },
        "env_name" : "myenvname-a",
        "env_folder" : "myenvname-a",
        "tf_state" :  "myenvname-a.tfstate",
        "tf_state_bucket" :"123456789012-myproj-tfstate",
        "project_config" : "123456789012-myproj-data",
        "project" : 'myproj',
        "route53_tld" : "my.toplevel.domain"
    }

    # fake_boto3 still required here because mock_iam has not yet
    # implemented the list_account_aliases() method yet, which is used
    # in aws.configure().
    s3client = boto3.client('s3')
    s3client.create_bucket(Bucket=expected_config['project_config'])
    s3client.create_bucket(Bucket=expected_config['tf_state_bucket'])
    with patch('deployer.aws.boto3', fake_boto3):
        # We need to create the bucket since this is all in Moto's 'virtual'
        # AWS account
        returned_config = aws.configure(mock_config)
    assert returned_config == expected_config

    return


@mock_s3
@mock_ec2
def test_configure_config_with_tags_no_version(mock_config_with_tags,
                                               setup_function):
    # Make sure we start with an empty environment
    assert dict(os.environ) == {}
    mock_config_with_tags['environment'].pop('version')
    
    expected_config = {
        "aws_profile" : "veracode-random",
        "aws_region" : "us-east-1",
        "availability_zones"  : [
            'us-east-1a',
            'us-east-1b',
            'us-east-1c'
        ],
        "account_id" : "123456789012",
        "environment" : {
            "name" : "myenvname"
        },
        "aws_region"  : "us-east-1",
        "tags" : {
            "key1" : "value1",
            "key2" : "value2",
            "env_name" : "myenvname"
        },

        "env_name" : "myenvname",
        "env_folder" : "myenvname",
        "tf_state" :  "myenvname.tfstate",
        "tf_state_bucket" :"123456789012-myproj-tfstate",
        "project_config" : "123456789012-myproj-data",
        "project" : 'myproj',
        "route53_tld" : "my.toplevel.domain"
    }

    # fake_boto3 still required here because mock_iam has not yet
    # implemented the list_account_aliases() method yet, which is used
    # in aws.configure().
    s3client = boto3.client('s3')
    s3client.create_bucket(Bucket=expected_config['project_config'])
    s3client.create_bucket(Bucket=expected_config['tf_state_bucket'])
    with patch('deployer.aws.boto3', fake_boto3):
        # We need to create the bucket since this is all in Moto's 'virtual'
        # AWS account
        returned_config = aws.configure(mock_config_with_tags)
    assert returned_config == expected_config

    return


@mock_s3
@mock_ec2
def test_configure_config_with_tags(mock_config_with_tags, setup_function):
    # Make sure we start with an empty environment
    assert dict(os.environ) == {}

    expected_config = {
        "aws_profile" : "veracode-random",
        "aws_region" : "us-east-1",
        "availability_zones"  : [
            'us-east-1a',
            'us-east-1b',
            'us-east-1c'
        ],
        "account_id" : "123456789012",
        "environment" : {
            "name" : "myenvname",
            "version" : "a",
        },
        "aws_region"  : "us-east-1",
        "tags" : {
            "key1" : "value1",
            "key2" : "value2",
            "env_name" : "myenvname",
            "env_version" : "a"
        },
        "env_name" : "myenvname-a",
        "env_folder" : "myenvname-a",
        "tf_state" :  "myenvname-a.tfstate",
        "tf_state_bucket" :"123456789012-myproj-tfstate",
        "project_config" : "123456789012-myproj-data",
        "project" : 'myproj',
        "route53_tld" : "my.toplevel.domain"
    }

    # fake_boto3 still required here because mock_iam has not yet
    # implemented the list_account_aliases() method yet, which is used
    # in aws.configure().
    s3client = boto3.client('s3')
    s3client.create_bucket(Bucket=expected_config['project_config'])
    s3client.create_bucket(Bucket=expected_config['tf_state_bucket'])
    with patch('deployer.aws.boto3', fake_boto3):
        # We need to create the bucket since this is all in Moto's 'virtual'
        # AWS account
        returned_config = aws.configure(mock_config_with_tags)
    assert returned_config == expected_config

    return


@mock_s3
@mock_iam
def test_configure_env(mock_config, mock_env, setup_function):
    # Make sure we start with an empty environment
    assert dict(os.environ) == {}

    # fake_boto3 still required here because mock_iam has not yet
    # implemented the list_account_aliases() method yet, which is used
    # in aws.configure().
    with patch('deployer.aws.boto3', fake_boto3):
        session = boto3.Session(profile_name='veracode-random')
        s3client = session.client('s3')
        s3client.create_bucket(Bucket="123456789012-myproj-data")
        aws.configure(mock_config)
        returned_env = dict(os.environ)
    assert returned_env == mock_env
    return


@mock_iam
def test_get_account_name():
    '''list_account_aliases() Not yet implemented.'''
    # assert aws.get_account_name()
    # return
    pass


@mock_sts
def test_get_account_id(mock_config):
    mock_config['account_id'] = "123456789012"
    returned_id = aws.get_account_id()
    assert returned_id == mock_config['account_id']
    return


@mock_ec2
def test_get_current_region():
    expected_region = 'us-east-1'
    returned_region = aws.get_current_region()

    assert expected_region == returned_region
    return


def test_get_current_az_list_passing_list():
    expected_zones = ["az-1","az-2","az-3","az-4"]
    passed_config = { "availability_zones" :  expected_zones }
    returned_zones = aws.get_current_az_list(passed_config)
    assert expected_zones == returned_zones
    return


@mock_ec2
def test_get_current_az_list_no_list():
    passed_config = {}
    expected_zones = ["us-east-1a",
                      "us-east-1b",
                      "us-east-1c",
                      "us-east-1d",
                      "us-east-1e",
                      "us-east-1f"]
    returned_zones = aws.get_current_az_list(passed_config)

    for zone in returned_zones:
        assert zone in expected_zones
    return


@mock_ec2
def test_list_vpcs(mock_config):
    env = mock_config['environment']['name']
    expected_vpcs = ['myenvname-a', 'myenvname-b', 'myenvname-c']

    # Create our mock VPCs.
    mock_vpcs()
    returned_vpcs = aws.list_vpcs(env)
    assert returned_vpcs == expected_vpcs
    return


@mock_ec2
@mock_s3
def test_environment_does_not_exist(mock_config):
    mock_config['environment']['name'] = 'myenvname'
    mock_config['environment']['version'] = 'z'
    with patch('deployer.aws.boto3', fake_boto3):
        assert not aws.environment_exists(mock_config)
    return
