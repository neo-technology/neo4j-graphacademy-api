import os
import logging

from neo4j.v1 import GraphDatabase, basic_auth
from encryption import decrypt_value_str

from retrying import retry

logger = logging.getLogger()
logger.setLevel(logging.INFO)

neo4j_url = 'bolt+routing://%s' % (decrypt_value_str(os.environ['GRAPHACADEMY_DB_HOST_PORT']))
neo4j_user = decrypt_value_str(os.environ['GRAPHACADEMY_DB_USER']) 
neo4j_password = decrypt_value_str(os.environ['GRAPHACADEMY_DB_PW'])

db_driver = GraphDatabase.driver(neo4j_url,  auth=basic_auth(neo4j_user, neo4j_password),
  max_retry_time=15,
  max_connection_lifetime=60)

@retry(stop_max_attempt_number=5, wait_fixed=(1 * 1000))
def get_class_enrollment_db(userId, className): 
  enrolled = False
  session = db_driver.session()
  enrollment_query = """
    MATCH (u:User {auth0_key:{auth0_key}}),
    (c:TrainingClass {name:{class_name}}),
    (u)-[:ENROLLED_IN]->(se:StudentEnrollment)-[:IN_CLASS]->(c)
    WHERE se.active=true
    RETURN se
    """
  res = session.run(enrollment_query, parameters={"auth0_key": userId, "class_name": className})
  for record in res:
    enrolled = True 

  return enrolled

@retry(stop_max_attempt_number=5, wait_fixed=(1 * 1000))
def get_set_class_complete(userId, className):
  session = db_driver.session()
  enrollment_query = """
MATCH (u:User {auth0_key:{auth0_key}})-
     [:ENROLLED_IN]->(se:StudentEnrollment)-[:IN_CLASS]->(c:TrainingClass {name:{class_name}})
WHERE
  se.active=true
WITH u.fullname AS user_name, c.fullname AS course_name, se.first_name + ' ' + se.last_name AS display_name, se
MATCH
  (se)-[p:PASSED]->(q:Quiz)
WHERE NOT EXISTS
  ( (se)-[:FAILED]->(:Quiz) )
WITH
  display_name, user_name, course_name, MAX(p.passed_date) AS max_passed, se, tointeger(round(rand() * 100000000)) AS certnum 
MERGE (se)<-[:INDICATES_COMPLETION]-(coc:Certificate)
ON CREATE SET coc.certificate_number=certnum, se.completed_date=max_passed, coc.issued_at=datetime(), coc.certificate_hash=apoc.util.sha256([tostring(se.createdAt),tostring(certnum)])
RETURN coc.certificate_number AS cert_number, coc.certificate_hash AS cert_hash, user_name, display_name, course_name, max_passed.year AS passed_year, max_passed.month AS passed_month, max_passed.day AS passed_day
  """
  res = session.run(enrollment_query, parameters={"auth0_key": userId, "class_name": className})
  for record in res:
    return record

@retry(stop_max_attempt_number=5, wait_fixed=(1 * 1000))
def set_class_enrollment_db(userId, className, firstName, lastName): 
  session = db_driver.session()
  enrollment_query = """
    MERGE (u:User {auth0_key:{auth0_key}})
    ON CREATE SET u.createdAt=timestamp()
    MERGE (c:TrainingClass {name:{class_name}})
    MERGE (u)-[:ENROLLED_IN]->(se:StudentEnrollment {active: true})-[:IN_CLASS]->(c)
    ON CREATE SET se.createdAt=timestamp(), se.enrolled_date=datetime(), se.first_name={first_name}, se.last_name={last_name}
    """
  res = session.run(enrollment_query, parameters={"auth0_key": userId, "class_name": className, "first_name": firstName, "last_name": lastName})
  res.consume()

  return True

@retry(stop_max_attempt_number=5, wait_fixed=(1 * 1000))
def log_class_part_view_db(userId, className, partName): 
  session = db_driver.session()
  log_query = """
    MERGE (u:User {auth0_key:{auth0_key}})
    ON CREATE SET u.createdAt=timestamp()
    MERGE (c:TrainingClass {name:{class_name}})
    MERGE (u)-[:ENROLLED_IN]->(se:StudentEnrollment {active:true})-[:IN_CLASS]->(c)
    ON CREATE SET se.createdAt=timestamp(), se.enrolled_date=datetime()
    MERGE (c)-[:INCLUDES]->(p:TrainingPart {name:{part_name}})
    ON CREATE SET p.createdAt=timestamp()
    CREATE (se)-[v:VIEWED]->(p)
    SET v.createdAt=timestamp()
    """
  res = session.run(log_query, parameters={"auth0_key": userId, "class_name": className, "part_name": partName})
  res.consume()

  return True
