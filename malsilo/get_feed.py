from connectors.core.connector import get_logger, ConnectorError

logger = get_logger('malsilo')

import requests
import csv
import re
from datetime import datetime
from contextlib import closing

TYPE_IPv4 = 'ipv4'
TYPE_URL = 'url'
TYPE_DOMAIN = 'domain'


def get_feed(type, url, verify_ssl):
    ip_list = []
    keys = []
    found_keys = False
    generatedAt = None
    with closing(
            requests.get(url, verify=verify_ssl, stream=True)) as r:
        f = (line.decode('utf-8') for line in r.iter_lines())
        reader = csv.reader(f, delimiter=',', quotechar='"')
        for row in reader:
            # there are 5 headers. other lines have text content. excluding
            if len(row) >= 5:
                if not found_keys:
                    # the first would keys row
                    for key in row:
                        key = key.replace('#', '')
                        key = key.strip()
                        if key == 'ipv4:port' or key == 'domain' or key == 'url':
                            key = 'value'
                        keys.append(key)
                    found_keys = True
                else:
                    ip_detail = {'type': type}
                    for count in range(len(keys)):
                        ip_detail[keys[count]] = row[count]
                    ip_list.append(ip_detail)
            else:
                # try to parse for data generation timestamp
                for item in row:
                    if "Dataset generated @" in item:
                        generatedAt = re.sub('.*Dataset generated @([0-9 :-]*) \(.*', '\\1', item).strip()
                        print(generatedAt)
    try:
        if generatedAt:
            generatedAt = datetime.strptime(generatedAt, '%Y-%m-%d %H:%M:%S').timestamp()
    except Exception as e:
        raise ConnectorError("Error parsing the feed generation timestamp for the IP Feed URL: " + str(e))
    return {"generatedAt": generatedAt, "feed": ip_list}


def get_ipv4_feed(config, params):
    url = config.get('ipv4_url', 'https://malsilo.gitlab.io/feeds/dumps/ip_list.txt')
    verify_ssl = config.get('verify_ssl', True)
    return get_feed(TYPE_IPv4, url, verify_ssl)


def get_url_feed(config, params):
    url = config.get('url_url', 'https://malsilo.gitlab.io/feeds/dumps/url_list.txt')
    verify_ssl = config.get('verify_ssl', True)
    return get_feed(TYPE_URL, url, verify_ssl)

def get_domain_feed(config, params):
    url = config.get('domain_url', 'https://malsilo.gitlab.io/feeds/dumps/domain_list.txt')
    verify_ssl = config.get('verify_ssl', True)
    return get_feed(TYPE_DOMAIN, url, verify_ssl)
