import os

from neo4j.v1 import GraphDatabase, basic_auth
from encryption import decrypt_value_str

neo4j_url = 'bolt://%s' % (decrypt_value_str(os.environ['GRAPHACADEMY_DB_HOST_PORT']))
neo4j_user = decrypt_value_str(os.environ['GRAPHACADEMY_DB_USER']) 
neo4j_password = decrypt_value_str(os.environ['GRAPHACADEMY_DB_PW'])

db_driver = GraphDatabase.driver(neo4j_url,  auth=basic_auth(neo4j_user, neo4j_password))

def set_quiz_status_db(userId, className, quizStatus): 
  session = db_driver.session()
  query = """
    MERGE (u:User {auth0_key:{auth0_key}})
    MERGE (c:TrainingClass {name:{class_name}})
    MERGE (u)-[:ENROLLED_IN]->(se:StudentEnrollment)-[:IN_CLASS]->(c)
    MERGE (se)-[:TOOK_QUIZES]->(cq:ClassQuizes)
    SET cq.passed={passed},
        cq.failed={failed}
    """
  results = session.run(query, parameters={"auth0_key": userId, "class_name": className, "passed": quizStatus["passed"], "failed": quizStatus["failed"]})
  results.consume()

def get_quiz_status_db(userId, className):
  session = db_driver.session()
  resultDict = {}
  query = """
    MATCH (u:User {auth0_key:{auth0_key}})-[:ENROLLED_IN]-(se:StudentEnrollment)-[:IN_CLASS]->(c:TrainingClass {name:{class_name}}),
          (se)-[:TOOK_QUIZES]->(cq:ClassQuizes)
    RETURN cq.passed AS passed, cq.failed AS failed
    """
  results = session.run(query, parameters={"auth0_key": userId, "class_name": className})
  for record in results:
    record = dict((el[0], el[1]) for el in record.items())
    resultDict['passed'] = record['passed']
    resultDict['failed'] = record['failed']

  return resultDict

