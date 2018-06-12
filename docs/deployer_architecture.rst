What is the Deployer?
The Deployer itself is nothing more than a python-based wrapper around Terraform. The purpose of this wrapper is isolate the basic infrastructure a team designs in Terraform from the logic required to deploy that infrastructure. What exactly does that mean? Let's take a step back and look first at what Terraform does and doesn't do well.

Terraform is a essentially declarative domain specific language which allows you to define your cloud-based architecture in a programming language like syntax. However, the down side of this is there there are not conditionals, looping constructs, variables, or any of the niceties we're used to with a normal programming syntax.  There is minimal support for things like arrays and hashes (what python calls dicts), one can approximate looping with a minor, but clever hack, and can approximate a rudimentary conditional by assuming a particular variable is a binary value and combining it with the loop-approximating hack.  But just from that description alone, you should be able to figure out these things are best not done to begin with.

The short of it is, Terraform is really good at one specific thing: providing a fairly decent DSL in which to describe the infrastructure you want to create. It is not really good at anything else. And for this reason, we need a wrapper around running terraform.

So, what sorts of things does the deployer wrapper take care of that Terraform doesn't?  Mostly taking care of all the variables associated with deploying a thing to an environment where the environment and it's characteristics are changeable and dependent upon context. For example, you might have multiple "environments" which you need to deploy your code to. Often times these are loosely defined as: Development, QA, Stage, and Production.

Each of the above named environments has a different use-case, and with it, certain characteristics which differ from the others. Some quick examples being: Name, Location (i.e. the AWS account in which it exists), IP Addressing, subnet allocation, data allowed in the environment, data allowed to leave the environment, etc. As a result, we need to be able to tell terraform what the values of all these variables are before running so terraform can do it's thing properly. We could specify all these things on the command line to, or we could create entirely different sets of identical code for each environment. But those both have obvious drawbacks. Hence the need for a wrapper.

What goes in the wrapper, what goes into Terraform?
In short, it's pretty simple, and can be answered with one of two questions:

Is it static, common to all environments, and will probably not change regardless which environment you're dealing with?
If so, it goes in Terraform. Declare it part of the infrastructure and just be done with it.
If not, put it in the deployer code wrapped in sufficient logic to result in whatever variable declarations are required to allow Terraform to just do its thing.
Is it highly variable, dynamic, subject to change between environments, or dynamically discernible in a programmatic manner?
If so, put it in the deployer code wrapped in sufficient logic to result in whatever variable declarations are required to allow Terraform to just do its thing.
If not, it goes in Terraform. Declare it part of the infrastructure and just be done with it.
Why a combination of Boto3 + Terraform?
Boto3 is fantastic, and it's used heavily within the deployer code itself. Why not boto3 exclusively? Terraform offers a very simple DSL in which it's extremely quick and efficient to define a fairly complex architecture and the various interdependencies in that architecture. It also has an unparalleled acyclic graph-based dependency resolution engine built into it that allows you to define your architecture without having to worry about orders of operation. Building a deployer in Boto3 exclusively would require us to deal with ordering problems. The result of this would be code which was fairly inflexible since we'd have to tightly couple our infrastructure design with our business logic code. This would lead to essentially a deployer designed for a very specific project which could not easily adapt to other people's needs.  For example, consider three different projects:

Project A uses a VPC, 6 subnets, a NAT gateway, and lots of ec2 instances behind ASGs behind ELBs.

Project B uses a similar setup, but instead of ec2 instances, they use ecs and lots of Docker instances.

Project C makes use of Lambdas, SNS, SQS, a back-end RDS database, and a bunch of S3 buckets.

Defining each of those environments in python with Boto3 would essentially mean each project would have to write very specific code for their infrastructure which deals with not only the architecture definition itself, but the order in which the pieces of the infrastructure are instantiated and how they are interlinked.  While it is certainly possible to write modular code to achieve such the goal of creating a very generic deployer useable across all of these projects, it requires a lot of forethought given specifically to the idea of a generalized deployment mechanism with modular code.

Which is exactly what we've done, and why we've chosen to use Terraform. This split has allowed us to split the concepts of deployment of a thing apart from the thing being deployed.  In short, we declare "the thing to be deployed" as a completely separate, external, and independent entity from the deployer itself.  The deployer then merely needs to provide "the thing to be deployed" with the correct information such that when built, it exists in the right time and place in its correct form for that time and place.  This allows us to concentrate in the deployer merely on the actions required to deploy a thing, regardless of what that thing actually is. As seen from the hypothetical projects above, that thing could a VPC, a Lambda, a Docker instance, etc.  The project using the deployer now only needs to declare whatever infrastructure they wish to use and define it in the context of Terraform's DSL letting Terraform deal with dependency resolution and order of operations and the deployer deal with providing terraform the correct information. Meanwhile, they can get back to writing their own code for whatever widget they're writing to change the world with!

How is the Deployer Code Organized?
The deployer is a normal python package structure. It could, if you wanted to, be installed via pip, though that is not necessary to use it. It can be run directly from the source tree itself.

Entry point
The main entry point for the deployer is in 'bin/deployer'. This code really does nothing more than evaluate the command line arguments and carry out the correct arguments based on the user supplied options. The entry point is also responsible for loading the configuration files and validating them.  The following steps are carried out by the deployer in the order presented:

Process and evaluate the command line arguments.
Load the environment configuration file into a python dictionary.
Validate that the configuration file meets the expected requirements dictated by the validation schema.
Use the configuration file to establish the correct working environment for running AWS comands via both boto3 and Terraform.
If --bootstrap was specified, bootstrab the AWS account by creating the proper S3 buckets and folders
Run through the pre-flight checks to ensure the environment and configuration is ready to run Terraform.
Validate that the configuration dictionary has all the required elements to run Terraform.
Write out the Terraform configuration.
Download any pre-staged artifacts Terraform needs to launch into AWS if necessary.
Sync the Terraform code to the working directory.
Run Terraform.
Teardown the working directory.
Configuration
The deployer is configured using a JSON-based config file located in the deployer/conf directory. There is a minimum set of configuration options which are required and enforced using a matching JSONSchema validation file.  If you want to change the required configuration options, you must also change the validation schema file as well.

You can have as many configuration files as you desire. We recommend at least one per environment per project. But be aware, that the definition of "environment" is arbitrary. There is nothing locking you into any pre-defined environment names. This means each person on your team can launch entirely separate, isolated, and disposable environments simply by selecting a unique string to insert in the environment['name'] field like this:

  "environment": {
    "name": "dev",
    "version": "a",
    "weight": 0
  },
differs from:

  "environment": {
    "name": "plltest",
    "version": "a",
    "weight": 0
  },

These configuration files will create entirely separate unique environments right down to the VPC level, including IAM roles & policies, e

WARNING: Two users using the same string to define their environment['name'] field will collide with each if they are both executing the deployer against the same AWS account. For example, two users in veracode-random-nonprod must select different environment names or risk colliding. Two users in separate accounts, for example, veracode-random-nonprod and veracode-nonrandom-prod  will not collide should they select the same environment names. It should also be obvious that there is nothing which restricts any given environment name to any given account name.

Modules
deployer/
The subdirectory deployer/ contains the bulk of the deployer code. These are normal python modules. They are NOT python Classes, as the deployer (at the current time) is not written in an object oriented manner; it is simply straightforward procedural python.

deployer
|-- aws.py
|-- bootstrap.py
|-- environments.py
|-- exceptions.py
|-- __init__.py
|-- preflight.py
|-- route53.py
|-- s3.py
|-- terraform.py
|-- utils.py
|-- _version.py
aws.py
Contains code to establish the correct environment for boto3 and Terraform to operate within a given AWS account structure. Sets things up like which AWS account to use, which S3 buckets to create or access, what the name of the environment specific folder is, what environment name to use for tagging and creation, and name-length validation checks.  Most of the functions in this module merely return the output of a single boto3 call to be used elsewhere in the code.

bootstrap.py
Creates S3 buckets and uploads artifacts to S3 so AWS objects can access them, and so future runs of the deployer can download them for Terraform to access.
(Yes, this is silly. We need to place things up into S3 so that we can turn around and download them just so we can upload them via Terraform. This is sadly a limitation of Terraform in that it can't pull things out of S3 in order to launch them into other AWS services.)

environments.py
This is where we create and destroy things (and eventually promote/demote). This is where we actually issue the Terraform commands to run.

exceptions.py
Pretty much all it sounds like. A class (yes, the one OO module) entirely devoted to customized exceptions.

preflight.py
Preflight does a number of things:

Setup/teardown
Sets up a bunch of variables, establishes the working directory area, creates an environment-specific folder in the S3 bucket, configures the DNS domain to be used. Then reverses all this for teardown().
Write the Terraform configuration file out to disk.
Download artifacts staged in S3 if necessary.
Sync the Terraform code to the working directory.
route53.py
Currently has a single function to return the AWS Zone ID of a named zone.

s3.py
A bunch of utility functions wrapping boto3 calls to create and destroy buckets, folders, and objects, or return bucket names.

terraform.py
Mostly functions to return the correct Terraform command to run.

utils.py

Utility functions to load config files or validation schemas, and run validations or shell commands (i.e. terraform).

tests/
In the tests/ subdirectory is a mock class used for testing. This class mocks out a few of the Boto3 calls used in the code so we can inject canned responses against which we can test the return values from the functions when they're called.

tests/test_data contains some canned configuration data used by the unit tests.

tests/unit contains unit tests for the vast majority of the code in deployer/*.py.

How is the Terraform Code Organized?
Basic Directory Structure Layout
The basic layout of the terraform code is fairly straightforward and entirely customizable to your project's need. The default structure looks like this:

.
|-- common_vars.tf
|-- main.tf
|-- main_vars.tf
|-- vpc
|   |- common_vars.tf -> ../common_vars.tf
|   |- nat.tf
|   |- private-nets.tf
|   |- private_routes.tf
|   |- public-nets.tf
|   |- public_routes.tf
|   |- scratch.tf
|   |- security_groups.tf
|   |- variables.tf
|   |- vpc.tf
|-- ec2
|   |- common_vars.tf -> ../common_vars.tf
|   |- ec2.tf
|   |- ec2_vars.tf
|-- iam
|   |- common_vars.tf -> ../common_vars.tf
|   |- enc_keys.tf
|   |- groups.tf
|   |- policies.tf
|   |- roles.tf
|   |- users.tf
|-- jumphost
|   |- common_vars.tf -> ../common_vars.tf
|   |- jumphost.tf
|   |- jumphost_iam.tf
|   |- jumphost_route53.tf
|   |- jumphost_vars.tf
|-- lambda
|   |- common_vars.tf -> ../common_vars.tf
|   |- consul.tf
|-- route53
|   |- common_vars.tf -> ../common_vars.tf
|   |- route53.tf
|   |- route53_private_zone.tf
|   |- route53_public_zone.tf
|   |- route53_vars.tf
|-- s3
|   |- common_vars.tf -> ../common_vars.tf
|   |- s3.tf
|   |- s3_variables.tf
|-- apps.tf
Terraform Entry Points and Variable Files
Let's break this down. The main entry point for terraform are the .tf files in the top-level directory.  

|-- main.tf
|-- main_vars.tf
|-- common_vars.tf
|-- apps.tf
Of these files, two of them contain nothing but variable definitions. The other two define the infrastructure as a whole. Let's start with main.tf:

# -*- terrarform -*-
provider "aws" {
  region                = "us-east-1"
  profile               = "${var.aws_profile}"
}

module "vpc" {
  source                = "./vpc"
  aws_profile           = "${var.aws_profile}"
  owner                 = "${var.owner}"
  group                 = "${var.group}"
  email                 = "${var.email}"
  product               = "${var.product}"
  aws_key_name          = "${var.aws_key_name}"
  env_name              = "${var.env_name}"
  availability_zones    = "${var.availability_zones}"
}
...
main.tf: sets up the AWS provider, then defines a bunch of modules passing each one a bunch of variables. Each directory listed above is a separate terraform module, meaning the code contained in there is essentially independent from all the other code. This allows us a great degree of freedom and flexibility. It also allows us to keep our files small and fairly readable.

common_vars.tf: Any variable which needs to be passed to all the various sub-directory modules is defined in common_vars.tf, which is then symlinked back from each module's sub-directory. This means that if the variable exists in this file, it must be passed into the module as shown above in the 'module "vpc" {}' example snippet.  Anything not common to all sub-modules must be defined in main_vars.tf and the individual sub-module's 'module_vars.tf' file.

main_vars.tf: defines all variables unique to any single module or at least not common to all modules. These variables also need to be defined in the receiving module's module_vars.tf as well.

module "route53" {
...
  public_zone_id        = "${var.public_zone_id}"
  route53_tld           = "${var.route53_tld}"
}


main_vars.tf:
variable "route53_tld"    { }
variable "public_zone_id" { }


route53/route53_vars.tf:
# -*- puppet -*-
variable "vpc_id"         { }
variable "route53_tld"    { }
variable "public_zone_id" { }
For example, consider the above where main.tf needs to pass the variables 'public_zone_id' and 'route53_tld' into the route53 module.  Since these variables are not common to all modules, we can't define them in common_vars.tf unless we also want to pass them into all modules.Terraform will fail otherwise since we've defined variables exist, but they aren't assigned any values. Therefore, we define them in main_vars.tf and in route53/route53_vars.tf and then we can safely pass them in via the module clause.

Module Subdirectory Layout
The subdirectories for the modules can, in their simplest form, consist of a single file defining all the variables and code for that module. However, in the default case, we've broken the module code out into at least 2 files:

module.tf which defines the code for that particuler piece of infrastructure
module_vars.tf which defines all the module specific variables required to build this piece of infrastructure not being passed in from main.tf
You can, as is shown above in the vpc/ module, break things down even further. The basic configuration for a VPC has a lot of moving parts, so we break each piece into a separate file. Think of it in terms of the AWS console.  The directory structure is equivalent to an AWS service, and the files inside are the left-side column sub-sections available for configuring that service.  This isn't written in stone, and as shown in the VPC module, we've broken subnets down even further into 'public' and 'private'. Everything here is entirely up to your discretion. We've broken things down to enhance organization and readability according to our own preferences. You are encouraged to do the same!
