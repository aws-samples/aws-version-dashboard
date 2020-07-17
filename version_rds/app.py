import boto3
import botocore.exceptions
from distutils.version import LooseVersion as versioncmp

def lambda_handler(event, context):

    id = boto3.client('sts').get_caller_identity().get('Account')
    regions = boto3.session.Session().get_available_regions('rds')

    resource_output = dict()

    for region in regions:

        rds = boto3.client('rds', region_name=region)
        try:
            instances = rds.describe_db_instances()
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'AuthFailure':
                print('Region {region} seems to be disabled for this account, skipping')
                continue
        except:
            raise e
        else:
            instances = instances["DBInstances"]

            latest_version = dict()

            for instance in instances:
                if instance['Engine'] not in latest_version.keys():
                    latest_version[instance['Engine']] = get_versions(rds, instance['Engine'])

                latest_version_len = len(latest_version[instance['Engine']])
                for i in range(latest_version_len):
                    if latest_version[instance['Engine']][i] == instance['EngineVersion']:
                        versions_back = i

                resource_output[instance['DBInstanceIdentifier']] = {'Check': 'rds',
                                                                     'Account': id,
                                                                     'Region': region,
                                                                     'Resource ID': instance['DBInstanceIdentifier'],
                                                                     'Sub Type': instance['Engine'],
                                                                     'Deployed Version': instance['EngineVersion'],
                                                                     'Latest Version': latest_version[instance['Engine']][0],
                                                                     'Versions Back': versions_back
                                                                     }

    return resource_output

def get_versions(rds, engine_type):

    rds_versions = rds.describe_db_engine_versions(Engine=engine_type)
    engine_versions = []

    for versions in rds_versions['DBEngineVersions']:
        if engine_type == 'aurora' and 'aurora' not in versions['EngineVersion']:
            pass
        elif engine_type == 'aurora-mysql' and 'aurora' not in versions['EngineVersion']:
            pass
        else:
            engine_versions.append(versions['EngineVersion'])

    engine_versions.sort(key=versioncmp, reverse=True)
    if engine_type == 'aurora-mysql':
        engine_versions.append('5.7.12')
    if engine_type == 'aurora':
        engine_versions.append('5.6.10a')

    return engine_versions