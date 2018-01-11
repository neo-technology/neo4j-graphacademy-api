import os

from neo4j.v1 import GraphDatabase, basic_auth
from encryption import decrypt_value_str

neo4j_url = 'bolt://%s' % (decrypt_value_str(os.environ['GRAPHACADEMY_DB_HOST_PORT']))
neo4j_user = decrypt_value_str(os.environ['GRAPHACADEMY_DB_USER']) 
neo4j_password = decrypt_value_str(os.environ['GRAPHACADEMY_DB_PW'])

db_driver = GraphDatabase.driver(neo4j_url,  auth=basic_auth(neo4j_user, neo4j_password))

def set_class_enrollment_db(userId, className): 
  session = db_driver.session()
  enrollment_query = """
    MERGE (u:User {auth0_key:{auth0_key}})
    ON CREATE SET u.createdAt=timestamp()
    MERGE (c:TrainingClass {name:{class_name}})
    MERGE (u)-[:ENROLLED_IN]->(se:StudentEnrollment)-[:IN_CLASS]->(c)
    ON CREATE SET se.createdAt=timestamp()
    """
  res = session.run(enrollment_query, parameters={"auth0_key": userId, "class_name": className})
  res.consume()

  return True

def log_class_part_view_db(userId, className, partName): 
  session = db_driver.session()
  log_query = """
    MERGE (u:User {auth0_key:{auth0_key}})
    ON CREATE SET u.createdAt=timestamp()
    MERGE (c:TrainingClass {name:{class_name}})
    MERGE (u)-[:ENROLLED_IN]->(se:StudentEnrollment)-[:IN_CLASS]->(c)
    ON CREATE SET se.createdAt=timestamp()
    MERGE (c)-[:INCLUDES]->(p:TrainingPart {name:{part_name}})
    ON CREATE SET p.createdAt=timestamp()
    CREATE (se)-[v:VIEWED]->(p)
    SET v.createdAt=timestamp()
    """
  res = session.run(log_query, parameters={"auth0_key": userId, "class_name": className, "part_name": partName})
  res.consume()

  return True
