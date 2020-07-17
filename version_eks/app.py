import boto3
import botocore.exceptions

def lambda_handler(event, context):

    eks_versions = ['1.16', '1.15', '1.14', '1.13']
    eks_versions_len = len(eks_versions)

    id = boto3.client('sts').get_caller_identity().get('Account')
    regions = boto3.session.Session().get_available_regions('eks')

    resource_output = dict()

    for region in regions:
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
