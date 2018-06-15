Introduction
The default Terraform architecture is setup in the form of a parent directory structure containing several sub-directories, each of which is set up as a Terraform module, and a two variable files. One variable file is common to all the sub-directories and is sym-linked from each sub-directory back to the parent directory. The other variable file contains those variables which are specific only to the top-level or might need to be passed into a sub-set of the other modules. In other words, they're variables not common to all modules.

terraform-deployer/sample-infrastructure
|-- apps.tf
|-- common_vars.tf
|-- ec2
|   |-- common_vars.tf -> ../common_vars.tf
|   |-- ec2.tf
|   `-- ec2_vars.tf
|-- iam
|   |-- common_vars.tf -> ../common_vars.tf
|   |-- enc_keys.tf
|   |-- groups.tf
|   |-- policies.tf
|   |-- roles.tf
|   `-- users.tf
|-- jumphost
|   |-- common_vars.tf -> ../common_vars.tf
|   |-- jumphost_iam.tf
|   |-- jumphost_route53.tf
|   |-- jumphost.tf
|   `-- jumphost_vars.tf
|-- lambda
|   |-- common_vars.tf -> ../common_vars.tf
|   `-- consul.tf
|-- main.tf
|-- main_vars.tf
|-- output.tf
|-- README.md
|-- route53
|   |-- common_vars.tf -> ../common_vars.tf
|   |-- route53_private_zone.tf
|   |-- route53_public_zone.tf
|   |-- route53.tf
|   `-- route53_vars.tf
|-- s3
|   |-- common_vars.tf -> ../common_vars.tf
|   |-- s3.tf
|   `-- s3_variables.tf
`-- vpc
    |-- common_vars.tf -> ../common_vars.tf
    |-- nat.tf
    |-- private-nets.tf
    |-- private_routes.tf
    |-- public-nets.tf
    |-- public_routes.tf
    |-- scratch.tf
    |-- security_groups.tf
    |-- variables.tf
    `-- vpc.tf

This structure is presented as an example. It works as is, but is designed to be completely module to fit your own needs and allow you the complete freedom to change this code around to suit your own needs.

Modules

Each directory is designed as separate Terraform module to enhance flexibility.  For example, if you wanted to design your VPC differently, or, if your infrastructure didn't actually use a VPC (maybe you're using nothing but S3, Route53, API Gateways, and Lambdas!), you could simply edit the main.tf and comment out this clause:

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

Voila! Suddenly your infrastructure is built without a VPC. You will of course have to deal with the fallout of this change, since the existing sample-infrastructure code has things which depend upon the VPC existing, e.g. the jumphost, ec2, and the sample-java-microservice modules.  But you get the idea.

Variables
If you open the main.tf you'll note that each module is passed a list of variables.  All of these variables must be declared somewhere. Currently they are declared in several places:

common_vars.tf - Variables common to all modules. (Despite being common, terraform still requires they be passed in.)
main_vars.tf - Variables which are not common to all modules. They may be common to several. In which case, you could create a not_so_common_vars.tf and link those variable definitions into just those modules.
<module-name>/<module-name>_vars.tf - variables defined for this specific module. These variables may have reasonable defaults set specific to that module, but they could also be over-ridden by passing new values in from main.tf.
 
