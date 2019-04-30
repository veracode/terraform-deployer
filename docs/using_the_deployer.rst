Here are some basic steps which should get you started using the terraform-deployer deployer from your desktop.   In this exercise, I use a generic project as an example. I also demonstrate how to use the deployer to deploy a service into a pre-existing environment by first deploying that pre-existing environment.  This is done in order show how you might deploy a service into a shared infrastructure which you might not have control over, or which someone else may have created to be shared across multiple teams. In these cases, you would skip the deployment of the pre-existing environment (because it already exists) and you'd simply have your service refer to a pre-existing state file containing all the data necessary to launch your service into that environment.

Installing the Deployer
Prerequisites
Creating a python virtual environment

I recommend using pyenv plus the pyenv-virtuallenv plugin. Resources here:

https://github.com/pyenv/pyenv
https://github.com/pyenv/pyenv-virtualenv
This is a good practice whether or not your plan on working on the deployer itself. It allows you to install the deployer and all dependencies into a virtual environment and keep that separate from other python environments you may have for other projects as well as keeping your base OS install clean.

Make sure you create your python virtual environment with python version 2.7.x.  The deployer does not work with python 3.x yet.

Install the AWS CLI tools
Follow the direction to install inside the virtualenv: https://docs.aws.amazon.com/cli/latest/userguide/awscli-install-virtualenv.html

This should be done from inside the Python virtualenv you just created. For example:

$ pyenv virtualenv 2.7.12 my-deployer-env
New python executable in /Users/pll/.pyenv/versions/2.7.12/envs/my-deployer-env/bin/python2.7
Also creating executable in /Users/pll/.pyenv/versions/2.7.12/envs/my-deployer-env/bin/python
...
$ pyenv activate my-deployer-env
pyenv-virtualenv: prompt changing will be removed from future release. configure `export PYENV_VIRTUALENV_DISABLE_PROMPT=1' to simulate the behavior.
(my-deployer-env): ~ $ pip install awscli
...
(my-deployer-env): ~ $ 
AWS Credentials File
For any AWS account in which you intend to have the deployer operate, you must have a set of AWS API credentials in your ~/.aws/credentials file for the deployer to use. The name of the profile listed in the credentials file must match the value assigned to aws_profile variable set in the JSON config file passed to the deployer at run time. For example, if the JSON config file for the deployer contains:

{
    "aws_profile": "aws-nonprod",
...
}
Then the ~/.aws/credentials file must contain a section like this:

[aws-nonprod]
aws_access_key_id=XXXXXXXXXXXXXXXXXXXX
aws_secret_access_key=YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY

Install Terraform
Get that from here. The currently supported version .0.10.6. The latest versions (0.11.x) may work, but are completely untested at this time.  This is a zip file, so just unzip it in place to some directory in your shell path.  I usually place it in /usr/local/bin.

Optional but really nice to have tools
SAWS
SAWS is a really nice-to-have tool. It's a console-based, aws cli tool which has command completion, command recall, and command editing features.  Use pip install for this from within your new virtual environment.

$ pip install saws
JMESPath Terminal
This is a tool that allows you to look at JSON output (whether in a file, or piped directly to it) and try out various queries against the data returned in order to form an expression you might pass to the aws cli --query option in order to pare down the results to exactly the output you really want to see.

$ pip install jmespath-terminal
You can then use it like this:

(my-deployer-env):~ $ aws ssm get-parameters --region 'us-east-1' --with-decryption --name "/some/path/some_key"
{
    "InvalidParameters": [],
    "Parameters": [
        {
            "Version": 2,
            "Type": "SecureString",
            "Name": "/some/path/some_key",
            "Value": "xxxxxxxxxxx"
        }
    ]
}
But say we simply wanted the output of the 'Name' and Value fields output to our terminal.  We could simply pipe this query to jpterm like this:

 

(my-deployer-env):~ $ aws ssm get-parameters --region 'us-east-1' --with-decryption --name "/some/path/some_key" | jpterm
which results in a screen like this, in which you an test JMESPath queries:

terraform-deployer > Deploy from your desktop > jpterm.png terraform-deployer > Deploy from your desktop > jpquery.png

Once we've refined what our query might be, we can apply it to the aws cli (in saws if we want) like this (with 3 different output styles depending on what you want):

saws> aws ssm get-parameters --with-decryption --name '/some/path/some_key' -
-query "Parameters[?Name == '/some/path/some_key'].[Name, Value]"
[
    [
        "/some/path/some_key",
        "some_value"
    ]
]
saws> aws ssm get-parameters --with-decryption --name '/some/path/some_key' -
-query "Parameters[?Name == '/some/path/some_key'].[Name, Value]" --output ta
ble
---------------------------------------
|            GetParameters            |
+----------------------+--------------+
|  /some/path/some_key |  some_value  |
+----------------------+--------------+

saws> aws ssm get-parameters --with-decryption --name '/some/path/some_key' -
-query "Parameters[?Name == '/some/path/some_key'].[Name, Value]" --output te
xt
 
/some/path/some_key     some_value

Installing the deployer using pip install

This is likely the easiest, mode expedient route.  It is also advisable to create a virtual environment for this route as well, though not absolutely necessary.

$ pip install --extra-index-url https://pypi.python.org/simple deployer
Installing and running the deployer in a deployer development environment

Checkout the deployer project:
https://github.com/veracode/terraform-deployer/deployer

Run: 

$ pip install -r requirements.txt


In the deployer top level directory, run:

$ make build
This creates a useable executable for you by installing the project into your environment.  You will see output like the following:


$ make build
python setup.py install > /dev/null
python setup.py build > /dev/null
$

Setting up the "mock runner" environment
On Github "runners" (the Docker containers that run the pipelines) the code repo (for which the runner has been invoked to "run a pipeline for") is checked out to a standad place "on disk". That path is of the form: /builds/<github group name>/<github project name>. So for example, for jobservice, the "on disk" location on a runner would be: /builds/was-job-runtime/was-jobservice-server.  Therefore, we need to create that base location for the deployer to clone the repository into and then clone the repository into it.

Create the directory hierarchy and clone the code repository:

$ mkdir -p /builds/was-job-runtime	
$ sudo chown -R <your username> /builds
$ cd /builds/was-job-runtime
$ git clone --recursive git@github.com/veracode/core-infrastructure.git
NOTE: If you are working in a deployer development repo go back to that location now. If you used *pip install* to install the deployer, disregard this step.
NOTE: The deployer can take advantage of git submodules. In fact, Github has built-in support for dealing with git submodules  as well. If the project you are checking out from git lab uses git submodules, use the --recursive option so the submodule gets checked out to right location.

 

Figure out what your GITHUB_USER_ID is and export it as an environment variable. for example, mine is 66:

$ export GITHUB_USER_ID=66
We do this because many people may be running a development environment, and rather than stand up a static shared environment we create unique "shared environments" (even though they're not really shared) which won't collide with anyone else's. This also allows for someone to develop and evolve the "core infrastructure" code as well and test this on a branch without negatively affecting other developers who may not want their infrastructure to break while working on other things and depending on the core infrastructure to "just work".


 Create a Github API_TOKEN here: https://github.com/veracode/profile/personal_access_tokens

This is used to clone repositories from github using the https method (as opposed to ssh, or other protocols). This is how the pipelines can clone repositories other than the one for which a given pipeline is running. The pipelines (should) already have an API_TOKEN variable set for the runners to use. Because we are mocking out how the runner operates, we're going to do the same, even though it's not strictly necessary (but how to use the deployer without this is outside the scope here, so just do this and move on (smile)


Export the API_TOKEN as an environment variable


Consider the scenario where an ephemeral, application-based infrastructure being launched into a pre-existing, shared infrastructure. In the case of a development pipeline, each developer may want to have things isolated such that they each have their own "pre-existing" infrastructure, which is launched just prior to deploying the ephemeral, service-based infrastructure. To accomplish this, a pipeline being run from the service/application repository would only have access to that repository. If the "shared" infrastructure code is in a different repository, the Github runner has no access to that, and therefore, the deployer can't find it since it's not there.  To get around this, we export an API_TOKEN in Github which allows us to check out that repository.  When deploying from our desktop and trying to mock the Github runner environment, we must do the same thing.

$ export API_TOKEN=XXXXXXXXXXXXXXXXXXXX
If the environment variable API_TOKEN is set in your environment, AND the deployer finds the token API_TOKEN in the config file like this:

{
    "terraform" : "https://github-ci-token:API_TOKEN@github.com/veracode/was-common/was-core-infrastructure.git",
...
}
it will replace the string 'API_TOKEN' with the value of the environment variable of the same name.  This allows the deployer to check code out of Github directly. Github runners can only access the code repository for the repository the pipeline was generated from. Therefore, if you're attempting to run a pipeline for projectB, which has a dependency on projectA, and you need to checkout projectA first, the runner has no way of doing this without authentication. The API_TOKEN is that authentication. 

Configuration and deployment of the environments
Generate a config file for both the “pre-existing” environment *and* the service environment:

$ ./bin/gen_config -c /builds/was-job-runtime/was-jobservice-server/deploy/config/deploy_shared_template.json --var '{ "environment": { "name": "dev'${GITHUB_USER_ID}'" } }' -o /builds/was-job-runtime/was-jobservice-server/launch_configs/deploy_shared_.json
$ ./bin/gen_config -c /builds/was-job-runtime/was-jobservice-server/deploy/config/deploy_jobservice_shared.json --var '{ "environment": { "name": "dev'${GITHUB_USER_ID}'", "version": "GET_NEXT" } }' -o /builds/was-job-runtime/was-jobservice-server/launch_configs/deploy_jobservice_.json
$
If you look carefully you'll notice each gen_config line is slightly different. The second one has an "environment version" defined (you'll also notice that this string is JSON, both the gen_config and deployer utilities can be passed strings of legal JSON to override any of the elements listed in the JSON config files). The gen_config utility takes a valid JSON structured file as input and treats it as a template. There a limited number of tokens which gen_config recognizes, GET_NEXT being the one to indicate that it should first query AWS to determine which ephemeral environents already exist, then "get the next one".  These version keys are the 26 letters of the alphabet. Therefore, you could possibly have 26 different jobservices running simultaneously in your "shared" environment.


Deploy the “pre-existing” environment:

$ ./bin/deployer create -v /builds/was-job-runtime/was-jobservice-server/launch_configs/deploy_shared_.json --debug


Deploy the "ephemeral" service environment:

$ ./bin/deployer create -v /builds/was-job-runtime/was-jobservice-server/launch_configs/deploy_jobservice_.json --debug
NOTE: You must always create the “pre-existing” environment first. Once it is up, you can create the service specific ephemeral environments. You can have as many of these as you want (well, up to 26 anyway :)

Destroying/Tearing down what you've built
In order to destroy the pre-existing environments, you need to first destroy all the service specific environments first. Therefore, you need to destroy them in reverse order. For example, to create you run:

$ ./bin/deployer create -v .../deploy_shared_.json
$ ./bin/deployer create -v .../deploy_jobservice_.json

To destroy, you’d do it in reverse:

$ ./bin/deployer destroy -v .../deploy_jobservice_.json
$ ./bin/deployer destroy -v .../deploy_shared_.json
 

Changing the environment configuration files
As mentioned earlier, each environment (both "pre-existing" and the "ephemeral" service-specific) has a basic configuration template file. These are stored in <service repo>/deploy/config/deploy_<descriptor>_.json (in a github pipeline, the last '_' is replaced with "${GITHUB_PIPELINE_ID}").  For example, the "shared environment" configuration template (located in: 

*deploy/config/deploy_shared_template.json*) looks like this:
{
    "tmpdir" : "/tmp/deployer_dir",
    "terraform" : "https://github-ci-token:API_TOKEN@github.com/veracode/was-core-infrastructure.git",
    "aws_region": "us-east-1",
    "owner": "Veracode terraform-deployer",
    "email": "dl-noreply@veracode.com",
    "group": "devops",
    "product": "deployer",
    "aws_profile": "aws-nonprod",
    "aws_key_name": "aws_pem_key",
    "route53_tld" : "terraform-deployer.veracode.github.io",
    "environment": {
      "name": "dev",
      "version": "a",
      "weight": 0
    },
    "project" : "deployer",
    "tags" : {
	"owner": "pllvc",
	"email": "dl-noreply@veracode.com",
	"group": "WAS"
    }
}
and the service template looks like this:

{
    "tmpdir" : "/tmp/deployer_dir",
    "terraform" : "/builds/widget?branch=test-2/deploy",
    "aws_region": "us-east-1",
    "aws_profile": "aws-nonprod",
    "aws_key_name": "aws_pem_key",
    "route53_tld" : "terraform-deployer.veracode.github.io",
    "environment": {
        "name": "dev",
        "version": "GET_NEXT",
        "weight": 0
    },
    "project": "widget",
    "staged_artifacts" : { },
    "service_version" : "1.1-1.x86_64",
    "puppet_version" : "latest",
    "jdk_version" : "8u40",
    "tags" : {
        "owner": "pllvc",
        "email": "dl-noreply@veracode.com",
        "group": "devops",
        "product": "widget",
        "system_type" : "widget",
        "Name" : "{{ config.tags['system_type'] }}-{{ config.tags['owner'] }}-{{ config.environment['name']}}-{{ config.environment['version'] }}"
    },
    "turn_monitor_on"          : 0,
    "use_elb_asg"              : 0,
    "widget" : {
    	"widget_min_elb_size"          : 1,
    	"widget_max_elb_size"          : 1,
    	"widget_min_elb_capacity"      : 1,
    	"widget_desired_capacity"      : 1,
    	"widget_capacity_timeout"      : "8m",
    	"widget_healthy_threshold"     : 2,
    	"widget_unhealthy_threshold"   : 2,
    	"widget_timeout"               : 3,
    	"widget_interval"              : 30,
    	"widget_elb-health-check"      : "HTTPS:8443/appstatus"
     }
}

In the first config, you'll notice a line like this:

    "terraform" : "https://github-ci-token:API_TOKEN@github.com/veracode/core-infrastructure.git",

When running the deployer, this is the line which tells the utility where the code repository exists for whatever the deployer is operating on.  In this example you'll also notice the use of API_TOKEN.  The deployer will extract this value from the environment variable and replace this token with it, thereby allowing the deployer to clone a repository different from the one which invoked the runner it is currently executing under.  See the terraform-deployer documentation for more detailed information about the variables contained in this file: https://github.com/veracode/terraform-deployer/deployer)
