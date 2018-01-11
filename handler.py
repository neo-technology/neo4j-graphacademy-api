import json
import os
from lib.quizes import set_quiz_status_db, get_quiz_status_db
from lib.classes import set_class_enrollment_db, log_class_part_view_db

def set_class_enrollment(event, context):
    user = event['requestContext']['authorizer']['principalId']
    requestData = json.loads(event["body"])

    className = requestData['className']

    enrollment = set_class_enrollment_db(user, className)

    body = {
        "message": "enrollment indicated",
        "enrolled": True
    }

    headers = { "Content-type": "application/json", "Access-Control-Allow-Origin": "*" }

    response = {
        "statusCode": 200,
        "body": json.dumps(body),
        "headers": headers
    }

    return response

def log_training_view(event, context):
    user = event['requestContext']['authorizer']['principalId']
    requestData = json.loads(event["body"])

    className = requestData['className']
    partName = requestData['partName']

    enrollment = set_class_enrollment_db(user, className)
    log_class_part_view_db(user, className, partName)

    body = {
        "message": "view indicated"
    }

    headers = { "Content-type": "application/json", "Access-Control-Allow-Origin": "*" }

    response = {
        "statusCode": 200,
        "body": json.dumps(body),
        "headers": headers
    }

    return response



def get_quiz_status(event, context):
    user = event['requestContext']['authorizer']['principalId']
    className = event['queryStringParameters']['className']

    quizStatus = get_quiz_status_db(user, className)

    body = {
        "message": "Quiz status retrieved",
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
