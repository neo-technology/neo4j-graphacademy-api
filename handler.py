import json
import os
import logging
from lib.quizes import set_quiz_status_db, get_quiz_status_db
from lib.classes import get_class_enrollment_db, set_class_enrollment_db, log_class_part_view_db, get_set_class_complete
from lib.certificate import generate_certificate

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def gen_class_certificate(event, context):
    userId = event['requestContext']['authorizer']['principalId']
    requestData = json.loads(event["body"])
    className = requestData['className']

    quiz_status = get_quiz_status_db(userId, className)

    if ( len(quiz_status['passed']) > 0 and len(quiz_status['failed']) == 0 and len(quiz_status['untried']) == 0 ):
      # all quizes passed
      classInfo = get_set_class_complete(userId, className)

      cert = generate_certificate(userId, classInfo['display_name'], '%s-%s-%s' % (classInfo['passed_year'], classInfo['passed_month'], classInfo['passed_day']), classInfo['cert_number'], classInfo['course_name'])

      body = {
        "message": "certificate generated",
        "url": cert
      }
      
      statusCode = 200
    else:
      statusCode = 404
      body = {
        "message": "certificate not able to be generated"
      }

    headers = { "Content-type": "application/json", "Access-Control-Allow-Origin": "*" }

    response = {
        "statusCode": 200,
        "body": json.dumps(body),
        "headers": headers
    }

    return response


def get_class_enrollment(event, context):
    user = event['requestContext']['authorizer']['principalId']
    className = event['queryStringParameters']['className']

    enrollment = get_class_enrollment_db(user, className)

    logger.info("enrollment retrieved for user %s in class %s: %s" % (user, className, enrollment))

    body = {
        "message": "enrollment retrieved",
        "enrolled": enrollment
    }

    headers = { "Content-type": "application/json", "Access-Control-Allow-Origin": "*" }

    response = {
        "statusCode": 200,
        "body": json.dumps(body),
        "headers": headers
    }

    return response

def set_class_enrollment(event, context):
    user = event['requestContext']['authorizer']['principalId']
    requestData = json.loads(event["body"])
    className = requestData['className']
    firstName = requestData['firstName']
    lastName = requestData['lastName']

    enrollment = set_class_enrollment_db(user, className, firstName, lastName)

    logger.info("enrollment indicated for user %s in class %s" % (user, className))

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

    logger.info("quiz status indicated for user %s in class %s with passed %s and failed %s" % (user, requestData["className"], json.dumps(requestData["passed"]), json.dumps(requestData["failed"])))

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
