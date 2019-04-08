import boto3
from mock import Mock
from moto import mock_ec2


class MyBoto3(object):

    def __init__(self):
        ec2 = boto3.client('ec2')
        iam = boto3.client('iam')
        resourcegroupstaggingapi = boto3.client('resourcegroupstaggingapi')
        route53 = boto3.client('route53')
        s3 = boto3.client('s3')
        sts = boto3.client('sts')
        return

    def setup_default_session(self, **kwargs):
        return
    
    def resource(self, service_name):
        return self.client(service_name)

    def client(self, service_name):
        services = { 'iam'     : self.iam_stub,
                     'ec2'     : self.ec2_stub,
                     'resourcegroupstaggingapi' : self.rgtaggingapi_stub,
                     'route53' : self.r53_stub,
                     's3'      : self.s3_stub,
                     'sts'     : self.sts_stub }
        return services[service_name]()

    @mock_ec2
    def ec2_stub(self):
        return boto3.client('ec2')

    def iam_stub(self, sub_service_field=None):
        return Mock(list_account_aliases=Mock(return_value={
            'AccountAliases' : ['tests-random']}))

    def rgtaggingapi_stub(self):
        return self.ResourceGroupsTaggingAPIClass()

    def r53_stub(self):
        return self.Route53Class()

    def s3_stub(self):
        return self.S3Class()

    def sts_stub(self):
        return Mock(get_caller_identity=Mock(
            return_value=Mock(get=Mock(return_value='123456789012'))))

    class ResourceGroupsTaggingAPIClass():
        def __init__(self):
            return

        def client(self):
            return self.client

        def get_resources(self, **kwargs):
            exists = {
                "PaginationToken": "",
                "ResourceTagMappingList": [
                    {
                        "ResourceARN": "arn:aws:ec2:us-east-1:419934374614:instance/i-c3bef428",
                        "Tags": [
                            {
                                "Key": "env_name",
                                "Value": "myenvname"
                            },
                            {
                                "Key": "env_version",
                                "Value": "a"
                            },
                            {
                                "Key": "product",
                                "Value": "mock_product"
                            }
                            
                        ]
                    }
                ],
                "ResponseMetadata": {
                    "RetryAttempts": 0,
                    "HTTPStatusCode": 200,
                    "RequestId": "d7216a34-ca38-11e7-bade-e73a12746909",
                    "HTTPHeaders": {
                        "x-amzn-requestid": "d7216a34-ca38-11e7-bade-e73a12746909",
                        "date": "Wed, 15 Nov 2017 19:11:52 GMT",
                        "content-length": "7540",
                        "content-type": "application/x-amz-json-1.1"
                    }
                }
            }
            
            not_exists = { u'ResourceTagMappingList': [] }

            if ( kwargs['TagFilters'][0]['Values'][0] == 'myenvname' and
                 kwargs['TagFilters'][2]['Values'][0] != 'd') :
                return exists
            else:
                return not_exists

    class Route53Class():
        def __init__(self):
            return

        def client(self):
            return self.client

        def list_hosted_zones_by_name(self, **kwargs):
            return {
                "HostedZones": [
                    {
                        "ResourceRecordSetCount": 3,
                        "CallerReference": "8822619A-56F3-B801-8D79-C23EAB1D220B",
                        "Config": {
                            "PrivateZone": False
                        },
                        "Id": "/hostedzone/Z1RWWTK7Y8UDDQ",
                        "Name": "subdomain.toplevel.domain."
                    },
                    {
                        "ResourceRecordSetCount": 2,
                        "CallerReference": "2017-02-22T18:08:25.689513617-05:00",
                        "Config": {
                            "Comment": "Private Env domain of a subdomain",
                            "PrivateZone": True
                        },
                        "Id": "/hostedzone/Z3L01Q527J489K",
                        "Name": "myenv-a.subdomain.toplevel.domain."
                    },
                    {
                        "ResourceRecordSetCount": 4,
                        "CallerReference": "2017-02-22T18:08:24.107796242-05:00",
                        "Config": {
                            "Comment": "Public env domain of a subdomain",
                            "PrivateZone": False
                        },
                        "Id": "/hostedzone/Z3H85C4DDTY08V",
                        "Name": "myenv-a.subdomain.toplevel.domain."
                    }
                ],
                "IsTruncated": 'false',
                "MaxItems": "100"
            }

    class S3Class():
        def __init__(self):
            return

        def client(self):
            return self.client

        class Object():
            def __init__(self, bucket, key):
                return

            def upload_file(self, file):
                return True
