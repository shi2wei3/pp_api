from rest import RestAPI
import logging


class PDCapi(RestAPI):
    def __init__(self):
        super(PDCapi, self).__init__()
        self.base_url = "https://pdc.engineering.redhat.com/rest_api/v1/"

    def get_releases(self, short, active):
        """ Get releases for the given product and version"""
        logging.info("Get %s releases for rhel" %
                     "active" if active == "true" else "inactive")
        url = self.base_url + "releases/?short=%s&active=%s" % (short, active)
        j_content = self.get(url)
        if self.r.status_code != 200:
            logging.error("GET releases error with code %s, text %s"
                          % (self.r.status_code, self.r.text))
            return self.r.status_code
        return j_content

    def get_compose_image_rtt_tests(self, compose, variant, arch):
        """ Get releases for the given product and version"""
        logging.info("Get compose image for %s %s %s"
                     % (compose, variant, arch))
        url = self.base_url + \
            "compose-image-rtt-tests/?compose=%s&variant=%s&arch=%s" \
            % (compose, variant, arch)
        j_content = self.get(url)
        if self.r.status_code != 200:
            logging.error("GET releases error with code %s, text %s"
                          % (self.r.status_code, self.r.text))
            return self.r.status_code
        return j_content


def main():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(message)s')
    pdc = PDCapi()
    import json
    j_content = pdc.get_releases("rhel", "rhel-6", "true")
    print json.dumps(j_content, indent=4)
    j_content = pdc.get_compose_image_rtt_tests("RHEL-7.4-20170711.0",
                                                "Server", "x86_64")
    print json.dumps(j_content, indent=4)

if __name__ == "__main__":
    main()
