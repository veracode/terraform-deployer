# What is it?

The Veracode terraform-deployer is a generalized deployment engine to
assist in launching a pre-defined infrastructure into AWS.
Essentially, it is a python wrapper around [Terraform](https://terraform.io) code which defines your infrastructure.

The terraform code defining an infrastructure, however, is located in a separated repository and is, or should be, completely customizable to your project's needs. The deployer is completely agnostic as to what the infrastructure is, just that it's defined using Terraform.

# Official Source Location

The official Git Repo of this project is located here at: [GitHub](https://github.com/veracode/terraform-deployer), because that's where Veracode graciously allowed me to release this code as Open Source.  I have since forked that repository here to [GitLab](https://gitlab.com/seek-and-deploy/terraform-deployer) because of GitLab's superior (in my opinion) development environment, including pipelines (all of which, ironically, I came to know and love while still at Veracode!)

Should Veracode ever decide to open up a Gitlab.com presence for their Open Source projects, I'll gladly move this under their auspices.  For now, my main development takes place here, and when I release anything new, it will be pushed over to GitHub as well to ensure that location is up to date.

# Deployment Requirements

1. A set of AWS credentials
   - For any AWS account in which you intend to have the deployer operate, you must have a set of AWS API credentials in your ~/.aws/credentials file for the deployer to use. The name of the profile listed in the credentials file must match the value assigned to aws_profile variable set in the JSON config file passed to the deployer at run time. For example, if the JSON config file for the deployer contains:

        {
		    "aws_profile": "aws-nonprod",
	        ...
        }

    Then the ~/.aws/credentials file must contain a section like this:

        [aws-nonprod]
		aws_access_key_id=XXXXXXXXXXXXXXXXXXXX
		aws_secret_access_key=YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY
2. [Pip](https://pip.pypa.io/en/latest/).
	- If you have Python 2.7.9, Pip will already be installed. Otherwise install Pip [using an OS Package Manager](https://pip.pypa.io/en/latest/installing.html#using-os-package-managers) or by [using a Python script](https://pip.pypa.io/en/latest/installing.html#install-pip)
3. [Terraform from Hashicorp](https://hashicorp.com/blog/terraform.html).
	- NOTE: Curretly, we have only tested with TERRAFORM 0.10.6. There are no version dependencies in this code and there is no reason why this should not work with any version of Terraform, but we have not tested with newer versions.  But be aware that the sample-infrastructure code may need to be updated for newer versions or features.

	- NOTE: The instructions below have been tested on Mac OSX and Linux. Your mileage may vary on Windows, and we have not tested it there. Theoretically, with a good Cygwin install, it should work. Caveat Emptor and all that.

# Deployment Instructions
### Running from a Docker Container

The Veracode terraform-deployer project maintains a docker image with the deployer already installed along with all of its pre-requisites.  The name of the docker container is: Veracode terraform-deployer/deployer and be eventually be found at Docker Hub.

### Prerequisites
- Python v2.7.x
- Git
- AWS Credentials

### Installation
- Clone the git repo locally.
- From the deployer directory, run:
```
    $ python setup.py install
```
or:
```
    $ make install
```
(NOTE: This assumes you have Make installed)

### Create an environment

The Veracode terraform-deployer deployer tool can be used to create a fully functional environment in AWS when coupled with a pre-defined infrastructure and applications which have been properly configured to be deployed in conjunction with that infrastructure.

Creating a new environment is run by a simple command. Please see the examples under deployer/conf/default.json for variable files to pass. The JSON launch configurations are used to override the standard variables stored in sample-infrastructure project's variables.tf file.

Variables.tf is targeted to be the default (production) values set, with a minimal set of values entered into deployer/conf/example_config.json. The launch config JSON file MUST contain at least the environment name and the required sets of tag variables (email, group, product, project, etc.)

In order to create a new scan environment, simply execute:

    $ bin/deployer create -v <path to var file>

There are critical components required in the varfile JSON that needs to exist. An example is below of the required fields:

    {
       "aws_region": "us-east-1",
       "owner": "Veracode terraform-deployer",
       "email": "dl-noreply@veracode.com",
       "group": "devops",
       "product": "deployer",
       "aws_profile": "aws-nonprod",
       "aws_key_name": "aws_pem_key",
       "route53_tld" : "deployer.terraform-deployer.veracode.io",
       "environment": {
         "name": "dev",
         "version": "a",
         "weight": 0
       },
       "project" : "deployer",
     }

Note the environment "version". The deployer assumes a canary deployment structure. If an environment named "production" with version "a" is deployed, then it will generate the environment with naming conventions in AWS "production-a". When you desire to upgrade your environment, you would re-run the deployer create command, but with the environment version set to "b", and so on.  Environements are designed to be ephemeral and disposable. You can not create two environments with the same name. In other words, if "coral-a" exists, you can not create "coral-a" again. You must destroy it, then re-create it.

### Delete an environment

If you created an environment for testing and need to tear down the environment, simply execute the following. The environment name is the environment_name variable defined in your varfile. This must be unique per deployment

    $ deployer destroy -v <path to var file>


# Development Instructions

To prevent installing the deployer to a development system, and allow for changes to be quickly tested, follow these instructions instead of the deployment instructions. Once the steps below are completed, you will be able to run the deployer commands for create, update, delete, etc.

### Create a Virtual Environment

Create a Python Virtual Environment for this project. This will let you keep the project's Python modules separate from your system's Python modules, [more details here](https://virtualenv.pypa.io/en/latest/#introduction).

    $ mkdir ~/.virtualenvs
    $ mkvirtualenv deployer

### Activate your newly created virtual environment

    $ workon deployer

You should now see ```(deployer)``` in your command prompt.

### Install all Python modules required for development.

    $ cd <your-cloned-repository-location>
    $ pip install -r requirements.txt

Run Tox to make sure all tests pass.

    $ tox



# The Config File
There are sample JSON config files located in the deployer project under `deployer/deployer/conf`. The actual config file used with the deployer can live anywhere, and is specified as a path with the the `-v` at run-time.  The only settings required in the config file are those variables which must be passed through to terraform itelf and which the deployer can not figure out on its own dynamically or via reasonable defaults. Required variables are enforced with a config schema located in `deployer/deployer/conf/default_schema.json`.

The `config.json` is read by the deployer into a dict called `config[]`. This dict is then updated with various "defaults" assuming that variable isn't already specified in the config file. If the deployer finds a variable it cares about already defined, it leaves that value alone. In otherwords, variables defined in the `config.json` override any defaults which the deployer might set on its own.

To summarize:
* Any of the "config['foo']" variables mentioned below can be defined or over*ridden in the `config.json` file.
* Any variable labeled `REQUIRED` must be defined there.
* `REQUIRED` variables are enforced by `default_schema.json`
* Any variable not labeled `REQUIRED` will default to something reasonable and can be over-ridden by defining it.

## Environment Variables Affecting Deployer Behavior

* **os.environ['AWS_DEFAULT_PROFILE']** and **os.environ['AWS_PROFILE']**
  * cleared out, then set from *config['aws_profile']*.

* **os.environ['AWS_DEFAULT_REGION']**
  * cleared out and set from *config['aws_region']*

* **os.environ['API_TOKEN']**
  used for string replacement to allow git to clone a repository using an API_TOKEN. sets *config['API_TOKEN']*.


## Required Deployer Variables
The following variables are currently required  by the deployer to be set in the config.json file. This is enforced by the default_schema.json file in the `deployer/deployer/conf/` directory.

* *config['aws_profile']**
  * REQUIRED
  * defines the account name/profile to look up in the ~/.aws/credentials file.

* **config['aws_region']**
  * REQUIRED
  * defines which region to operate on/in.

* **config['environment']['name']**
	* REQUIRED
	* basic environment name. i.e. dev, qa, prod, etc.
	* used in tags and names.

* **config['environment']['version']**
  * REQUIRED
  * single letter to differentiate between versions of an environment.
  * used in tags and names.

* **config['project']**
  * REQUIRED
  * short name of the project. e.g. 'dynarch', 'onewas', 'twowas', etc.
  * used in tag values and name strings

* **config['route53_tld']**
  * REQUIRED
  * used to determine config['public_zone_id']

* **config['staged_artifacts']**
  * REQUIRED
  * defines a hash map of `s3://project_config/<path to artifact>` to `<staged_artifacts/local_artifacts_to_upload`
  * (this is likely backwards, and probably should be REQUIRED

* **config['terraform']**
  * REQUIRED
  * location deployer should find terraform infrastructure code at.
  * may be a relative or canonical local path to where terraform code exists, or a git URL to check the code out from.
  * A git repository branch may be specified by appending the string "?branch=<branch name>" to the end of the repository URL. For example:

  "git@github.com:veracode/terraform-sample-infrastructure.git?branch=master",

(NOTE: That repository doesn't actually exist yet).

  This tells the deployer to clone the 'master' branch of this repository.  The string 'master' can be replaced with any branch name and the deployer will clone the repository and checkout that branch prior to running terraform on that code.
  * An API TOKEN can be used used to allow the deployer to clone non-public repositories if:
  * A URL for the terraform location similar to this is used:
	"https://github-ci-token:API_TOKEN@github.com:/veracode/terraform-deployer/sample-infrastructure.git"
  * An environment variable API_TOKEN is defined within the gitlab Pipelines section.
  * If these two conditions are met, the deployer will replace the string API_TOKEN with a pre-defined environment variable *${API_TOKEN}*. The deployer does this directly in the python code (in aws.py) using string substitution on the value of *config['terraform']* if it finds the string *API_TOKEN* in that URL.


## Derived Default Variables set by the Deployer at Run-Time
These variables are used directly in the deployer code and are derived or defaulted to "reasonable defaults".

* **config['API_TOKEN']**
  * set from os.environ['API_TOKEN']
  * written out to the vars.tf file and passed to terraform
  * (despite terraform not being able to use it).

* **config['account_id']**
  * the AWS account ID for the account defined by *config['aws_profile']*.
  * set by boto call to AWS API.
  * used to create unique bucket names prefixed with the account number.

* **config['availability_zones']**
  * set by boto call, passed to terraform

* **config['env_folder']**
  * defaults to *config['env_name']*
  * used environment-specific S3 bucket
  * not used currently. "seemed like a good idea at the time".

* **config['env_name']**
  * defaults to `<config['environment']['name']>-<config['environment']['version']>`
  * passed to terraform as identifier string in AWS object names.

* **config['project_config']**
  * Defaults to "<account_id>-<project>"
  * S3 bucket name.
  * place to find/store artifacts

* **config['public_zone_id']**
  * Derived from *config['route53_tld']*
  * Passed to terraform to use in creating delegation sets.

* **config['tf_root']**
  * path to location of checked out terraform code.
  * derived from combining *config['tmpdir']* with directory where deployer cloned terraform code to.

* **config['tf_state']**
  * name of terraform state file
  * defaults to <env_name>.tfstate

* **config['tf_state_bucket']**
  * name of S3 bucket to store state files in.
  * defaults to `<account id>-<project>-tfstate`

* **config['tfvars']**
  * location of variables file to pass to terraform
  * defaults to `<tmp_dir>/vars.tf`

* **config['tmpdir']**
  * location of where to check repositories out to.
  * defaults to */tmp/<randomized UUID string>*

## Terraform Pass-Through Variables

Any variable your terraform code requires being set should be defined in the `config.json` file. By default, the following are required:

* aws_key_name
* aws_profile
* aws_region
* email
* group
* owner
* product

However, these variables must also be definted somewhere, since they are referenced by the terraform code as well. Technically, this means they are "required" variables, but they may not be found in the `config.json` file, since some are set to reasonable defaults by the deployer itself.

* project_config : required, but set by the deployer
* route53_tld    : required because terraform references it
* tmpdir         : required, but set by the deployer

Additionally, there may be variables you want to pass through to terraform which in turn merely passes the value through to something like an ec2 cloud-init script via user_data. Examples of those can be seen here:

* sjm_version
* verajdk_version
* verapuppet_version

All three of there are merely passed through to the launch-config of an ec2 instance via the user-data cloud-init script that gets run at boot time.
