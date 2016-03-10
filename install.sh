#!/bin/sh

test -d env || virtualenv env
. env/bin/activate
pip install gevent
pip install git+https://github.com/openprocurement/openprocurement.client.python

