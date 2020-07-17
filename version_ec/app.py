import boto3
import botocore.exceptions
from distutils.version import LooseVersion as versioncmp

def lambda_handler(event, context):

    id = boto3.client('sts').get_caller_identity().get('Account')
    regions = boto3.session.Session().get_available_regions('elasticache')

    resource_output = dict()

    for region in regions:
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
