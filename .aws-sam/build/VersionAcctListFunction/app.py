import json
import boto3
import logging
import os
import csv

org = boto3.client('organizations')

accts = {}
accts["accounts"] = []

def lambda_handler(event, context):
    
    print(os.environ['ACCOUNTS'])
    
    if ',' in os.environ['ACCOUNTS']:
        getAccts()
    elif '.csv' in os.environ['ACCOUNTS']:
        getCSV()
    elif 'ALL' in os.environ['ACCOUNTS']:
        getOrgList()
    else:
        getAccts()



    return accts
    
def getAccts():
    accountList = os.environ['ACCOUNTS']
    accountSplit = accountList.split(',')
    
    for i in accountSplit:
        acctslist = accts["accounts"]
        acct = {'account' : i}
        acctslist.append(acct)
        print(acct)

    

def getCSV():
    filePath = os.environ['LAMBDA_TASK_ROOT'] + "/" + os.environ['ACCOUNTS']
    
    with open(filePath) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            print(row)
            acctslist = accts["accounts"]
            acct = {'account' : row[0]}
            acctslist.append(acct)


def getOrgList():
    response = org.list_accounts()
    
    for id in response.get('Accounts'):
        acctslist = accts["accounts"]
        acct = {'account' : id.get('Id')}
        acctslist.append(acct)
    
    