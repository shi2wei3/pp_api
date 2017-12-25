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
import smtplib
import logging
import argparse
import mysql.connector as mariadb
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from .pdc_api import PDCapi


class HTTP_helper(object):
    def __init__(self):
        self.s = requests.Session()
        headers = {"Accept": "text/html"}
        self.s.headers.update(headers)
        self.r = None

    def __get(self, url):
        logging.debug("Making api get call to %s" % url)
        try:
            self.r = self.s.get(url, verify=False)
        except:
            logging.error("connection failed")
        soup = BeautifulSoup(self.r.text, 'lxml')
        for script in soup(["script", "style"]):
            script.extract()
        return soup.get_text()

    def get_latest_released_image(self, x):
        release_url = "http://download-node-02.eng.bos.redhat.com/rel-eng/"

        phase = {"Alpha": 1,
                 "Beta": 2,
                 "Snapshot": 3,
                 "RC": 4}

        html_text = self.__get(release_url)
        m = re.findall(r"\s*(RHEL-" + str(x) +
                       "\.\d+-(?:Alpha|Beta|RC|Snapshot)-\d+\.\d+).*",
                       html_text)
        L = sorted(m, key=lambda k: (k.split('-')[1].split('.')[0],
                                     k.split('-')[1].split('.')[1],
                                     phase[k.split('-')[2]],
                                     k.split('-')[3].split('.')[0],
                                     k.split('-')[3].split('.')[1]))
        print(L[-1])
        html_text = self.__get(release_url + L[-1] +
                               "/compose/Server/x86_64/images/")
        m = re.findall(r"\s*(rhel-guest-image-.*.x86_64.qcow2)\s+.*",
                       html_text)
        print(m[0].encode('ascii', 'ignore'))

    def get_released_image(self, y_stream):
        release_url = "http://download-node-02.eng.bos.redhat.com/rel-eng/"

        phase = {"Alpha": 1,
                 "Beta": 2,
                 "Snapshot": 3,
                 "RC": 4}

        html_text = self.__get(release_url)
        m = re.findall(r"\s*(RHEL-" + y_stream +
                       "-(?:Alpha|Beta|RC|Snapshot)-\d+\.\d+).*",
                       html_text)
        if (len(m) == 0):
            return
        L = sorted(m, key=lambda k: (phase[k.split('-')[2]],
                                     k.split('-')[3].split('.')[0],
                                     k.split('-')[3].split('.')[1]))
        html_text = self.__get(release_url + L[-1] +
                               "/compose/Server/x86_64/images/")
        m = re.findall(r"\s*(rhel-guest-image-.*.x86_64.qcow2)\s+.*",
                       html_text)
        if (len(m) == 0):
            return
        else:
            return [L[-1], m[0].encode('ascii', 'ignore')]

    def get_latest_update_image(self, x):
        release_url = "http://download-node-02.eng.bos.redhat.com/rel-eng/"
        update_url = release_url + "updates/"

        html_text = self.__get(update_url)
        m = re.findall(r"\s*(RHEL-" + str(x) + "\.\d+).*", html_text)
        L1 = sorted(m, key=lambda k: (k.split('-')[1].split('.')[0],
                                      k.split('-')[1].split('.')[1]))
        for max_y_stream in reversed(L1):
            html_text = self.__get(update_url + max_y_stream + "/")
            m = re.findall(r"\s*(" + max_y_stream + "-Update-\d+\.\d+).*",
                           html_text)
            if len(m) == 0:
                continue
            L2 = sorted(m, key=lambda k: (k.split('-')[3].split('.')[0],
                                          k.split('-')[3].split('.')[1]))
            for max_revision in reversed(L2):
                html_text = self.__get(update_url + max_y_stream + "/" +
                                       max_revision +
                                       "/compose/Server/x86_64/images/")
                n = re.findall(r"\s*(rhel-guest-image-.*.x86_64.qcow2)\s+.*",
                               html_text)
                if len(n) > 0:
                    print(max_revision)
                    print(n[0].encode('ascii', 'ignore'))
                    break
            break

    def get_update_image(self, y_stream):
        release_url = "http://download-node-02.eng.bos.redhat.com/rel-eng/"
        update_url = release_url + "updates/"

        html_text = self.__get(update_url + y_stream + "/")
        m = re.findall(r"\s*(" + y_stream + "-Update-\d+\.\d+).*",
                       html_text)
        if len(m) == 0:
            return
        L = sorted(m, key=lambda k: (k.split('-')[3].split('.')[0],
                                     k.split('-')[3].split('.')[1]))
        for max_revision in reversed(L):
            html_text = self.__get(update_url + y_stream + "/" + max_revision +
                                   "/compose/Server/x86_64/images/")
            n = re.findall(r"\s*(rhel-guest-image-.*.x86_64.qcow2)\s+.*",
                           html_text)
            if len(n) > 0:
                return [max_revision, n[0].encode('ascii', 'ignore')]
        return


def get_active_rhel_releases(args):
    pdc = PDCapi()
    j_content = pdc.get_releases("rhel", "true")
    if(len(j_content) < 1):
        logging.error("No releases was founded")
        sys.exit(1)
    else:
        return [i['release_id'] for i in j_content['results']]


def get_builds(args):
    helper = HTTP_helper()
    if args is not None and args.version is not None:
        print(helper.get_released_image(args.version))
        print(helper.get_update_image('RHEL-' + args.version))
        return

    active_releases = get_active_rhel_releases(None)
    print("=== Active RHEL releases ===")
    for i in active_releases:
        print(i)
    exclude_udpates = ['rhel-5.11-updates', 'rhel-6-updates']
    release_pattern = re.compile(r"rhel-\d+\.\d+$")
    update_pattern = re.compile(r"rhel-\d+\.\d+-updates$")
    filtered_releases = filter(release_pattern.match, active_releases)
    filtered_updates = list(set(filter(update_pattern.match,
                                       active_releases)) -
                            set(exclude_udpates))
    L = []
    for i in filtered_releases:
        L1 = [i]
        release_info = helper.get_released_image(i.split('-')[1])
        if release_info is not None:
            L1.extend(release_info)
        else:
            L1.extend([None, None])
        L.append(L1)
    for i in filtered_updates:
        L1 = [i]
        update_arg = '-'.join(i.split('-')[0:2]).upper()
        update_info = helper.get_update_image(update_arg)
        if update_info is not None:
            L1.extend(update_info)
        else:
            L1.extend([None, None])
        L.append(L1)
    return L


def sync(args):
    builds = get_builds(None)
    print("=== Realtime data ===")
    for i in builds:
        print(i)
    try:
        mariadb_connection = mariadb.connect(host='10.8.184.8', user='wshi',
                                             password='redhatqas1',
                                             database='REDHAT')
    except mariadb.Error as err:
        print("Error with DB connection: {}".format(err))
        sys.exit(1)
    cursor = mariadb_connection.cursor()
    cursor.execute("SELECT release_name, release_version, build_name "
                   "FROM RHEL_GUEST_IMAGE WHERE 1 = %s", ("1"))
    db_builds = []
    print("=== DB data ===")
    for name, version, build in cursor:
        row = [name, version, build]
        db_builds.append(row)
        print(row)
    update_list = []
    insert_list = []
    for build in builds:
        logging.debug("=== Enter loop ===")
        logging.debug(build)
        if build[1] is None:
            logging.debug("Skip None build: %s" % str(build))
            continue
        elif build[0] not in [i[0] for i in db_builds]:
            insert_list.append(build)
            logging.debug("Insert new build to DB: %s" % str(build))
        elif build[1] != [i[1] for i in db_builds if i[0] == build[0]][0]:
            update_list.append(build)
            logging.debug("Update existing build to DB: %s" % str(build))
            logging.debug("--- diff in realtime --- %s" % str(build[1]))
            tmp_db = [i[1] for i in db_builds if i[0] == build[0]][0]
            logging.debug("--- diff in DB --- %s" % str(tmp_db))
        else:
            logging.debug("Already in DB: %s" % str(build))
    print("=== Update list ===")
    for i in update_list:
        print(i)
        args.content = "Update: " + str(i) + "\n"
        args.build = i[2].encode('ascii', 'ignore')
        send_mail(args)
    print("=== Insert list ===")
    for i in insert_list:
        print(i)
        args.content = "Insert: " + str(i) + "\n"
        args.build = i[2].encode('ascii', 'ignore')
        send_mail(args)
    try:
        for i in update_list:
            cursor.execute("UPDATE RHEL_GUEST_IMAGE "
                           "SET release_version=%s,build_name=%s "
                           "WHERE release_name=%s", (i[1], i[2], i[0]))
        for i in insert_list:
            cursor.execute("INSERT INTO RHEL_GUEST_IMAGE "
                           "(release_name,release_version,build_name) "
                           "VALUES (%s,%s,%s)", (i[0], i[1], i[2]))
        mariadb_connection.commit()
    except mariadb.Error as error:
        print("Error with DB operations: {}".format(error))
        mariadb_connection.rollback()
        sys.exit(1)
    mariadb_connection.close()


def send_mail(args):
    mail_server = "smtp.corp.redhat.com"
    mail_from = "wshi@redhat.com"
    mail_to = "wshi@redhat.com"

    if "content" not in vars(args):
        args.content = ""
    if "build" not in vars(args):
        args.build = ""
    msg = MIMEText(args.content, _subtype='html', _charset='utf-8')
    msg["Subject"] = "New build {0} founded!".format(args.build)
    msg["From"] = mail_from
    msg["To"] = mail_to

    try:
        server = smtplib.SMTP()
        server.connect(mail_server)
        server.sendmail(mail_from, mail_to, msg.as_string())
        server.close()
    except Exception as e:
        print(str(e))


cmd_dict = {"releases": get_active_rhel_releases,
            "builds": get_builds,
            "sync": sync,
            "email": send_mail}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', type=str, choices=list(cmd_dict.keys()),
                        help="subcommands")
    parser.add_argument('-n', '--release_version', type=str, dest='version',
                        help="release version, eg: 7.2", required=False)
    parser.add_argument('-d', '--debug', action="store_true", dest='debug',
                        help="enable debug messages", required=False)

    args = parser.parse_args()
    if args.debug is True:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s %(message)s')
        logging.debug("Running in debug mode")
    else:
        logging.basicConfig(level=logging.WARNING,
                            format='%(asctime)s %(levelname)s %(message)s')
        logging.info("Running in normal mode")

    cmd_dict[args.command](args)

if __name__ == "__main__":
    main()
