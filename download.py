#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()

import time
import os.path
import logging
import socket
import subprocess
from openprocurement_client.client import Client

logger = logging.getLogger(__name__)

client_config = {
    'key': '',
    'host_url': "https://public.api.openprocurement.org",
    'api_version': '0',
    'params': {},
    'timeout': 30,
}

document_ext = ['doc', 'docx', 'pdf', 'rtf', 'txt', 'zip',
    'xls', 'xlsx', 'yaml', 'json']

def is_ascii(s):
    return all(ord(c) < 128 for c in s)

def wait_plist(plist, limit=20):
    while len(plist):
        for k in list(plist.keys()):
            if plist[k].poll() is None:
                continue
            del plist[k]
        if len(plist) < limit:
            break
        time.sleep(0.1)

def process_document(plist, tender, doc):
    ext = doc.title.rsplit('.', 1)[1]
    if ext not in document_ext:
        return

    dir_date = tender.dateModified[:10]
    dir_name = os.path.join("out", dir_date, tender.id)

    if is_ascii(doc.title):
        name = "{}_{}".format(doc.id[:4], doc.title)
    else:
        name = "{}.{}".format(doc.id, ext)
    file_name = os.path.join(dir_name, name)

    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    p = subprocess.Popen("wget -nv -O '{}' {}".format(
        file_name, doc.url), shell=True)
    plist[p.pid] = p

    wait_plist(plist)
    logger.info("Now %d procs", len(plist))


def main():
    FORMAT = '%(asctime)-15s %(levelname)s [%(name)s] %(funcName)s %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)

    client = Client(**client_config)
    socket.setdefaulttimeout(client_config['timeout'])

    try:
        offset = open('next_tender').read()
        client.params['offset'] = offset
    except:
        pass

    plist = dict()

    while True:
        tender_list = client.get_tenders()
        if not tender_list:
            break

        for t in tender_list:
            logger.info("Get tener %s %s", t.id, t.dateModified)
            try:
                tender = client.get_tender(t.id)['data']

                if 'documents' not in tender:
                    continue

                for d in tender.documents:
                    logger.info("++ Got document %s", d.title)
                    process_document(plist, t, d)

            except Exception as e:
                logger.error("Exception {}: {}".format(type(e), e))

        with open('next_tender', 'w') as f:
            f.write(client.params['offset'])


if __name__ == '__main__':
    main()
