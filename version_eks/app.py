import boto3
import logging
import botocore.exceptions

def lambda_handler(event, context):

    eks_versions = ['1.25', '1.24', '1.23', '1.22', '1.21', '1.20', '1.19']
    eks_versions_len = len(eks_versions)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    master_session = boto3.session.Session()
    sts = master_session.client('sts')
    
    current_account = sts.get_caller_identity()['Account']
    
    id = event["account"]
    regions = boto3.session.Session().get_available_regions('eks')

    resource_output = dict()

    for region in regions:
        if id != current_account:
            role = "arn:aws:iam::{}:role/aws-ver-dash-lambda-eks"
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
                eks = boto3.client(
                    'eks',
                    aws_access_key_id=ACCESS_KEY,
                    aws_secret_access_key=SECRET_KEY,
                    aws_session_token=SESSION_TOKEN,
                    region_name=region,
                )
            except Exception as e:
                logger.error("Assume role error %s", e)
            
        else:
            eks = boto3.client('eks', region_name=region)

        try:
            clusterslist = eks.list_clusters()
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'AuthFailure':
                print('Region {region} seems to be disabled for this account, skipping')
                continue
        except:
            raise e
        else:
            clusterslist = clusterslist['clusters']

            for clusterName in clusterslist:
                instance = eks.describe_cluster(name=clusterName)
                for i in range(eks_versions_len):
                    if instance['cluster']['version'] == eks_versions[i]:
                        versions_back = i

                resource_output[instance['cluster']['name']] = {'Check': 'eks',
                                                                'Account': id,
                                                                'Region': region,
                                                                'Resource ID': instance['cluster']['name'],
                                                                'Sub Type': '',
                                                                'Deployed Version': instance['cluster']['version'],
                                                                'Latest Version': eks_versions[0],
                                                                'Versions Back': versions_back
                                                                }

    return resource_output
