import boto3
import botocore.exceptions
from distutils.version import LooseVersion as versioncmp

def lambda_handler(event, context):

    id = boto3.client('sts').get_caller_identity().get('Account')
    regions = boto3.session.Session().get_available_regions('docdb')

    resource_output = dict()

    for region in regions:
        docdb = boto3.client('docdb', region_name=region)
        print(region)
        try:
            instances = docdb.describe_db_instances()
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'AuthFailure':
                print('Region {region} seems to be disabled for this account, skipping')
                continue
        except:
            raise e
        else:
            instances = instances["DBInstances"]

            versions = get_versions(docdb)
            versions_len = len(versions)

            for instance in instances:
                if instance['Engine'] == 'docdb':
                    for i in range(versions_len):
                        if instance['EngineVersion'] == versions[i]:
                            versions_back = i
                    resource_output[instance['DBInstanceIdentifier']] = {'Check': 'docdb',
                                                                         'Account': id,
                                                                         'Region': region,
                                                                         'Resource ID': instance['DBInstanceIdentifier'],
                                                                         'Sub Type': instance['Engine'],
                                                                         'Deployed Version': instance['EngineVersion'],
                                                                         'Latest Version': versions[0],
                                                                         'Versions Back': versions_back
                                                                         }

    return resource_output

def get_versions(docdb):

    docdb_versions = []

    try:
        engine_versions = docdb.describe_db_engine_versions(Engine='docdb')
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'InvalidParameterValue':
            print('Docdb not supported in this region')
    except:
        raise e
    else:
        for versions in engine_versions['DBEngineVersions']:
            docdb_versions.append(versions['EngineVersion'])
        docdb_versions.sort(key=versioncmp, reverse=True)

    return docdb_versions