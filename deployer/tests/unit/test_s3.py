'''
Unit tests for the s3.py module. Currently we do not test the
validity of anything dependent upon boto3 calls, since we haven't
figured out how to mock those calls out with moto properly.  And,
apparently, the features of boto3 we use have not yet been implemented
in moto yet.
'''
import boto3
import pytest
from moto import mock_s3
from moto import mock_sts

from   deployer import s3


@pytest.fixture
def canned_config(scope="function"):
    # Stash the existing environment here
    return { "account_id" : "123456789012",
             "env_name"   : "myenvname-a",
             "project"    : "myproj"}


def teardown_function(function):
    return


@mock_s3
@mock_sts
def test_get_bucket_name_with_suffix(canned_config):
    expected_bucket_name = "123456789012-myproj-my_suffix"
    s3client = boto3.client('s3')
    s3client.create_bucket(Bucket=expected_bucket_name)
    returned_bucket_name = s3.get_bucket_name(canned_config, "my_suffix")

    assert returned_bucket_name == expected_bucket_name
    return


@mock_s3
@mock_sts
def test_get_bucket_name_no_suffix(canned_config):
    expected_bucket_name = "123456789012-myproj"
    s3client = boto3.client('s3')
    s3client.create_bucket(Bucket=expected_bucket_name)
    returned_bucket_name = s3.get_bucket_name(canned_config)
    assert returned_bucket_name == expected_bucket_name

    return


@mock_s3
@mock_sts
def test_get_env_bucket_name_with_suffix(canned_config):
    expected_bucket_name = "123456789012-myproj-myenvname-a-my_suffix"
    s3client = boto3.client('s3')
    s3client.create_bucket(Bucket=expected_bucket_name)
    returned_bucket_name = s3.get_env_bucket_name(canned_config,
                                                  "my_suffix")
    assert returned_bucket_name == expected_bucket_name

    return


@mock_s3
@mock_sts
def test_get_env_bucket_name_no_suffix(canned_config):
    expected_bucket_name = "123456789012-myproj-myenvname-a"
    s3client = boto3.client('s3')
    s3client.create_bucket(Bucket=expected_bucket_name)
    returned_bucket_name = s3.get_env_bucket_name(canned_config)
    assert returned_bucket_name == expected_bucket_name
    return


