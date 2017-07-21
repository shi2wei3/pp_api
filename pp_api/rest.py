import requests
# Disable HTTPS verification warnings.
try:
    from requests.packages import urllib3
except ImportError:
    pass
else:
    urllib3.disable_warnings()
import re
import json
import logging


class RestAPI(object):
    def __init__(self):
        self.s = requests.Session()
        headers = {"Accept": "application/json"}
        self.s.headers.update(headers)
        self.r = None

    def get(self, url, json=True):
        logging.debug("Making api get call to %s" % url)
        try:
            self.r = self.s.get(url, verify=False)
        except:
            logging.error("connection to pp failed")
        # convert response to json
        if json is True:
            return self.__json()
        else:
            return self.r.text

    def post(self, url, data):
        logging.debug("Making api post call to %s" % url)
        try:
            self.r = self.s.post(url, data=data, verify=False)
        except:
            logging.error("connection to pp failed")
        # convert response to json
        return self.__json()

    def put(self, url, data):
        logging.debug("Making api put call to %s" % url)
        try:
            self.r = self.s.put(url, data=data, verify=False)
        except:
            logging.error("connection to pp failed")
        # convert response to json
        return self.__json()

    def delete(self, url):
        logging.debug("Making api delete call to %s" % url)
        try:
            self.r = self.s.delete(url, verify=False)
        except:
            logging.error("connection to pp failed")

    def __json(self):
        json_string = re.sub(r"throw.*;\s*", "", self.r.text)
        try:
            json_obj = json.loads(json_string)
            return json_obj
        except:
            logging.error("Unable to convert string to json\n %s"
                          % json_string)
