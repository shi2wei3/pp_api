import requests

# Disable HTTPS verification warnings.
try:
    from requests.packages import urllib3
except ImportError:
    pass
else:
    urllib3.disable_warnings()
import os
import re
import sys
import smtplib
import logging
import argparse
import mysql.connector as mariadb
import openstack
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from .pp_api import PPapi

jenkins_job_trigger = "java -jar ~/Downloads/jenkins-cli.jar -noCertificateCheck -s " \
                      "https://xen-jenkins.rhev-ci-vms.eng.rdu2.redhat.com/ build rhel-guest-image-runtest -p 'NVR=%s'"


class HTTPHelper(object):
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

        phase = {"DevelPhaseExit": 1,
                 "Alpha": 2,
                 "Beta": 3,
                 "Snapshot": 4,
                 "RC": 5}

        html_text = self.__get(release_url)
        m = re.findall(r"\s*(RHEL-" + str(x) +
                       "\.\d+-(?:DevelPhaseExit|Alpha|Beta|RC|Snapshot)-\d+\.\d+).*",
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

        phase = {"DevelPhaseExit": 1,
                 "Alpha": 2,
                 "Beta": 3,
                 "Snapshot": 4,
                 "RC": 5}

        html_text = self.__get(release_url)
        m = re.findall(r"\s*(RHEL-" + y_stream +
                       "-(?:DevelPhaseExit|Alpha|Beta|RC|Snapshot)-\d+\.\d+).*",
                       html_text)
        if len(m) == 0:
            return
        L = sorted(m, key=lambda k: (phase[k.split('-')[2]],
                                     k.split('-')[3].split('.')[0],
                                     k.split('-')[3].split('.')[1]))
        if y_stream[0] == "8":
            image_rel_path = "/compose/BaseOS/x86_64/images/"
        else:
            image_rel_path = "/compose/Server/x86_64/images/"
        html_text = self.__get(release_url + L[-1] + image_rel_path)
        m = re.findall(r"\s*(rhel-guest-image-.*.x86_64.qcow2)\s+.*",
                       html_text)
        if len(m) == 0:
            return
        else:
            build_name = m[0].encode('ascii', 'ignore')
            return [L[-1], build_name, release_url + L[-1] + image_rel_path + build_name]

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
                build_name = n[0].encode('ascii', 'ignore')
                return [max_revision, build_name,
                        update_url + y_stream + "/" + max_revision + "/compose/Server/x86_64/images/" + build_name]
        return

    def get_nightly_image(self, y_stream):
        base_url = "http://download-node-02.eng.bos.redhat.com/nightly/"
        nightly_url = base_url + y_stream

        revision = self.__get(nightly_url +
                              "/COMPOSE_ID").lstrip().rstrip()
        html_text = self.__get(nightly_url +
                               "/compose/BaseOS/x86_64/images/")
        n = re.findall(r"\s*(rhel-guest-image-.*.x86_64.qcow2)\s+.*",
                       html_text)
        if len(n) > 0:
            build_name = n[0].encode('ascii', 'ignore')
            return [revision, build_name,
                    nightly_url + "/compose/BaseOS/x86_64/images/" + build_name]


def get_rhel_eng_releases():
    pp = PPapi()
    j_content = pp.get_releases("rhel", "3,4,5")
    if len(j_content) < 1:
        logging.error("No releases was founded")
        sys.exit(1)
    else:
        return [i['shortname'] for i in j_content]


def get_rhel_update_releases():
    pp = PPapi()
    j_content = pp.get_releases("rhel", "6")
    if len(j_content) < 1:
        logging.error("No releases was founded")
        sys.exit(1)
    else:
        return [i['shortname'] for i in j_content]


def get_builds(args=None):
    helper = HTTPHelper()
    if args is not None and args.version is not None:
        print(helper.get_released_image(args.version))
        print(helper.get_update_image('RHEL-' + args.version))
        return

    rhel_eng_releases = get_rhel_eng_releases()
    rhel_update_releases = get_rhel_update_releases()
    print("=== rhel-eng releases ===")
    for i in rhel_eng_releases:
        print(i)
    print("=== update releases ===")
    for i in rhel_update_releases:
        print(i)
    release_pattern = re.compile(r"rhel-\d+\-\d+$")
    filtered_releases = list(filter(release_pattern.match, rhel_eng_releases))
    filtered_updates = list(filter(release_pattern.match, rhel_update_releases))
    L = []
    for i in filtered_releases:
        j = re.sub(r'^(rhel-[0-9]+)-', r'\1.', i)
        L1 = [j]
        release_info = helper.get_released_image(j.split('-')[1])
        if release_info is not None:
            L1.extend(release_info)
        else:
            L1.extend([None, None])
        L.append(L1)
    for i in filtered_updates:
        j = re.sub(r'^(rhel-[0-9]+)-', r'\1.', i)
        L1 = [j + "-updates"]
        update_arg = j.upper()
        update_info = helper.get_update_image(update_arg)
        if update_info is not None:
            L1.extend(update_info)
        else:
            L1.extend([None, None])
        L.append(L1)

    nightly_arg = "latest-RHEL-8"
    nightly_info = helper.get_nightly_image(nightly_arg)
    L1 = [nightly_arg]
    print(nightly_info)
    if nightly_info is not None:
        L1.extend(nightly_info)
    else:
        L1.extend([None, None])
    L.append(L1)

    return L


def sync(args):
    builds = get_builds()
    print("=== Realtime data ===")
    for i in builds:
        print(i)
    try:
        mariadb_connection = mariadb.connect(host='10.8.242.130', user='wshi',
                                             password='redhatqas1',
                                             database='REDHAT')
    except mariadb.Error as err:
        print(("Error with DB connection: {}".format(err)))
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
        elif build[2] != [i[2] for i in db_builds if i[1] == build[1]][0]:
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
        filename = download_file(i[3])
        upload_to_rhos(filename)
        if os.path.exists(filename):
            os.remove(filename)
        send_mail(args)
        os.system(jenkins_job_trigger % args.build)
    print("=== Insert list ===")
    for i in insert_list:
        print(i)
        args.content = "Insert: " + str(i) + "\n"
        args.build = i[2].encode('ascii', 'ignore')
        filename = download_file(i[3])
        upload_to_rhos(filename)
        if os.path.exists(filename):
            os.remove(filename)
        send_mail(args)
        os.system(jenkins_job_trigger % args.build)
    try:
        for i in update_list:
            cursor.execute("UPDATE RHEL_GUEST_IMAGE "
                           "SET release_version=%s,build_name=%s,build_url=%s,last_update=sysdate() "
                           "WHERE release_name=%s", (i[1], i[2], i[3], i[0]))
        for i in insert_list:
            cursor.execute("INSERT INTO RHEL_GUEST_IMAGE "
                           "(release_name,release_version,build_name,build_url,last_update) "
                           "VALUES (%s,%s,%s,%s,sysdate())", (i[0], i[1], i[2], i[3]))
        mariadb_connection.commit()
    except mariadb.Error as error:
        print(("Error with DB operations: {}".format(error)))
        mariadb_connection.rollback()
        sys.exit(1)
    mariadb_connection.close()


def download_file(url):
    local_filename = '/tmp/' + url.split('/')[-1]
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
    return local_filename


def upload_to_rhos(filename):
    # Connnection attributes
    auth_url = 'https://ci-rhos.centralci.eng.rdu2.redhat.com:13000/v2.0'
    project_name = 'xen-jenkins'
    username = 'xenqe'
    password = ''

    # Initialize cloud
    conn = openstack.connect(auth_url=auth_url,
                              project_name=project_name,
                              username=username,
                              password=password)

    name = filename.split('/')[-1]
    short_name = re.findall(r'^rhel-guest-image-\d+\.\d+', name)[0]
    iter = conn.image.images(visibility="private")
    for i in iter:
        if i.name.startswith(short_name):
            conn.image.delete_image(i.id)

    # Build the image attributes
    #image_attrs = {
    #    'name': filename.split('/')[-1],
    #    'filename': filename,
    #    'disk_format': 'qcow2',
    #    'container_format': 'bare',
    #    'wait': True
    #}
    image_attrs = {
        'name': name,
        'data': open(filename, 'r'),
        'disk_format': 'qcow2',
        'container_format': 'bare',
        'hw_rng_model': 'virtio'
    }

    conn.image.upload_image(**image_attrs)


def send_mail(args):
    mail_server = "smtp.corp.redhat.com"
    mail_from = "wshi@redhat.com"
    mail_to = "wshi@redhat.com, wshi@redhat.com"

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


cmd_dict = {"builds": get_builds,
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
