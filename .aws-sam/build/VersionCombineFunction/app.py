import json
import boto3
import csv
import os
import logging

s3 = boto3.client('s3')

bucket = os.environ['s3BucketName']

def lambda_handler(event, context):
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    logger.info("Processing account %s", event)
    
    accountid = ""
    
    for get in event:
        for account in get:
            if not get[account]['Account'] == '':
                accountid = get[account]['Account']
    
    with open("/tmp/" + accountid + ".csv", "w+") as csvfile:
        tmpcsv = csv.writer(csvfile)
        tmpcsv.writerow(["Check", "Account", "Region", "Resource ID", "Sub Type", "Deployed Version", "Latest Version", 'Versions Back'])

        for check in event:
            for instance in check:
                tmpcsv.writerow([check[instance]['Check'],
                                 check[instance]['Account'],
                                 check[instance]['Region'],
                                 check[instance]['Resource ID'],
                                 check[instance]['Sub Type'],
                                 check[instance]['Deployed Version'],
                                 check[instance]['Latest Version'],
                                 check[instance]['Versions Back']
                                ])

    s3.upload_file('/tmp/' + accountid + '.csv', bucket, accountid + '.csv')

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "version_combine completed",
        }),
    }
