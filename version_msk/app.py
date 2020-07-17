import boto3
import botocore.exceptions
from distutils.version import LooseVersion as versioncmp

def lambda_handler(event, context):

    id = boto3.client('sts').get_caller_identity().get('Account')
    regions = boto3.session.Session().get_available_regions('kafka')

    resource_output = dict()

    for region in regions:
        msk = boto3.client('kafka', region_name=region)

        try:
            clusterslist = msk.list_clusters()
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'AuthFailure':
                print('Region {region} seems to be disabled for this account, skipping')
                continue
        except:
            raise e
        else:
            clusterslist = clusterslist["ClusterInfoList"]

            versions = get_versions(msk)
            versions_len = len(versions)

            for cluster in clusterslist:
                for i in range(versions_len):
                    if cluster['CurrentBrokerSoftwareInfo']['KafkaVersion'] == versions[i]:
                        versions_back = i

                resource_output[cluster['ClusterName']] = {'Check': 'msk',
                                                           'Account': id,
                                                           'Region': region,
                                                           'Resource ID': cluster['ClusterName'],
                                                           'Sub Type': 'kafka',
                                                           'Deployed Version': cluster['CurrentBrokerSoftwareInfo']['KafkaVersion'],
                                                           'Latest Version': versions[0],
                                                           'Versions Back': versions_back
                                                           }

    return resource_output

def get_versions(msk):

    kafka_versions = msk.list_kafka_versions()
    msk_versions = []

    for versions in kafka_versions['KafkaVersions']:
        msk_versions.append(versions['Version'])
    msk_versions.sort(key=versioncmp, reverse=True)
    return msk_versions
