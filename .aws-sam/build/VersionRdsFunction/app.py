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
    regions = boto3.session.Session().get_available_regions('rds')

    resource_output = dict()

    for region in regions:
        
        if id != current_account:
            role = "arn:aws:iam::{}:role/aws-ver-dash-lambda-rds"
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
                rds = boto3.client(
                    'rds',
                    aws_access_key_id=ACCESS_KEY,
                    aws_secret_access_key=SECRET_KEY,
                    aws_session_token=SESSION_TOKEN,
                    region_name=region,
                )
            except Exception as e:
                logger.error("Assume role error %s", e)
            
        else:
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