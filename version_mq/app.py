import boto3
import botocore.exceptions
from distutils.version import LooseVersion as versioncmp

def lambda_handler(event, context):

    id = boto3.client('sts').get_caller_identity().get('Account')
    regions = boto3.session.Session().get_available_regions('mq')

    resource_output = dict()

    for region in regions:
        mq = boto3.client('mq', region_name=region)

        try:
            brokerslist = mq.list_brokers()
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'AuthFailure':
                print('Region {region} seems to be disabled for this account, skipping')
                continue
        except:
            raise e
        else:
            brokers = brokerslist["BrokerSummaries"]

            for broker in brokers:
                mq_params = mq.describe_broker(BrokerId=broker['BrokerId'])
                enginetype = mq_params['EngineType']
                deploy_version = mq_params['EngineVersion']
                versions = get_versions(mq, enginetype)
                versions_len = len(versions)
                for i in range(versions_len):
                    if deploy_version == versions[i]:
                        versions_back = i

                resource_output['BrokerName'] = {'Check': 'mq',
                                                 'Account': id,
                                                 'Region': region,
                                                 'Resource ID': broker['BrokerName'],
                                                 'Sub Type': enginetype,
                                                 'Deployed Version': deploy_version,
                                                 'Latest Version': versions[0],
                                                 'Versions Back': versions_back
                                                 }

    return resource_output

def get_versions(mq, engine_type):

    engine_versions = mq.describe_broker_engine_types()
    mq_versions = []

    for enginetype in engine_versions["BrokerEngineTypes"]:
        if enginetype["EngineType"].casefold() == engine_type.casefold():
            for versions in enginetype["EngineVersions"]:
                mq_versions.append(versions['Name'])
    mq_versions.sort(key=versioncmp, reverse=True)
    return mq_versions
