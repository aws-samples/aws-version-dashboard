import boto3
import logging
import botocore.exceptions

def lambda_handler(event, context):

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    master_session = boto3.session.Session()
    sts = master_session.client('sts')
    
    current_account = sts.get_caller_identity()['Account']
    
    id = event["account"]
    regions = boto3.session.Session().get_available_regions('es')

    resource_output = dict()

    for region in regions:
        
        if id != current_account:
            role = "arn:aws:iam::{}:role/aws-ver-dash-lambda-es"
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
                es = boto3.client(
                    'es',
                    aws_access_key_id=ACCESS_KEY,
                    aws_secret_access_key=SECRET_KEY,
                    aws_session_token=SESSION_TOKEN,
                    region_name=region,
                )
            except Exception as e:
                logger.error("Assume role error %s", e)
            
        else:
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
