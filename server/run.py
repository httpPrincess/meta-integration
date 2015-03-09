#!/usr/bin/env python

from flask import Flask, request

app = Flask(__name__)

@app.route('/hooker/', methods=['POST'])
def incoming_notification():
    event = request.headers['User-Agent']
    print 'Event %s ' % event
    print '%r ' % request.headers
    print '%r ' % request.data
    print 'JSON content %r ' % request.get_json()
    return 'Ok'


if __name__=='__main__':
    app.run(port=7000, debug=True)
