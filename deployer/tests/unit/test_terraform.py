'''
Unit tests for the terraform.py module. Currently we do not test
actual calls to terraform, just the various utility methods in
terraform.py which are testable.

'''
import pytest
import deployer.terraform as tf


@pytest.fixture
def mock_config(scope="function"):
    return {
        "aws_profile" : "my_aws_profile",
        "aws_region" : "us-east-1",
        "availability_zones"  : [
            'us-east-1b',
            'us-east-1c',
            'us-east-1d',
            'us-east-1e'
        ],
        "account_id" : "123456789012",
        "environment" : {
            "name" : "myenvname",
            "version" : "a",
        },
        "env_name" : "myenvname-a",
        "tf_state_bucket" : "123456789012-myproj-tfstate",
        "tf_state" : "myenvname-a.tfstate",
        "project_config" : "123456789012-myproj-data",
        "project" : 'myproj',
        "tfvars" : '/tmp/test_tmp_dir/vars.tf'
    }


def test_tf_get():
    expected = ['terraform', 'get']
    result = tf.get()
    assert expected == result
    return


def test_remote_state(mock_config):
    bucket = '-backend-config=bucket=123456789012-myproj-tfstate'
    key = '-backend-config=key=myenvname-a.tfstate'
    expected = ['terraform',
                'init',
                '-backend=true',
                bucket,
                key,
                '-backend-config=region=us-east-1',
                '-backend-config=profile=my_aws_profile']
    result = tf.remote_state(mock_config)
    assert expected == result
    return


def test_tf_push():
    expected = ['terraform', 'state', 'push', '.terraform/terraform.tfstate']
    result = tf.remote_push()
    assert expected == result
    return


def test_tf_pull():
    expected = ['terraform', 'state', 'pull']
    result = tf.remote_pull()
    assert expected == result
    return


def test_tf_validate(mock_config):
    expected = ['terraform',
                'validate',
                "-var='aws_region=us-east-1'",
                '-var-file=/tmp/test_tmp_dir/vars.tf']
    result = tf.validate(mock_config)
    assert expected == result
    return


def test_tf_plan_with_plan_action(mock_config):
    expected = ['terraform',
                'plan',
                "-var='aws_region=us-east-1'",
                '-var-file=/tmp/test_tmp_dir/vars.tf',
                ]

    mock_action = 'plan'
    result = tf.plan(mock_config, mock_action)
    assert result == expected
    return


def test_tf_plan_with_create_action(mock_config):
    expected = ['terraform',
                'plan',
                "-var='aws_region=us-east-1'",
                '-var-file=/tmp/test_tmp_dir/vars.tf',
                ]
    mock_action = 'create'
    result = tf.plan(mock_config, mock_action)
    assert result == expected
    return


def test_tf_plan_with_destroy_action(mock_config):
    expected = ['terraform',
                'plan',
                '-destroy',
                "-var='aws_region=us-east-1'",
                '-var-file=/tmp/test_tmp_dir/vars.tf',
                ]
    mock_action = 'destroy'
    result = tf.plan(mock_config, mock_action)
    assert result == expected
    return


def test_tf_apply(mock_config):
    expected = ['terraform',
                'apply',
                "-var='aws_region=us-east-1'",
                '-var-file=/tmp/test_tmp_dir/vars.tf',
                ]
    result = tf.apply(mock_config)
    assert result == expected
    return


def test_tf_destroy(mock_config):
    expected = ['terraform',
                'destroy',
                '-force',
                "-var='aws_region=us-east-1'",
                '-var-file=/tmp/test_tmp_dir/vars.tf',
                ]
    result = tf.destroy(mock_config)
    assert result == expected
    return


def test_tf_output():
    mock_tfvar = 'foo'

    expected = ['terraform',
                'output',
                'foo',
                ]
    result = tf.output(mock_tfvar)
    assert result == expected
    return
