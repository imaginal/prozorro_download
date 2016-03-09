#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()

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

document_ext = ['doc', 'docx', 'pdf', 'rtf', 'txt', 'yaml']


def process_document(tender, doc):
    ext = doc.title.rsplit('.', 1)[1]
    if ext not in document_ext:
        return

    dir_date = tender.dateModified[:10]
    dir_name = os.path.join("out", dir_date, tender.id)

    name = "{}_{}".format(doc.id[:4], doc.title)
    file_name = os.path.join(dir_name, name)

    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    subprocess.call("wget -nv -O '{}' {}".format(
        file_name, doc.url), shell=True)


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
                    process_document(t, d)

            except Exception as e:
                logger.error("Exception {}: {}".format(type(e), e))

        with open('next_tender', 'w') as f:
            f.write(client.params['offset'])


if __name__ == '__main__':
    main()
