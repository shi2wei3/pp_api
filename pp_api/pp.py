from pp_api import PPapi
import argparse
import logging
import sys


def schedule(pp, args):
    j_content = pp.get_release_schedule_tasks(args.shortname)
    j_content_sorted = sorted(j_content, key=lambda k: map(int,
        k['hierarchy'].split('.')))
    for item in j_content_sorted:
        print("%s ~ %s%s%s" % (item['date_start'], item['date_finish'],
              ' ' * (len(item['hierarchy'].split('.'))*2), item['name']))

def changelog(pp, args):
    j_content = pp.get_release_schedule_changelog(args.shortname)
    for rev in j_content:
        print("revision: %s\tuser: %s\tdate: %s" % (rev['revision'], rev['user'],
              rev['date']))
        print("msg: " + rev['msg'])
        print

def latest_revision(pp, args):
    j_content = pp.get_release_schedule_changelog(args.shortname)
    if(len(j_content) < 1):
        logging.error("No revision was founded")
        sys.exit(1)
    else:
        print j_content[0]['revision']

def diff(pp, args):
    if not args.revision:
        logging.error("diff need -r revision, check it with changelog")
        sys.exit(1)
    diff = pp.get_release_schedule_diff(args.shortname, args.revision)
    f = open("diff.html", 'w')
    f.write(diff)
    f.close()

cmd_dict = {"schedule": schedule,
            "changelog": changelog,
            "latest_revision": latest_revision,
            "diff": diff}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', type=str, choices=list(cmd_dict.keys()),
                        help="subcommands")
    parser.add_argument('-n', '--shortname', type=str, dest='shortname',
                        help="release short name, eg: rhel-7-2", required=True)
    parser.add_argument('-r', '--revision', type=str, dest='revision',
                        help="release schedule revision number", required=False)
    parser.add_argument('-d', '--debug', action="store_true", dest='debug',
                        help="enable debug messages", required=False)

    args = parser.parse_args()
    if args.debug == True:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
        logging.debug("Running in debug mode")
    else:
        logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s %(message)s')
        logging.info("Running in normal mode")

    # setup pp
    pp = PPapi()
    # make api call
    cmd_dict[args.command](pp, args)

if __name__ == "__main__":
    main()
