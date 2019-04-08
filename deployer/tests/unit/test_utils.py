'''
Unit tests for the utils.py module. Currently we do not test the
validity of anything dependent upon boto3 calls, since we haven't
figured out how to mock those calls out with moto properly.  And,
apparently, the features of boto3 we use have not yet been implemented
in moto yet.
'''

import json
from   jsonschema.exceptions import ValidationError
import os
import workdir
import pytest

import deployer.utils as utils
from   deployer.exceptions import EnvironmentNameException


@pytest.fixture
def setup_teardown(scope="function"):
    # Make sure test environment doesn't exist
    mock_config = {
        "terraform": "git@gitlab.org:group/project.git?branch=made_up_branch",
        "aws_profile" : "tests-random",
        "aws_region" : "us-east-1",
        "availability_zones"  : [
            'us-east-1b',
            'us-east-1c',
            'us-east-1d',
            'us-east-1e'
        ],
        "account_id" : "555828001259",
        "environment" : {
            "name" : "myenvname",
            "version" : "a",
        },
        "env_name" : "myenvname-a",
        "tf_state" : "555828001259-unittests-my_env_name-a-tfstate",
        "project_config" : "555828001259-unittests-data",
        "project" : 'myproj'
    }

    tmpdir = '/tmp/test_tmp_dir'
    tmpfile = os.path.join(tmpdir, "test_vars.json")

    workdir.options.path = tmpdir
    workdir.create()
    with open(tmpfile, 'w') as tfile:
        json.dump(mock_config, tfile, indent=2)

    yield {'mock_config' : mock_config, 'filename' : tmpfile}
    # Make sure we clean up if anything else actually creates it
    workdir.options.path = tmpdir
    workdir.remove()


def test_load_vars(setup_teardown):
    loaded_data = utils.load_vars(setup_teardown['filename'])

    assert loaded_data == setup_teardown['mock_config']


def test_validate_env_name_num_tokens():
    shared_env_name = 'env'
    ephemeral_env_name = 'env-a'
    too_many_tokens = 'test-env-a'
    too_few_tokens = ''
    
    assert utils.validate_env_name(shared_env_name)
    assert utils.validate_env_name(ephemeral_env_name)

    except_msg = "Incorrect number of tokens. "
    except_msg += "Environment name can not be undefined"
    with pytest.raises(EnvironmentNameException) as e:
        utils.validate_env_name(too_few_tokens)
    assert(e.value.args[0] == except_msg)

    except_msg = "Incorrect number of tokens. Should be 1 or 2 tokens, not {}"
    with pytest.raises(EnvironmentNameException) as e:
        utils.validate_env_name(too_many_tokens)
    assert(e.value.args[0] == except_msg.format(len(too_many_tokens.split('-'))))


def test_validate_env_name_length():
    good_name = 'thisisalongenvname-a'
    bad_name = 'thisenvnameistoolong-a'

    assert utils.validate_env_name(good_name)

    except_msg = "Environment Name too long: {} characters. Limit: 20."
    with pytest.raises(EnvironmentNameException) as e:
        utils.validate_env_name(bad_name)
    assert (e.value.args[0] == (except_msg.format(len(bad_name))))


def test_validate_env_name_version_is_char():
    good_name = 'env-a'
    bad_name_double_char = 'env-aa'
    bad_name_number = 'env-1'

    assert utils.validate_env_name(good_name)

    except_msg = "Environment version is limited to a single character: {}"
    msg_double_char = except_msg.format(bad_name_double_char.split('-')[-1])
    msg_number = except_msg.format(bad_name_number.split('-')[-1])

    with pytest.raises(EnvironmentNameException) as e:
        utils.validate_env_name(bad_name_double_char)
    assert (e.value.args[0] == msg_double_char)

    with pytest.raises(EnvironmentNameException) as e:
        #pytest.set_trace()
        utils.validate_env_name(bad_name_number)
    assert (e.value.args[0] == msg_number)


@pytest.fixture
def basic_schema(scope="function"):
    return os.path.join(os.path.dirname(__file__),
                        os.pardir,
                        os.pardir,
                        'conf',
                        'default_schema.json')


@pytest.fixture
def terraform_schema(scope="function"):
    return os.path.join(os.path.dirname(__file__),
                        os.pardir,
                        os.pardir,
                        'conf',
                        'terraform_schema.json')


def test_validate_schema_good(basic_schema):
    basic_schema_file = basic_schema
    basic_complete_config = os.path.join(os.path.dirname(__file__),
                                         os.pardir,
                                         'test_data',
                                         'base_complete_config.json')
    basic_config = utils.load_vars(basic_complete_config)
    utils.validate_schema(basic_config, basic_schema_file)


def test_validate_schema_missing_required_property(basic_schema):
    basic_schema_file = basic_schema
    with pytest.raises(ValidationError) as e:
        basic_incomplete_config = os.path.join(os.path.dirname(__file__),
                                               os.pardir,
                                               'test_data',
                                               'base_incomplete_config.json')
        basic_config = utils.load_vars(basic_incomplete_config)
        utils.validate_schema(basic_config, basic_schema_file)

    assert e.value.args[0] == "'aws_profile' is a required property"


def test_validate_tf_schema_good(terraform_schema):
    tf_schema_file = terraform_schema
    tf_complete_config = os.path.join(os.path.dirname(__file__),
                                      os.pardir,
                                      'test_data',
                                      'terraform_complete_data.json')
    tf_config = utils.load_vars(tf_complete_config)
    utils.validate_schema(tf_config, tf_schema_file)


def test_validate_tf_schema_missing_required_property(terraform_schema):
    tf_schema_file = terraform_schema
    with pytest.raises(ValidationError) as e:
        tf_incomplete_config = os.path.join(os.path.dirname(__file__),
                                            os.pardir,
                                            'test_data',
                                            'terraform_incomplete_data.json')
        tf_config = utils.load_vars(tf_incomplete_config)
        utils.validate_schema(tf_config, tf_schema_file)
    assert e.value.args[0] == "'public_zone_id' is a required property"


def test_git_pull():
    repo = "/some/local/path"
    expected_cmd = ['git', 'pull']
    returned_cmd = utils.git_pull(repo)
    assert returned_cmd == expected_cmd

    
def test_git_clone_with_branch():
    repo = 'git@gitlab.org:group/project'
    branch = "made_up_branch"
    expected_cmd = ['git',
                    'clone',
                    '--recursive',
                    '-b',
                    branch,
                    repo]

    return_cmd = utils.git_clone(repo, branch)
    assert expected_cmd == return_cmd


def test_git_clone_without_branch():
    repo = 'git@gitlab.org:group/project'
    expected_cmd = ['git',
                    'clone',
                    '--recursive',
                    repo]

    return_cmd = utils.git_clone(repo)
    assert expected_cmd == return_cmd


def test_git_url_with_nongit_url():
    url = "/some/local/path"
    assert not utils.git_url(url)

    expected_repo = '/some/local/path'
    expected_branch = None
    expected_subdir = None
    (repo, branch, subdir) = utils.parse_git_url(url)


def test_git_url_with_nongit_url_with_branch():
    url = "/some/local/path?branch=BRANCH_NAME"
    assert not utils.git_url(url)

    expected_repo = '/some/local/path'
    expected_branch = 'BRANCH_NAME'
    expected_subdir = None
    (repo, branch, subdir) = utils.parse_git_url(url)
    

def test_git_url_with_nongit_url_with_subdir():
    url = "/some/local/path//subdir"
    assert not utils.git_url(url)

    expected_branch = None
    expected_subdir = 'subdir'
    (repo, branch, subdir) = utils.parse_git_url(url)


def test_git_url_with_nongit_url_with_branch_and_subdir():
    url = "/some/local/path?branch=BRANCH_NAME//subdir"
    assert not utils.git_url(url)

    expected_repo = '/some/local/path'
    expected_branch = 'BRANCH_NAME'
    expected_subdir = 'subdir'
    (repo, branch, subdir) = utils.parse_git_url(url)


def test_git_url_with_nongit_url_with_dotgit():
    # should fail
    url = "/some/local/path.git"
    #assert not utils.git_url(url)

    url = "/some/local/path?branch=BRANCH_NAME//subdir"

    expected_repo = '/some/local/path'
    expected_branch = 'BRANCH_NAME'
    expected_subdir = 'subdir'
    (repo, branch, subdir) = utils.parse_git_url(url)


def test_git_url_with_no_subdir_no_branch():
    url = 'git@gitlab.org:group/project.git'
    assert utils.git_url(url)

    expected_repo = 'git@gitlab.org:group/project.git'
    expected_branch = None
    expected_subdir = None
    (repo, branch, subdir) = utils.parse_git_url(url)

    assert expected_repo == repo
    assert expected_branch == branch
    assert expected_subdir == subdir

    
def test_git_url_with_branch_no_subdir():
    url = 'git@gitlab.org:group/project.git?branch=made_up_branch'
    assert utils.git_url(url)

    expected_repo = 'git@gitlab.org:group/project.git'
    expected_branch = 'made_up_branch'
    expected_subdir = None
    (repo, branch, subdir) = utils.parse_git_url(url)

    assert expected_repo == repo
    assert expected_branch == branch
    assert expected_subdir == subdir


def test_git_url_with_subdir_no_branch():
    url = 'git@gitlab.org:group/project.git//subdir'
    assert utils.git_url(url)

    expected_repo = 'git@gitlab.org:group/project.git'
    expected_branch = None
    expected_subdir = 'subdir'

    (repo, branch, subdir) = utils.parse_git_url(url)

    assert expected_repo == repo
    assert expected_branch == branch
    assert expected_subdir == subdir


def test_git_http_url_with_no_branch_no_subdir():
    url = 'https://git@gitlab.org:group/project.git'
    assert utils.git_url(url)

    expected_repo = 'https://git@gitlab.org:group/project.git'
    expected_branch = None
    expected_subdir = None

    (repo, branch, subdir) = utils.parse_git_url(url)

    assert expected_repo == repo
    assert expected_branch == branch
    assert expected_subdir == subdir


def test_git_http_url_with_branch_no_subdir():
    url = 'https://git@gitlab.org:group/project.git?branch=made_up_branch'
    assert utils.git_url(url)

    expected_repo = 'https://git@gitlab.org:group/project.git'
    expected_branch = 'made_up_branch'
    expected_subdir = None
    (repo, branch, subdir) = utils.parse_git_url(url)

    assert expected_repo == repo
    assert expected_branch == branch
    assert expected_subdir == subdir


def test_git_http_url_with_subdir_no_branch():
    url = 'https://git@gitlab.org:group/project.git//subdir'
    assert utils.git_url(url)
    
    expected_repo = 'https://git@gitlab.org:group/project.git'
    expected_branch = None
    expected_subdir = 'subdir'
    (repo, branch, subdir) = utils.parse_git_url(url)

    assert expected_repo == repo
    assert expected_branch == branch
    assert expected_subdir == subdir


def ttest_git_http_url_with_branch_and_subdir():
    url = 'git@gitlab.org:group/project.git?branch=made_up_branch//subdir'
    expected_repo = 'git@gitlab.org:group/project.git'
    expected_branch = 'made_up_branch'
    expected_subdir = 'subdir'
    (repo, branch, subdir) = utils.parse_git_url(url)

    assert expected_repo == repo
    assert expected_branch == branch
    assert expected_subdir == subdir

    return


def test_local_dir_from_repo_full_url():
    url = 'git@gitlab.org:group/project.git?branch=made_up_branch//subdir'
    expected_dir = 'project/subdir'
    returned_dir = utils.local_dir_from_git_repo(url)

    assert expected_dir == returned_dir


def test_local_dir_from_repo_just_repo():
    repo = 'git@gitlab.org:group/project.git'
    expected_dir = 'project'
    returned_dir = utils.local_dir_from_git_repo(repo)
    assert expected_dir == returned_dir

    
def test_get_tf_location_from_local_path():
    mock_config = { "terraform": "/some/local/path" }
    expected_root = "/some/local/path"
    returned_root = utils.get_tf_location(mock_config)

    assert expected_root == returned_root


def test_get_tf_location_from_git_url():
    mock_config = {
        "tmpdir" : '/tmp/test_tmp_dir',
        "terraform": "git@gitlab.org:group/project.git?branch=made_up_branch"
    }
    expected_root = os.path.join( mock_config['tmpdir'], "project" )
    returned_root = utils.get_tf_location(mock_config)

    assert expected_root == returned_root


def test_parseConfigOpts():

    mock_args = [ '{ "tmpdir" : "/fizzle/drizzle" }',
                  '{ "environment" : { "name" : "coral", "version" : "q"} }',
                  '{ "random_list" : [ 0, 1, 2, 3, 4, 5 ] }' ]

    expected = { "tmpdir" : "/fizzle/drizzle",
                 "environment" : { "name" : "coral",
                                   "version" : "q"},
                 "random_list" : [ 0, 1, 2, 3, 4, 5 ] }

    return_stuff = utils.parseConfigOpts(mock_args)
    assert return_stuff == expected


def test_git_set_branch():
    url = "/some/local/path?branch=BRANCH_NAME"

    assert not utils.git_url(url)
    expected_cmd = [ 'git', 'checkout', 'BRANCH_NAME' ]

    (repo, branch, subdir) = utils.parse_git_url(url)
    returnd_cmd = utils.git_set_branch(branch)

    assert expected_cmd == returnd_cmd


def test_run_command():

    import platform
    systype = platform.system()

    truefalse = {
        'Darwin' : '/usr/bin',
        'Linux' : '/bin'
    }

    command = [ "{}/true".format(truefalse[systype]) ]
    # pytest.set_trace()
    expected_code = 0
    return_code = utils.run_command(command, cwd = '/tmp')
    assert return_code == expected_code
    
    command = [ "{}/false".format(truefalse[systype]) ]
    # pytest.set_trace()
    expected_code = 1
    return_code = utils.run_command(command, cwd = '/tmp')
    assert return_code == expected_code
