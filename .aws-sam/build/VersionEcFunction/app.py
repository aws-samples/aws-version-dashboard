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
    regions = boto3.session.Session().get_available_regions('elasticache')

    resource_output = dict()

    for region in regions:
        
        if id != current_account:
            role = "arn:aws:iam::{}:role/aws-ver-dash-lambda-ec"
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
                ec = boto3.client(
                    'elasticache',
                    aws_access_key_id=ACCESS_KEY,
                    aws_secret_access_key=SECRET_KEY,
                    aws_session_token=SESSION_TOKEN,
                    region_name=region,
                )
            except Exception as e:
                logger.error("Assume role error %s", e)
            
        else:
            ec = boto3.client('elasticache', region_name=region)

        try:
            clusters = ec.describe_cache_clusters()
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'AuthFailure':
                print('Region {region} seems to be disabled for this account, skipping')
                continue
        except:
            raise e
        else:
            memcache_versions = get_versions(ec, 'memcached')
            mem_versions_len = len(memcache_versions)
            redis_versions = get_versions(ec, 'redis')
            red_versions_len = len(redis_versions)

            for cluster in clusters['CacheClusters']:
                if cluster['Engine'] == 'memcached':
                    engine_latest = memcache_versions[0]
                    for i in range(mem_versions_len):
                        if memcache_versions[i] == cluster['EngineVersion']:
                            versions_back = i
                elif cluster['Engine'] == 'redis':
                    engine_latest = redis_versions[0]
                    for i in range(red_versions_len):
                        if redis_versions[i] == cluster['EngineVersion']:
                            versions_back = i

                resource_output[cluster['CacheClusterId']] = {'Check': 'elasticache',
                                                              'Account': id,
                                                              'Region': region,
                                                              'Resource ID': cluster['CacheClusterId'],
                                                              'Sub Type': cluster['Engine'],
                                                              'Deployed Version': cluster['EngineVersion'],
                                                              'Latest Version': engine_latest,
                                                              'Versions Back': versions_back
                                                              }

    return resource_output

def get_versions(ec, engine):

    params = ec.describe_cache_engine_versions(Engine=engine)
    versions = []

    for version in params['CacheEngineVersions']:
        versions.append(version['EngineVersion'])
    versions.sort(key=versioncmp, reverse=True)

    return versions
