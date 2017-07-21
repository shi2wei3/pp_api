from rest import RestAPI
import sys
import logging


class PPapi(RestAPI):
    def __init__(self):
        super(PPapi, self).__init__()
        self.base_url = "https://pp.engineering.redhat.com/pp-admin/api/v1/"

    def get_release_id_from_shortname(self, shortname):
        """ Get release_id from shortname """
        logging.info("Getting content_id from shortname %s" % shortname)
        url = self.base_url + "releases/?shortname=%s" % shortname
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
        url = self.base_url + "releases/%s/schedule-tasks/" % release_id
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
        url = self.base_url + "releases/%s/schedule-changelog/" % release_id
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
        url = self.base_url + "releases/%s/schedule-diff/?revision=%s" \
                              % (release_id, revision)
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
