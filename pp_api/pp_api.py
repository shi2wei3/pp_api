import requests
# Disable HTTPS verification warnings.
try:
    from requests.packages import urllib3
except ImportError:
    pass
else:
    urllib3.disable_warnings()
import re
import sys
import json
import logging


class PPSession(object):
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
        if json == True:
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


class PPapi(PPSession):
    def __init__(self):
        super(PPapi, self).__init__()
        self.base_url = "https://pp.engineering.redhat.com/pp-admin/api/v1/"

    def get_release_id_from_shortname(self, shortname):
        """ Get release_id from shortname """
        logging.info("Getting content_id from shortname %s" % shortname)
        url = requests.compat.urljoin(self.base_url,
                                      "releases/?shortname=%s" % shortname)
        j_content = self.get(url)
        if self.r.status_code == 404:
            logging.error("shortname " + shortname + " not found.")
            exit(self.r.status_code)
        if len(j_content) != 1:
            logging.error("get_release_id_from_shortname return " +
                          str(len(j_content)) + " releases")
            sys.exit(1)
        release_id = j_content[0]['id']
        return release_id

    def get_release_schedule_tasks(self, shortname):
        """ Get schedule_tasks for the given release"""
        logging.info("Get shortname %s" % shortname)
        release_id = self.get_release_id_from_shortname(shortname)
        url = requests.compat.urljoin(self.base_url,
                                      "releases/%s/schedule-tasks/" %
                                      release_id)
        j_content = self.get(url)
        if self.r.status_code != 200:
            logging.error("GET shortname %s error with code %s, text %s"
                          % (shortname, self.r.status_code, self.r.text))
            return self.r.status_code
        return j_content

    def get_release_schedule_changelog(self, shortname):
        """ Get schedule_changelog for the given release"""
        logging.info("Get shortname %s" % shortname)
        release_id = self.get_release_id_from_shortname(shortname)
        url = requests.compat.urljoin(self.base_url,
                                      "releases/%s/schedule-changelog/" %
                                      release_id)
        j_content = self.get(url)
        if self.r.status_code != 200:
            logging.error("GET shortname %s error with code %s, text %s"
                          % (shortname, self.r.status_code, self.r.text))
            return self.r.status_code
        return j_content

    def get_release_schedule_diff(self, shortname, revision):
        """ Get schedule_diff for the given release and given revision"""
        logging.info("Get shortname %s" % shortname)
        release_id = self.get_release_id_from_shortname(shortname)
        url = requests.compat.urljoin(self.base_url,
                                      "releases/%s/schedule-diff/?revision=%s"
                                      % (release_id, revision))
        j_content = self.get(url, json=False)
        if self.r.status_code != 200:
            logging.error("GET shortname %s error with code %s, text %s"
                          % (shortname, self.r.status_code, self.r.text))
            return self.r.status_code
        return j_content


def main():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(message)s')
    pp = PPapi()
    print pp.get_release_schedule_tasks("rhel-6-8")
    print pp.get_release_schedule_changelog("rhel-6-8")

    diff = pp.get_release_schedule_diff("rhel-6-8", "1.5")
    f = open("diff.html", 'w')
    f.write(diff)
    f.close()

if __name__ == "__main__":
    main()
