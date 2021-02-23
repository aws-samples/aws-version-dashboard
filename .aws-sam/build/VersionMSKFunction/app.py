import boto3
import logging
import botocore.exceptions
from distutils.version import LooseVersion as versioncmp

def lambda_handler(event, context):

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    master_session = boto3.session.Session()
    sts = master_session.client('sts')
    
    current_account = sts.get_caller_identity()['Account']
    
    id = event["account"]
    regions = boto3.session.Session().get_available_regions('kafka')

    resource_output = dict()

    for region in regions:
        
        if id != current_account:
            role = "arn:aws:iam::{}:role/aws-ver-dash-lambda-msk"
            role_arn = role.format(id)
            try:
                assume_role_response = sts.assume_role(
                    RoleArn=role_arn, RoleSessionName="LambdaExecution")
                
                sts_connection = boto3.client('sts')
                acct_b = sts_connection.assume_role(
                    RoleArn=role_arn,
                    RoleSessionName="cross_acct_lambda"
                )
    
                ACCESS_KEY = acct_b['Credentials']['AccessKeyId']
                SECRET_KEY = acct_b['Credentials']['SecretAccessKey']
                SESSION_TOKEN = acct_b['Credentials']['SessionToken']

                # create service client using the assumed role credentials, e.g. S3
                msk = boto3.client(
                    'kafka',
                    aws_access_key_id=ACCESS_KEY,
                    aws_secret_access_key=SECRET_KEY,
                    aws_session_token=SESSION_TOKEN,
                    region_name=region,
                )
            except Exception as e:
                logger.error("Assume role error %s", e)
            
        else:
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
