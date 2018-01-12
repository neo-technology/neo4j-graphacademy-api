import os

from neo4j.v1 import GraphDatabase, basic_auth
from encryption import decrypt_value_str

neo4j_url = 'bolt://%s' % (decrypt_value_str(os.environ['GRAPHACADEMY_DB_HOST_PORT']))
neo4j_user = decrypt_value_str(os.environ['GRAPHACADEMY_DB_USER']) 
neo4j_password = decrypt_value_str(os.environ['GRAPHACADEMY_DB_PW'])

db_driver = GraphDatabase.driver(neo4j_url,  auth=basic_auth(neo4j_user, neo4j_password))

def set_quiz_status_db(userId, className, quizStatus): 
  session = db_driver.session()
  passed_query = """
    MERGE (u:User {auth0_key:{auth0_key}})
    ON CREATE SET u.createdAt=timestamp()
    MERGE (c:TrainingClass {name:{class_name}})
    MERGE (u)-[:ENROLLED_IN]->(se:StudentEnrollment)-[:IN_CLASS]->(c)
    ON CREATE SET se.createdAt=timestamp()
    WITH c, se
    MATCH (c)-[:REQUIRES]->(q:Quiz {name:{passed_quiz}})
    MERGE (se)-[:PASSED]->(q)
    WITH se, q
    MATCH (se)-[f:FAILED]->(q)
    DELETE f
    """
  for passed_quiz in quizStatus['passed']:
    passed_results = session.run(passed_query, parameters={"auth0_key": userId, "class_name": className, "passed_quiz": passed_quiz})
    passed_results.consume()

  failed_query = """
    MERGE (u:User {auth0_key:{auth0_key}})
    ON CREATE SET u.createdAt=timestamp()
    MERGE (c:TrainingClass {name:{class_name}})
    MERGE (u)-[:ENROLLED_IN]->(se:StudentEnrollment)-[:IN_CLASS]->(c)
    ON CREATE SET se.createdAt=timestamp()
    WITH c, se
    MATCH (c)-[:REQUIRES]->(q:Quiz {name:{failed_quiz}})
    WHERE NOT EXISTS( (se)-[:PASSED]->(q) )
    MERGE (se)-[:FAILED]->(q)
    """
  for failed_quiz in quizStatus['failed']:
    failed_results = session.run(failed_query, parameters={"auth0_key": userId, "class_name": className, "failed_quiz": failed_quiz})
    failed_results.consume()

def get_quiz_status_db(userId, className):
  session = db_driver.session()
  resultDict = {}

  passed_query = """
    MATCH (u:User {auth0_key:{auth0_key}})-[:ENROLLED_IN]-(se:StudentEnrollment)-[:IN_CLASS]->(c:TrainingClass {name:{class_name}}),
          (se)-[p:PASSED]->(q:Quiz)
    RETURN q.name AS name
    """
  passed_results = session.run(passed_query, parameters={"auth0_key": userId, "class_name": className})
  resultDict['passed'] = []
  for record in passed_results:
    record = dict((el[0], el[1]) for el in record.items())
    resultDict['passed'].append(record['name'])

  failed_query = """
    MATCH (u:User {auth0_key:{auth0_key}})-[:ENROLLED_IN]-(se:StudentEnrollment)-[:IN_CLASS]->(c:TrainingClass {name:{class_name}}),
          (se)-[p:PASSED]->(q:Quiz)
    RETURN q.name AS name
    """
  failed_results = session.run(failed_query, parameters={"auth0_key": userId, "class_name": className})
  resultDict['failed'] = []
  for record in failed_results:
    record = dict((el[0], el[1]) for el in record.items())
    resultDict['failed'].append(record['name'])

  return resultDict

