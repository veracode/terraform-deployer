#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import boto3
# import datetime
# import json
# from moto import ( mock_ec2,
#                    mock_route53 )


# @mock_ec2
# def foo():
#     client = boto3.client('ec2')
#     vpc1 = client.create_vpc(CidrBlock='10.1.0.0/16').get('Vpc').get('VpcId')
#     client.create_tags(Resources = [ vpc1 ],
#                        Tags=[ {'Key':'Name',
#                                'Value' : 'myproj-myenvname-a'},
#                               {'Key':'env',
#                                'Value' : 'myenvname-a'} ])
#     filters = [{'Name': 'tag:Name', 'Values': ['myproj-myenvname-a'] }]
#     print("Dumping: client.describe_vpcs()")
#     print(json.dumps(client.describe_vpcs(), indent=4))
#     print("")
#     print("Dumping: client.describe_vpcs(Filters=filters)")
#     print(json.dumps(client.describe_vpcs(Filters=filters), indent=4))
#     return


# @mock_route53
# def bar():

#     caller_ref = datetime.datetime.now().strftime('%s')
#     r53client = boto3.client('route53')
#     zone_name = "subdomain.toplevel.domain"
#     r53client.create_hosted_zone(Name=zone_name,
#                                  CallerReference=caller_ref )

#     zones = r53client.list_hosted_zones_by_name()
#     print("Dumping zones without specifying DNSName:")
#     print(json.dumps(zones))
#     zones2 = r53client.list_hosted_zones_by_name(DNSName=zone_name)
#     print("Dumping zones with specifying DNSName:")
#     print(json.dumps(zones2))
#     return


# #foo()
# bar()

