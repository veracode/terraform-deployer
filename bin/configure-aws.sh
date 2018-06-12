#!/bin/sh

# declare default aws parameters for tests

mkdir ~/.aws

cat >~/.aws/config <<HERE
[default]
region = us-east-1
HERE

cat >~/.aws/credentials <<HERE
[default]
aws_access_key_id = $AWS_ACCESS_KEY_ID
aws_secret_access_key = $AWS_SECRET_ACCESS_KEY

[veracode-dynarch-nonprod]
aws_access_key_id = $AWS_ACCESS_KEY_ID
aws_secret_access_key = $AWS_SECRET_ACCESS_KEY

[veracode-random]
aws_access_key_id=XXXXXXXXXXXXXXXXXXXX
aws_secret_access_key=YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY    

HERE
