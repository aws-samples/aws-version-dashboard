import json
import boto3
import logging
import os
import csv

org = boto3.client('organizations')

def lambda_handler(event, context):
    
    accts = {}
    accts["accounts"] = []
    
    print(os.environ['ACCOUNTS'])
    
    if ',' in os.environ['ACCOUNTS']:
        getAccts(accts)
    elif '.csv' in os.environ['ACCOUNTS']:
        getCSV(accts)
    elif 'ALL' in os.environ['ACCOUNTS']:
        getOrgList(accts)
    else:
        getAccts(accts)



    return accts
    
def getAccts(accts):
    accountList = os.environ['ACCOUNTS']
    accountSplit = accountList.split(',')
    
    for i in accountSplit:
        acctslist = accts["accounts"]
        acct = {'account' : i}
        acctslist.append(acct)
        print(acct)

    

def getCSV(accts):
    filePath = os.environ['LAMBDA_TASK_ROOT'] + "/" + os.environ['ACCOUNTS']
    
    with open(filePath) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            print(row)
            acctslist = accts["accounts"]
            acct = {'account' : row[0]}
            acctslist.append(acct)


def getOrgList(accts):
    response = org.list_accounts()
    
    for id in response.get('Accounts'):
        acctslist = accts["accounts"]
        acct = {'account' : id.get('Id')}
        acctslist.append(acct)
    
    