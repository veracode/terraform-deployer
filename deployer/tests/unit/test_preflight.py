'''
Unit tests for the preflight.py module. Currently we do not test the
validity of anything dependent upon boto3 calls, since we haven't
figured out how to mock those calls out with moto properly.  And,
apparently, the features of boto3 we use have not yet been implemented
in moto yet.
'''
import boto3
import datetime
from mock import patch
from moto import ( mock_route53,
                   mock_s3 )
import os
import workdir
import pytest

import deployer.preflight as preflight


def mock_run_cmd(args, cwd=None):
    return "CWD: {}, Running command: {}".format(cwd, " ".join(args))


@pytest.fixture
def setup_teardown(scope="function"):
    passed_config = {
        "terraform": "git@gitlab.org:group/project.git?branch=made_up_branch",
        "tmpdir" : "/tmp/test_tmp_dir",
        "tfvars": "/tmp/test_tmp_dir/vars.tf",
        "tf_state_dir" :  "myenvname-a",
        "tf_state_bucket" :"123456789012-myproj-tfstate",
        "project_config" : "123456789012-myproj-data",
        "env_folder" : "myenvname-a",
        "route53_tld" : "subdomain.toplevel.domain"
    }
    workdir.options.path = passed_config['tmpdir']
    workdir.remove()

    yield passed_config
    # Make sure we clean up if anything else actually creates it
    workdir.options.path = passed_config['tmpdir']
    workdir.remove()


@pytest.fixture
def preconfig(setup_teardown):
    # Make sure test environment exists so we can test cleanup
    print("\nIn preconfig()")
    workdir.options.path = setup_teardown['tmpdir']
    workdir.create()

    print("passed_config['tmpdir'] = {}".format(setup_teardown['tmpdir']))
    return setup_teardown


@mock_s3
def test_presetup(setup_teardown):
    expected_file = os.path.join(setup_teardown['tmpdir'], 'vars.tf')
    return_config = preflight.pre_setup(setup_teardown)

    assert os.path.isdir(setup_teardown['tmpdir'])
    assert return_config['tfvars'] == expected_file
    assert return_config['tf_root'] == os.path.join(setup_teardown['tmpdir'],
                                                    'project')
    return


@mock_route53
@mock_s3
def test_setup(setup_teardown):
    expected_file = os.path.join(setup_teardown['tmpdir'], 'vars.tf')
    s3client = boto3.client('s3')
    s3client.create_bucket(Bucket=setup_teardown['project_config'])
    s3client.create_bucket(Bucket=setup_teardown['tf_state_bucket'])

    caller_ref = datetime.datetime.now().strftime('%s')
    r53client = boto3.client('route53')
    zone = r53client.create_hosted_zone(Name=setup_teardown['route53_tld'],
                                        CallerReference=caller_ref )
    zoneId = zone.get('HostedZone').get('Id').split('/')[2]
    config = preflight.pre_setup(setup_teardown)
    # We set this to "<computed>" if we're running "plan", so need to
    # undo it to simulate reality.
    config.pop('public_zone_id', None)
    return_config = preflight.setup(config)

    assert os.path.isdir(setup_teardown['tmpdir'])
    assert return_config['tfvars'] == expected_file
    assert return_config['public_zone_id'] == zoneId
    assert return_config['tf_root'] == os.path.join(setup_teardown['tmpdir'],
                                                    'project')
    return


@mock_route53
@mock_s3
def test_setup_with_local_dir0(setup_teardown):
    setup_teardown['terraform'] = "/some/local/path?branch=BRANCH_NAME"
    
    expected_file = os.path.join(setup_teardown['tmpdir'], 'vars.tf')

    s3client = boto3.client('s3')
    s3client.create_bucket(Bucket=setup_teardown['project_config'])
    s3client.create_bucket(Bucket=setup_teardown['tf_state_bucket'])

    caller_ref = datetime.datetime.now().strftime('%s')
    r53client = boto3.client('route53')
    zone = r53client.create_hosted_zone(Name=setup_teardown['route53_tld'],
                                        CallerReference=caller_ref )
    zoneId = zone.get('HostedZone').get('Id').split('/')[2]

    with patch('deployer.utils.run_command', mock_run_cmd):
        config = preflight.pre_setup(setup_teardown)
        # We set this to "<computed>" if we're running "plan", so need to
        # undo it to simulate reality.
        config.pop('public_zone_id', None)
        return_config = preflight.setup(config)
        
    assert return_config['tf_root'] == "/some/local/path"


@mock_route53
@mock_s3
def test_setup_with_local_dir_and_subdir(setup_teardown):
    setup_teardown['terraform'] = "/some/local/path?branch=BRANCH_NAME//subdir"
    
    expected_file = os.path.join(setup_teardown['tmpdir'], 'vars.tf')

    s3client = boto3.client('s3')
    s3client.create_bucket(Bucket=setup_teardown['project_config'])
    s3client.create_bucket(Bucket=setup_teardown['tf_state_bucket'])

    caller_ref = datetime.datetime.now().strftime('%s')
    r53client = boto3.client('route53')
    zone = r53client.create_hosted_zone(Name=setup_teardown['route53_tld'],
                                        CallerReference=caller_ref )
    zoneId = zone.get('HostedZone').get('Id').split('/')[2]

    with patch('deployer.utils.run_command', mock_run_cmd):
        config = preflight.pre_setup(setup_teardown)
        # We set this to "<computed>" if we're running "plan", so need to
        # undo it to simulate reality.
        config.pop('public_zone_id', None)
        return_config = preflight.setup(config)

    assert return_config['tf_root'] == "/some/local/path/subdir"


@mock_s3
def test_teardown(preconfig, setup_teardown):
    # define where we want the tmpdir to live.
    # make sure the tmpdir does not exist.
    expected_file = os.path.join(preconfig['tmpdir'], 'vars.tf')

    session = boto3.Session(profile_name='tests-random',)
    s3client = session.client('s3')
    s3client.create_bucket(Bucket=setup_teardown['project_config'])
    s3client.put_object(Bucket=setup_teardown['project_config'],
                        Key=setup_teardown['env_folder'])

    preflight.teardown(preconfig)

    print("expected file = {}".format(expected_file))
    assert not os.path.isdir(preconfig['tmpdir'])
    assert not os.path.exists(expected_file)


def test_sync_terraform(setup_teardown):
    workdir.options.path = setup_teardown['tmpdir']
    workdir.create()
    here = os.path.dirname(__file__)
    os.path.abspath(os.path.join(here, os.pardir, os.pardir, 'terraform'))
    git_url = 'git@gitlab.org:group/project?branch=made_up_branch'
    setup_teardown['terraform'] = git_url
    
    with patch('deployer.utils.run_command', mock_run_cmd):
        preflight.sync_terraform(setup_teardown)

    return


def test_write_vars(setup_teardown, preconfig):
    expected_file = os.path.join(setup_teardown['tmpdir'], 'vars.tf')
    # We need to create the bucket since this is all in Moto's 'virtual'
    # AWS account
    preflight.write_vars(setup_teardown, setup_teardown['tfvars'])
    assert os.path.exists(expected_file)

