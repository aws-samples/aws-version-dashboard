import boto3
import boto3
import csv
import os
import json
import logging

s3 = boto3.client('s3')

s3bucket = os.environ['s3BucketName']

def lambda_handler(event, context):
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    response = s3.list_objects(
        Bucket=s3bucket
    )
    
    with open("/tmp/all_versions.csv", "w+") as csvfile:
        tmpcsv = csv.writer(csvfile)
        tmpcsv.writerow(["Check", "Account", "Region", "Resource ID", "Sub Type", "Deployed Version", "Latest Version", 'Versions Back'])


    
        for i in response.get('Contents'):

            if not i.get('Key') == 'all_versions.csv':
                response = s3.get_object(Bucket=s3bucket, Key=i.get('Key'))
                data = response['Body'].read().decode('utf-8')
                
                splitlines = data.splitlines()
                
                for n in splitlines:
                    splitstr = n.split(',')
                    if not splitstr[0] == 'Check':
                        tmpcsv.writerow(splitstr)
                
        
       

    s3.upload_file('/tmp/all_versions.csv', s3bucket, 'all_versions.csv')

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "version_combine completed",
        }),
    }