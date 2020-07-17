import boto3
import os
import random, string
import urllib3
import json
from botocore.exceptions import ClientError

step = boto3.client('stepfunctions')
http = urllib3.PoolManager()

def lambda_handler(event, context):

    print(event)
    execution_id = randomid(10)

    response_data = {}

    try:
        step_response = step.start_execution(
            stateMachineArn=os.environ['StepFunctionArn'],
            name=execution_id,
            input='{}'
        )

    except ClientError as e:
        response_data['Data'] = e
        send(event, context, 'FAILED', response_data, 'TriggerStepFunction')
    else:
        response_data['Data'] = step_response['executionArn']
        send(event, context, 'SUCCESS', response_data, 'TriggerStepFunction')

    return

def randomid(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def send(event, context, responseStatus, responseData, physicalResourceId=None, noEcho=False):
    responseUrl = event['ResponseURL']

    print(responseUrl)

    responseBody = {}
    responseBody['Status'] = responseStatus
    responseBody['Reason'] = 'See the details in CloudWatch Log Stream: ' + context.log_stream_name
    responseBody['PhysicalResourceId'] = physicalResourceId or context.log_stream_name
    responseBody['StackId'] = event['StackId']
    responseBody['RequestId'] = event['RequestId']
    responseBody['LogicalResourceId'] = event['LogicalResourceId']
    responseBody['NoEcho'] = noEcho
    responseBody['Data'] = responseData

    print(responseBody)
    json_responseBody = json.dumps(responseBody)

    print("Response body:\n" + json_responseBody)

    headers = {
        'content-type': '',
        'content-length': str(len(json_responseBody))
    }

    try:
        response = http.request('PUT',
                                responseUrl,
                                body=json_responseBody,
                                headers=headers)
        print("Status code: " + response.reason)
    except Exception as e:
        print("send(..) failed executing requests.put(..): " + str(e))