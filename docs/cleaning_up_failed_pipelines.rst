NOTE: This documentation currently only pertains to running in GitLab pipelines. It will eventually be cleaned up and re-written once we figure out GitHub equivalent process.

Cleaning up after failed pipeline is no different than running the deployer in 'destroy' mode as explained in the directions for Deploy from your desktop. The only difference being, you may need to fiddle with things a bit more.  But really, it's exactly the same process.  Therefore, assuming some pipeline has created an environment which it has failed to clean up, and you now must do so yourself, here are the steps to do so. We will also assume that you have followed the steps to Deploy from your desktop and therefore, have all the necessary source code repositories checked out to the proper locations on your desktop syste,


Creating the necessary config files.

This can be done in a couple of different ways.

You can hand-craft the config files
You can run gen_config against the templates stored in the code repository under "deploy/config"
Or copy and paste from the failed pipeline. 
Really, it doesn't matter which route you choose. The most important part is that the environment name and version match that which you are trying to destroy. The easiest route (unless you've already created configs via gen_config following the directions for setting up the mock Gitlab runner scenario) is to just copy the configs output during the failed pipeline's deploy-env phase. Those configs look something like this:

Git Lab user ID: 199
{
    "tmpdir" : "/tmp/deployer_dir",
    "terraform" : "https://github-ci-token:API_TOKEN@github.com/veracode/core-infrastructure.git",
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
{
    "tmpdir" : "/tmp/deployer_dir",
    "terraform" : "/builds/widget?branch=test-2//deploy",
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
 
You'll notice there are actually two different config files there. The first one is for the shared environment, and the second for the service-specific environment. You need to copy these to separate files on your desktop. The names of these files don’t matter. 

Clearing out local Terraform State
Since you've previously followed the directions for Deploy from your desktop, and probably the subsection on mock runners, you should clear out any of the terrafrom residue from previous deployer runs. This residue consists of the .terraform/ subdirectory and any terraform.tfstate* files which the deployer may have left behind. 

    $ cd /builds/widget/deploy
    $ rm -rf .terraform/ terraform.tfstate*

If you wanted to be overly paranoid, you could do this instead:

    $ cd /builds
    $ find . -name \*terraform\* | xargs rm -rf

The first example will remove only the .terraform  directory structure and terraform.tfstate* files located with in the deploy/ subdirectory of the was-jobservice-server  tree. The second will remove all .terraform subdirectories and terraform.tfstate* files down the entire /builds hierarchy.

Resurrecting the S3 state file
It is possible you might have to restore the S3-based state file. In order to do so, log into the S3 console, if there is no dev<your gitlab UID>-<env version>.tfstate file, click on the “Show” icon. This will show you all the deleted versions.

Save the most recent non-empty file (it will be at least 40KB, the ones that show as 573.0B, are essentially empty and useless) to your desktop. In the example image above, we'd want the 41.1KB version from Dec 11, 2017 11:33:22 AM GMT-0500 (assuming our Gitlab UID was 199). Once that's saved to your desktop, simply re-upload it to the s3 bucket like this:

    $ aws s3 cp ./dev<your gitlab UID>-<env version>.tfstate s3://<tfstate bucket>/dev<your gitlab UID>-<env version>.tfstate

Using the file listed above, and assuming it was saved as dev199-a.tfstate in the current working directory, we'd just use the AWS CLI to copy it back to S3:

    $ aws s3 cp ./dev199-a.tfstate s3://<tfstate bucket>/dev199-a.tfstate

This is necessary because the file you downloaded from S3 is a older version. The S3 file was deleted. This is essentially a backup being restored from version control. By copying the deleted version to our desktop and copying it back to S3, we are making the old version the latest, most recent copy. In essence, you're undeleting the file so the deployer can find it again.

Note: the example explained here used an ephemeral environment state file. It is entirely possible you  might need to restore both the ephemeral and the pre-existing environment in order for things to work correctly. And, you may have to play the file-restore game more than once before you're finally able to get the deployer to run correctly and properly tear down all of the environment. Be patient, make sure you read, understand, and follow these directions, and eventually it should run to completion, cleaning up all the remnants of the failed pipeline.

Running the deployer in destroy mode
 

After both the tfstate file has been restored in s3 and the local state has been destroyed, you should be able to run the deployer against your copied config files and have it destroy the existing environment.

 

    $ deployer destroy -v /tmp/service.json
    ...
    $ deployer destroy -v /tmp/shared.json

Note: You must destroy the service-based ephemeral environment first. Attempting to destroy the pre-existing, non-ephemeral environment before the ephemeral will fail because of live dependencies. For example, you can't destroy a subnet if there's an ec2 instance still running. Destroying the pre-existing first will result in a paritially populated tfstate file for the pre-existing environment. This in turn, will result in the ephemeral environment also likely having problems when you attempt to destroy it. Should this happen, follow the directions above in the Resurrecting the S3 State File section and resurrect both the dev<your gitlab uid>.tfstate and the dev<your gitlab uid>-<version>.tfstate files, and re-run the deployer with the destroy command in the correct order again.

 
