import os
import logging
from neo4j import GraphDatabase, basic_auth
from retrying import retry
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# def get_ssm_param(keypart):
#   ssmc = boto3.client('ssm')
#   resp = ssmc.get_parameter(
#     Name='com.neo4j.graphacademy.%s.%s' % (DEPLOY_STAGE, keypart),
#     WithDecryption=True
#   )
#   return resp['Parameter']['Value']

# if DEPLOY_STAGE == 'prod':
#   boltproto = 'bolt+routing://'
# else:
#   boltproto = 'bolt://'
# NEO4J_HOST = '%s%s' % (boltproto, get_ssm_param('dbhostport'))

# neo4j_user = get_ssm_param('dbuser')
# neo4j_password = get_ssm_param('dbpassword')

# db_driver = GraphDatabase.driver(NEO4J_HOST,  auth=basic_auth(neo4j_user, neo4j_password),
#   max_retry_time=15,
#   max_connection_lifetime=60)

NEO4J_HOST = os.environ['NEO4J_HOST']
NEO4J_USER = os.environ['NEO4J_USER']
NEO4J_PASS = os.environ['NEO4J_PASS']
db_driver = GraphDatabase.driver(NEO4J_HOST, auth=basic_auth(NEO4J_USER, NEO4J_PASS))
def set_quiz_status_db(userId, className, quizStatus): 
  session = db_driver.session()
  passed_query = """
    MERGE (u:User {auth0_key:$auth0_key})
    ON CREATE SET u.createdAt=timestamp()
    MERGE (c:TrainingClass {name:$class_name})
    MERGE (u)-[:ENROLLED_IN]->(se:StudentEnrollment {active:true})-[:IN_CLASS]->(c)
    ON CREATE SET se.createdAt=timestamp(), se.enrolled_date=datetime()
    WITH c, se
    MATCH (c)-[:REQUIRES]->(q:Quiz {name:$passed_quiz})
    MERGE (se)-[pp:PASSED]->(q)
    ON CREATE SET pp.passed_date=datetime()
    WITH se, q
    MATCH (se)-[f:FAILED]->(q)
    DELETE f
    """
  for passed_quiz in quizStatus['passed']:
    passed_results = session.run(passed_query, parameters={"auth0_key": userId, "class_name": className, "passed_quiz": passed_quiz})
    passed_results.consume()

  failed_query = """
    MERGE (u:User {auth0_key:$auth0_key})
    ON CREATE SET u.createdAt=timestamp()
    MERGE (c:TrainingClass {name:$class_name})
    MERGE (u)-[:ENROLLED_IN]->(se:StudentEnrollment {active:true})-[:IN_CLASS]->(c)
    ON CREATE SET se.createdAt=timestamp(), se.enrolled_date=datetime()
    WITH c, se
    MATCH (c)-[:REQUIRES]->(q:Quiz {name:$failed_quiz})
    WHERE NOT EXISTS( (se)-[:PASSED]->(q) )
    MERGE (se)-[:FAILED]->(q)
    """
  for failed_quiz in quizStatus['failed']:
    failed_results = session.run(failed_query, parameters={"auth0_key": userId, "class_name": className, "failed_quiz": failed_quiz})
    failed_results.consume()

@retry(stop_max_attempt_number=5, wait_fixed=(1 * 1000))
def get_quiz_status_db(userId, className):
  session = db_driver.session()
  resultDict = {}

  passed_query = """
    MATCH (u:User {auth0_key:$auth0_key})-[:ENROLLED_IN]-(se:StudentEnrollment {active:true})-[:IN_CLASS]->(c:TrainingClass {name:$class_name}),
          (se)-[p:PASSED]->(q:Quiz)
    RETURN q.name AS name
    """
  passed_results = session.run(passed_query, parameters={"auth0_key": userId, "class_name": className})
  resultDict['passed'] = []
  for record in passed_results:
    record = dict((el[0], el[1]) for el in record.items())
    resultDict['passed'].append(record['name'])

  failed_query = """
    MATCH (u:User {auth0_key:$auth0_key})-[:ENROLLED_IN]-(se:StudentEnrollment {active:true})-[:IN_CLASS]->(c:TrainingClass {name:$class_name}),
          (se)-[p:FAILED]->(q:Quiz)
    RETURN q.name AS name
    """
  failed_results = session.run(failed_query, parameters={"auth0_key": userId, "class_name": className})
  resultDict['failed'] = []
  for record in failed_results:
    record = dict((el[0], el[1]) for el in record.items())
    resultDict['failed'].append(record['name'])

  untried_query = """
    MATCH (u:User {auth0_key:$auth0_key})-[:ENROLLED_IN]-(se:StudentEnrollment {active:true})-[:IN_CLASS]->(c:TrainingClass {name:$class_name}), (c)-[:REQUIRES]->(q:Quiz)
WHERE 
    NOT EXISTS
          ( (se)-[:FAILED]->(q) )
    AND NOT EXISTS
          ( (se)-[:PASSED]->(q) )
 RETURN q.name AS name
    """
  untried_results = session.run(untried_query, parameters={"auth0_key": userId, "class_name": className})
  resultDict['untried'] = []
  for record in untried_results:
    record = dict((el[0], el[1]) for el in record.items())
    resultDict['untried'].append(record['name'])

  return resultDict

