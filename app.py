#!/usr/bin/env python3
#
# Simple visit counter application
#
#

from flask import Flask
import redis
import os

app = Flask(__name__)

rdb = redis.Redis(host='redisdb', port=6379, db=0)

@app.route('/')
def index():
    visitor = rdb.get('vcount')

    if not visitor:
        # Unable to get visitors counter, you must be first
        visitor = 1

    if not rdb.incr('vcount',amount=1):
        return "ERROR: unable to increment visitors counter!\n"

    try:
        instance = os.environ['HOSTNAME']
        return (u'Hello visitor %s, this is instance %s\n' % (visitor, os.environ['HOSTNAME']))
    except KeyError as e:
        # environment variable is not defined, returning hardcoded value
        return (u'Hello visitor %s, this is instance %s\n' % (visitor, "gremlin"))



if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=False)
