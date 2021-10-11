PRINTFUL_API_KEY = "fpqjodzu-lmfy-an1o:diex-foz2kqw37pzx"
PRINTFUL_API_BASE_URL = "https://api.printful.com/"
from requests import Session
from base64 import b64encode
from urllib.parse import urljoin
from lib import 

import logging
logger = logging.getLogger()
class PrintfulClient():
  def __init__(self):
    self.api_key = PRINTFUL_API_KEY
    self.base_url = PRINTFUL_API_BASE_URL
    self.auth_header = "Basic " + b64encode(self.api_key.encode("UTF-8")).decode('UTF-8')
    self.session = Session()
    self.session.headers.update({
        "Authorization": self.auth_header
    })
  def _get(self, path):
     url = urljoin(self.base_url, path)
     with self.session as s:
      print(s.headers)
      resp = s.get(url)
      return resp
  def get_products (self, limit=20, offset=0):
    return self._get("store/products")
def handle_non_authorized():
    response = {
        "statusCode": 301,
        "headers": {
            "Location": ""
        }
    }
    return 
def get_print_form(event,context):
    try:
        userId = event['requestContext']['authorizer']['principalId']
        if not userId:
            handle_non_authorized()
        else:

    except e as Exception:
        logger.info("User not Authorized")
        handle_non_authorized()
  