'''
Unit tests for the bootstrap.py module. Currently we do not test the
validity of anything dependent upon boto3 calls, since we haven't
figured out how to mock those calls out with moto properly.  And,
apparently, the features of boto3 we use have not yet been implemented
in moto yet.
'''
import boto3
from mock import patch
from moto import mock_ec2
from moto import mock_s3
import os
import pytest

import deployer.tests.MyBoto3 as MyBoto3
import deployer.bootstrap as bootstrap
from   deployer.exceptions import MissingConfigurationParameterException

fake_boto3 = MyBoto3.MyBoto3()


def test_upload_staged_artifacts_undefined():
    passed_config = {
        "project_config" : "s3_bucket"
    }
    with pytest.raises(MissingConfigurationParameterException) as e:
        bootstrap.upload_staged_artifacts(passed_config)
    expected_msg  = "deployer.bootstrap: Configuration missing key fields. "
    expected_msg += "'staged_artifacts' is a required property"
    assert e.value.args[0] == expected_msg
    return


def test_upload_staged_artifacts_config_validation_error():
    config_no_project_config = {
        "staged_artifacts" : {
            "artifacts/foo" : "staged_artifacts/orig_foo",
            "artifacts/bar" : "staged_artifacts/orig_bar"
        }
    }

    with pytest.raises(MissingConfigurationParameterException) as e:
        bootstrap.upload_staged_artifacts(config_no_project_config)
    filename = "deployer.bootstrap"
    expected_msg = "{}: Configuration missing key fields. ".format(filename)
    expected_msg += "'project_config' is a required property"
    assert(e.value.args[0] == expected_msg)

    config_no_staged = { "project_config" : "s3_bucket" }
    with pytest.raises(MissingConfigurationParameterException) as e:
        bootstrap.upload_staged_artifacts(config_no_staged)
    filename = "deployer.bootstrap"
    expected_msg = "{}: Configuration missing key fields. ".format(filename)
    expected_msg += "'staged_artifacts' is a required property"
    assert(e.value.args[0] == expected_msg)
    return


def test_upload_staged_artifacts_no_local_dir():
    config = {
        "project_config" : "s3_bucket",
        "staged_artifacts" : {
            "artifacts/foo" : "local_dir/orig_foo",
        }
    }

    with pytest.raises(SystemExit) as e:
        bootstrap.upload_staged_artifacts(config)

    pwd = os.path.dirname(__file__)
    pardir = os.path.abspath(os.path.join(pwd,
                                          os.pardir,
                                          os.pardir,
                                          os.pardir))

    file_path = os.path.join(pardir,"local_dir/orig_foo")
    expected_msg = "File {} does not exist".format(file_path)
    assert(e.value.args[0] == expected_msg)

    return


def mock_isfile(args):
    return True


@mock_s3
@mock_ec2
def test_upload_staged_artifacts_upload_succeeds():
    config = {
        "project_config" : "s3_bucket",
        "staged_artifacts" : {
            "artifacts/foo" : "local_dir/orig_foo",
        }
    }
    s3client = boto3.client('s3')
    s3client.create_bucket(Bucket=config['project_config'])

    # Still need fake_boto3 here because of how moto's file_upload
    # call works...
    with patch('deployer.bootstrap.boto3', fake_boto3):
        with patch('deployer.bootstrap.os.path.isfile', mock_isfile):
            ret_val = bootstrap.upload_staged_artifacts(config)
    assert ret_val

    return


def mock_upload(*args):
    raise ValueError("FAILED TO UPLOAD")
    return False


@mock_s3
def test_upload_staged_artifacts_upload_fails():
    config = {
        "project_config" : "s3_bucket",
        "staged_artifacts" : {
            "artifacts/foo" : "local_dir/orig_foo",
        }
    }
    source_file = os.path.abspath(config['staged_artifacts']['artifacts/foo'])
    bucket_name = config['project_config']
    bucket_key = 'artifacts/foo'
    message = "FAILED TO UPLOAD"
    expected_error = "Error uploading {} to {}/{}: {}".format(source_file,
                                                              bucket_name,
                                                              bucket_key,
                                                              message)

    with pytest.raises(ValueError) as e:
        # Still need fake_boto3 here because of how moto's file_upload
        # call works...
        with patch('deployer.bootstrap.boto3', fake_boto3):
            with patch('deployer.bootstrap.os.path.isfile', mock_isfile):
                with patch('deployer.tests.MyBoto3.MyBoto3.S3Class.Object.upload_file', mock_upload):
                    bootstrap.upload_staged_artifacts(config)

    assert e.value.args[0] == expected_error
    return

