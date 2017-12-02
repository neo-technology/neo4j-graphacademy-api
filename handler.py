import json
import os
from lib.quizes import set_quiz_status_db, get_quiz_status_db

def get_quiz_status(event, context):
    user = event['requestContext']['authorizer']['principalId']
    className = event['queryStringParameters']['className']

    quizStatus = get_quiz_status_db(user, className);

    body = {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "quizStatus": quizStatus
    }

    headers = { "Content-type": "application/json", "Access-Control-Allow-Origin": "*" }

    response = {
        "statusCode": 200,
        "body": json.dumps(body),
        "headers": headers
    }

    return response

def set_quiz_status(event, context):
    user = event['requestContext']['authorizer']['principalId']
    requestData = json.loads(event["body"])

    set_quiz_status_db(user, requestData["className"], {"passed": requestData["passed"], "failed": requestData["failed"]})

    body = {
        "message": "Updated quiz status"
    }

    headers = { "Content-type": "application/json", "Access-Control-Allow-Origin": "*" }

    response = {
        "statusCode": 200,
        "body": json.dumps(body),
        "headers": headers
    }

    return response
