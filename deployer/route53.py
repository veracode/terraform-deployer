# -*- coding: utf-8 -*-
#
# Copyright Veracode Inc., 2014

import boto3
import logging
import os

from deployer.exceptions import MissingConfigurationParameterException

logger = logging.getLogger(os.path.basename('deployer'))


def get_zone_id(zone_name):
    """
    Returns the Zone ID for the specified zone name.

    Args:
        zone_name: string representing the zone name.

    Returns:
        None

    Raises:
        MissingConfigurationParameterException if zone_name is not defined.
    """
    if not zone_name:
        msg = "DNS Zone Name not defined."
        raise MissingConfigurationParameterException(msg)

    r53 = boto3.client('route53')
    zones = r53.list_hosted_zones_by_name()
    for zone in zones['HostedZones']:
        if zone['Name'].rstrip('.') == zone_name :
            if not zone['Config']['PrivateZone']:
                return zone['Id'].split('/')[2]

    return None
