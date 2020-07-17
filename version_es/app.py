import boto3
import botocore.exceptions

def lambda_handler(event, context):

    id = boto3.client('sts').get_caller_identity().get('Account')
    regions = boto3.session.Session().get_available_regions('es')

    resource_output = dict()

    for region in regions:
        es = boto3.client('es', region_name=region)

        try:
            domains = es.list_domain_names()
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'AuthFailure':
                print('Region {region} seems to be disabled for this account, skipping')
                continue
        except:
            raise e
        else:
            versions = es.list_elasticsearch_versions()['ElasticsearchVersions']
            versions.sort(reverse=True)
            length = len(versions)

            for domain in domains['DomainNames']:
                domain_describe = es.describe_elasticsearch_domain(DomainName=domain['DomainName'])
                deployed_version = domain_describe['DomainStatus']['ElasticsearchVersion']
                for i in range(length):
                    if versions[i] == deployed_version:
                        versions_back = i

                resource_output[domain['DomainName']] = {'Check': 'elasticsearch',
                                                         'Account': id,
                                                         'Region': region,
                                                         'Resource ID': domain['DomainName'],
                                                         'Sub Type': '',
                                                         'Deployed Version': domain_describe['DomainStatus']['ElasticsearchVersion'],
                                                         'Latest Version': versions[0],
                                                         'Versions Back': versions_back
                                                         }

    return resource_output
