# -*- coding: utf-8 -*-
#
# Copyright Veracode Inc., 2014

import boto3
import botocore
import logging
import os

import deployer.aws

logger = logging.getLogger(os.path.basename('deployer'))


def get_bucket_name(config, bucket_suffix=None):
    """
    Return a bucket name of the form: ${account_id}-${project}-${suffix}

    Args:
        config: dictionary containing all variable settings required
                to run terraform with.

        bucket_suffix: string to add to the returned bucket name.

    Returns:
        bucket_name: string representing the name of a bucket.
    """
    bucket_prefix = "{}-{}".format(config.get('account_id',
                                              deployer.aws.get_account_id()),
                                   config['project'])
    bucket_name = bucket_prefix
    if bucket_suffix:
        bucket_name = "{}-{}".format(bucket_prefix, bucket_suffix)

    return bucket_name


def get_env_bucket_name(config, bucket_suffix=None):
    """
    Return an environment-specific bucket name of the form:
    ${bucket_name}-${env}

    Args:
        config: dictionary containing all variable settings required
                to run terraform with

        bucket_suffix: string to add to the returned bucket name.

    Returns:
        bucket_name: string representing the name of a bucket.
    """

    suffix = "{}".format(config['env_name'])
    if bucket_suffix:
        suffix = "{}-{}".format(suffix, bucket_suffix)
    return get_bucket_name(config, suffix)


def create_bucket(bucket_name):
    """
    Create specified bucket name.

    Args:
        bucket_name: string representing the name of a bucket.

    Returns :
        nothing

    Raises:
        botocore.exceptions.ClientError if bucket already exists.
    """
    s3 = boto3.client('s3')
    try:
        s3.create_bucket(Bucket=bucket_name)
    except botocore.exceptions.ClientError as e:
        if not e.response.get('Error', {}).get('Code') == "BucketAlreadyExists":
            logger.error("{}".format(e.message))
            raise
    return


def destroy_bucket(bucket_name):
    """
    Destroys specified bucket name.

    Args:
        bucket_name: string representing a bucket name.

    Returns:
        nothing.

    Raises:
        botocore.exceptions.ClientError if bucket already exists.
    """
    s3 = boto3.client('s3')
    try:
        s3.delete_bucket(Bucket=bucket_name)
    except botocore.exceptions.ClientError as e:
        if not e.response.get('Error', {}).get('Code') == "BucketAlreadyExists":
            logger.error("{}".format(e.message))
            raise
    return


def create_folder(bucket, key):
    """
    Creates a subfolder of value KEY in bucket BUCKET.

    Args:
        bucket: string representing a bucket name
        key   : string representing a folder name

    Returns:
        nothing

    Raises:
        botocore.exceptions.ClientError if folder already exists.
    """
    key = key if key.endswith('/') else "{}/".format(key)
    try:
        boto3.client('s3').put_object(Bucket=bucket, Key=key)
    except botocore.exceptions.ClientError as e:
        if not e.response.get('Error', {}).get('Code') == "BucketAlreadyExists":
            logger.error("{}".format(e.message))
            raise
    return


def destroy_folder(bucket, folder):
    """
    Destroys a subfolder of value KEY in bucket BUCKET.

    Args:
        bucket: string representing a bucket name
        key   : string representing a folder name

    Returns:
        nothing
    """
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket)
    delete_recursively(bucket, folder, s3)

    return


def delete_recursively(bucket, folder, s3):
    """
    Destroys (recursively) a subfolder of value KEY in bucket BUCKET.

    Args:
        bucket: string representing a bucket name
        key   : string representing a folder name
        s3    : s3 boto object

    Returns:
        nothing
    """

    for obj in bucket.objects.filter(Prefix=folder + "/"):
        try:
            s3.Object(bucket.name, obj.key).delete()
        except:
            delete_recursively(bucket, obj.key, s3)
    return


def object_exists(bucket, key):
    """
    Determine if object KEY exists in specified bucket BUCKET.

    Args:
        bucket: string representing a bucket name
        key   : string representing a folder name

    Returns:
      True on success
      False if object does not exists

    Raises:
        botocore.exceptions.ClientError if bucket does not exist.
    """
    s3 = boto3.resource('s3')
    try:
        bucket = s3.Bucket(bucket)
        objs = list(bucket.objects.filter(Prefix=key))
    except botocore.exceptions.ClientError as e:
        if ( e.response.get('Error', {}).get('Code') == "NoSuchBucket" or
             e.response.get('Error', {}).get('Code') == "NoSuchKey"):
            return False
    
    if len(objs) > 0 and objs[0].key == key:
        return True

    return False


def delete_object(bucket, key):
    """
    Delete KEY in bucket BUCKET.

    Args:
        bucket: string representing a bucket name
        key   : string representing a folder name

    Returns:
        nothing

    Raises:
        Exception on failure.
    """
    logger.debug("{}: Deleting {} from bucket {}".format(__name__, key, bucket))
    try:
        boto3.client('s3').delete_object(Bucket=bucket, Key=key)
    except:
        raise

    return
