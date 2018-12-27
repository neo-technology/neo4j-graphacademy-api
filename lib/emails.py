import base64
import datetime
import hashlib
import logging
import os

import boto3
import flask
from flask import render_template
from botocore.vendored import requests
from encryption import decrypt_value_str

from neo4j.v1 import GraphDatabase, basic_auth

LOGGING_LEVEL = int(os.environ.get("LOGGING_LEVEL", 0))
logger = logging.getLogger()
logger.setLevel(LOGGING_LEVEL)

app = flask.Flask('myemail')

neo4j_url = 'bolt://%s' % (decrypt_value_str(os.environ['GRAPHACADEMY_DB_HOST_PORT']))
neo4j_user = decrypt_value_str(os.environ['GRAPHACADEMY_DB_USER'])
neo4j_password = decrypt_value_str(os.environ['GRAPHACADEMY_DB_PW'])

db_driver = GraphDatabase.driver(neo4j_url,  auth=basic_auth(neo4j_user, neo4j_password),
  max_retry_time=15,
  max_connection_lifetime=60)

def mark_email_queued(auth0_key, timestamp, field):
    session = db_driver.session()

    # cypher query for queued
    email_queued_query = """
MATCH (u:User {auth0_key:{auth0_key}})-[:ENROLLED_IN]-(s:StudentEnrollment {createdAt:{createdAt}, active:true})
CALL apoc.create.setProperty(s, {field}, 'Q')
YIELD node
RETURN s
"""
    results = session.run(email_queued_query, parameters={"auth0_key":auth0_key, "createdAt":timestamp, "field":field}).consume()
    return results

def mark_email_sent(auth0_key, timestamp, field):
    session = db_driver.session()

    # cypher query for queued
    email_queued_query = """
MATCH (u:User {auth0_key:{auth0_key}})-[:ENROLLED_IN]-(s:StudentEnrollment {createdAt:{createdAt}, active:true})
CALL apoc.create.setProperty(s, {field}, datetime())
YIELD node
RETURN s
"""
    results = session.run(email_queued_query, parameters={"auth0_key":auth0_key, "createdAt":timestamp, "field":field}).consume()
    return results

def email_reminder_messages():
    session = db_driver.session()

    # cypher query for email
    reminder_email_query = """
MATCH (u:User)-[:ENROLLED_IN]->(s:StudentEnrollment {active:true})-[:IN_CLASS]-(c:TrainingClass)
WHERE EXISTS (c.reminder_email_template)
AND NOT EXISTS (s.reminder_email_sent)
AND datetime() > datetime( {epochMillis: s.createdAt}) + c.reminder_time
AND NOT u.email IS NULL
AND NOT EXISTS(s.completed_date)
RETURN u.auth0_key AS auth0_key, s.createdAt AS e_c, datetime( {epochMillis: s.createdAt}) AS enrollment_created_at, c.welcome_email_template AS template, c.time_est AS time_est, datetime( {epochMillis: s.createdAt}) + c.deadline AS deadline, c.reminder_time.days + ' days' AS reminder_time, c.fullname AS course_name, coalesce(s.first_name, u.first_name, u.firstName) + ' ' + coalesce(s.last_name, u.last_name, u.lastName) AS display_name, u.email AS email, c.course_url AS course_url
"""
    results = session.run(reminder_email_query)
    for record in results:
      # mark_email_queued
      mark_email_queued(record['auth0_key'], record['e_c'], 'reminder_email_sent')
      
      tmpl_vars = {
        'course_name': record['course_name'],
        'deadline': record['deadline'].iso_format()[:10],
        'time_est': record['time_est'],
        'reminder_time': record['reminder_time'],
        'display_name': record['display_name'],
        'course_url': record['course_url']
      }
      send_email('reminder', 'Neo4j GraphAcademy <devrel@neo4j.com>', record['email'], 'Reminder to complete GraphAcademy course: %s' % (tmpl_vars['course_name']), tmpl_vars)
      mark_email_sent(record['auth0_key'], record['e_c'], 'reminder_email_sent')




def email_welcome_messages():
    session = db_driver.session()

    # cypher query for email
    welcome_email_query = """
MATCH (u:User)-[:ENROLLED_IN]->(s:StudentEnrollment {active:true})-[:IN_CLASS]-(c:TrainingClass)
WHERE EXISTS (c.welcome_email_template)
AND NOT EXISTS (s.welcome_email_sent)
AND NOT u.email IS NULL
RETURN u.auth0_key AS auth0_key, s.createdAt AS e_c, datetime( {epochMillis: s.createdAt}) AS enrollment_created_at, c.welcome_email_template AS template, c.time_est AS time_est, datetime( {epochMillis: s.createdAt}) + c.deadline AS deadline, c.reminder_time.days + ' days' AS reminder_time, c.fullname AS course_name, coalesce(s.first_name, u.first_name, u.firstName) + ' ' + coalesce(s.last_name, u.last_name, u.lastName) AS display_name, u.email AS email, c.course_url AS course_url
"""
    results = session.run(welcome_email_query)
    for record in results:
      # mark_email_queued
      mark_email_queued(record['auth0_key'], record['e_c'], 'welcome_email_sent')
      
      tmpl_vars = {
        'course_name': record['course_name'],
        'deadline': record['deadline'].iso_format()[:10],
        'time_est': record['time_est'],
        'reminder_time': record['reminder_time'],
        'display_name': record['display_name'],
        'course_url': record['course_url']
      }
      send_email('welcome', 'Neo4j GraphAcademy <devrel@neo4j.com>', record['email'], 'Welcome to the GraphAcademy course: %s' % (tmpl_vars['course_name']), tmpl_vars)
      mark_email_sent(record['auth0_key'], record['e_c'], 'welcome_email_sent')


def email_congrats_messages():
    session = db_driver.session()

    # cypher query for email
    congrats_email_query = """
MATCH (u:User)-[:ENROLLED_IN]->(s:StudentEnrollment {active:true})-[:IN_CLASS]-(c:TrainingClass),
(s)<-[:INDICATES_COMPLETION]-(coc:Certificate)
WHERE EXISTS (c.congrats_email_template)
AND NOT EXISTS (s.congrats_email_sent)
AND EXISTS (s.completed_date)
AND NOT u.email IS NULL
RETURN u.auth0_key AS auth0_key, s.createdAt AS e_c, datetime( {epochMillis: s.createdAt}) AS enrollment_created_at, c.congrats_email_template AS template, c.fullname AS course_name, coalesce(s.first_name, u.first_name, u.firstName) + ' ' + coalesce(s.last_name, u.last_name, u.lastName) AS display_name, u.email AS email, c.course_url AS course_url, coc.issued_at AS cert_issued_date, coc.certificate_number AS cert_number, coc.certificate_hash AS cert_hash
"""
    results = session.run(congrats_email_query)
    for record in results:
      # mark_email_queued
      mark_email_queued(record['auth0_key'], record['e_c'], 'congrats_email_sent')
      
      tmpl_vars = {
        'course_name': record['course_name'],
        'display_name': record['display_name'],
        'cert_issued_date': record['cert_issued_date'],
        'cert_number': record['cert_number'],
        'cert_hash': record['cert_hash'],
        'cert_url': 'https://graphacademy.neo4j.com/training/certificates/%s.pdf' % (record['cert_hash']),
        'course_url': record['course_url']
      }
      send_email(record['template'], 'Neo4j GraphAcademy <devrel@neo4j.com>', record['email'], 'Congrats on Completing the GraphAcademy course "%s"' % (tmpl_vars['course_name']), tmpl_vars)
      mark_email_sent(record['auth0_key'], record['e_c'], 'congrats_email_sent')


def send_email(template, from_line, to_address, subject, tmpl_vars):
    client = boto3.client('ses')

    with app.app_context():
      rendered_html = render_template('emails/%s.html' % template, **tmpl_vars) 
      rendered_txt = render_template('emails/%s.txt' % template, **tmpl_vars) 

    response = client.send_email(
        Source = from_line,
        SourceArn = 'arn:aws:ses:us-east-1:128916679330:identity/neo4j.com',
        Destination = {
              'ToAddresses': [ to_address ]
        },
        Message = {
            'Subject': { 'Data': subject },
            'Body': {
              'Text':
                { 'Data': rendered_txt },
              'Html':
                { 'Data': rendered_html },
            }
        }
    )
      
    

def generate_certificate(user_id, name, date, cert_number, course_name):
    #user_id = event['requestContext']['authorizer']['principalId']
    cert_hash = hashlib.sha256(str(cert_number).encode("utf-8")).hexdigest()
    cert_path = 'training/certificates'
    cert_url = 'https://graphacademy.neo4j.com/%s/%s.pdf' % (cert_path, cert_hash)
   
    r = requests.head(cert_url)
    
    if r.status_code == 200:
      return cert_url 

    with app.app_context():
        with open("static/neo4j.png", "rb") as neo4j_image:
            base_64_logo_image = base64.b64encode(neo4j_image.read())

        with open("static/certified-transparent-logo.png", "rb") as cert_image:
            base_64_cert_image = base64.b64encode(cert_image.read())

        with open("static/emil-signature.png", "rb") as sig_image:
            base_64_sig_image = base64.b64encode(sig_image.read())

        with open("static/grid_graph.png", "rb") as bg_image:
            base_64_bg_image = base64.b64encode(bg_image.read())

        rendered = render_template('certificate_completion.html',
                                   base_64_logo_image=base_64_logo_image.decode("utf-8"),
                                   base_64_cert_image=base_64_cert_image.decode("utf-8"),
                                   base_64_sig_image=base_64_sig_image.decode("utf-8"),
                                   base_64_bg_image=base_64_bg_image.decode("utf-8"),
                                   certificate_number=cert_number,
                                   course_name=course_name,
                                   date=date,
                                   name=name)

        local_html_file_name = "/tmp/{file_name}.html".format(file_name=user_id)
        with open(local_html_file_name, "wb") as file:
            file.write(rendered.encode('utf-8'))

        local_pdf_file_name = "/tmp/{file_name}.pdf".format(file_name=user_id)
        wkhtmltopdf(local_html_file_name, local_pdf_file_name)
        pdf_location = "{certificate_path}/{certificate_hash}.pdf".format(certificate_path=cert_path,certificate_hash=cert_hash)

        s3 = boto3.client('s3')
        with open(local_pdf_file_name, 'rb') as data:
            s3.put_object(ACL="public-read", Body=data, Bucket=BUCKET_NAME, Key=pdf_location)

        return "https://{bucket_name}/{pdf_location}".format(bucket_name=BUCKET_NAME,
                                                         pdf_location=pdf_location)


def generate_pdf_location(event):
    return "certificates/{certificate_hash}.pdf".format(certificate_hash=generate_certificate_hash(event))


def generate_certificate_hash(event):
    unhashed_key = "{0}-{1}-{2}".format(event["user_id"], event["test_id"], event["auth0_key"])
    return hashlib.sha256(unhashed_key.encode("utf-8")).hexdigest()
