#!/bin/sh

# declare default aws parameters for tests

mkdir ~/.aws

CREDS="AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY"

PROFILE=$( "$CREDS" aws iam list-account-aliases --output text | awk '{print $2}')

cat >~/.aws/config <<HERE
[default]
region = us-east-1
HERE

cat >~/.aws/credentials <<HERE
[$PROFILE]
aws_access_key_id = $AWS_ACCESS_KEY_ID
aws_secret_access_key = $AWS_SECRET_ACCESS_KEY

[unit-test-random]
aws_access_key_id=XXXXXXXXXXXXXXXXXXXX
aws_secret_access_key=YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY    

HERE
