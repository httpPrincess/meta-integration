#!/usr/bin/env python
import os
from flask import Flask, request, send_from_directory, Response
from werkzeug import secure_filename
from subprocess import call, PIPE, Popen
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads/'

__BOOT_COMMAND__ = [u'boot', u'--flavor', u'l8', u'--image',
                    u'c18c14ff-bb66-4fc2-9085-f08b7c2efe66', u'--user-data',
                    u'mysk.sh']
creds = []


@app.route('/hooker/', methods=['POST'])
def incoming_notification():
    # event = request.headers['User-Agent']
    # print 'Event %s ' % event
    # print '%r ' % request.headers
    # print '%r ' % request.data
    # print 'JSON content %r ' % request.get_json()
    execute_nova_command(__BOOT_COMMAND__ + ['integration_testing_instance'])

    # github does not have to about the errors
    return 'Ok'


@app.route('/logs/', methods=['GET'])
def get_logs():
    log_list = os.listdir(app.config['UPLOAD_FOLDER'])
    return '%s' % log_list, 200


@app.route('/logs/', methods=['POST'])
def log_uploader():
    auth = request.authorization
    if auth is None or auth.username != 'uploader' or auth.password != '0x0aa':
        return Response('Wrong credentials', 401,
                        {'WWW-Authenticate': 'Basic realm="Login Required"'})

    uploaded_file = request.files['file']
    json_object = json.loads(uploaded_file.read())
    instance_id = json_object['uuid']
    log = execute_nova_command(['console-log', instance_id])
    if log:
        save_log(log, instance_id)

    execute_nova_command(['stop', instance_id])
    return 'Thanks and now die'

@app.route('/logs/<log_id>', methods=['GET'])
def get_log(log_id):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               log_id)


def save_log(log, instance_id):
    filename = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(
        instance_id))
    with open(filename, 'w+') as logfile:
        logfile.write(log)


def kill_instance(instance_id):
    execute_nova_command(['stop', instance_id])


def execute_nova_command(command):
    process = Popen(creds + command, stdout=PIPE)
    out, err = process.communicate()
    if err != 0:
        app.logger.error('Unable to execute nova command %s', command)
    return out


if __name__ == '__main__':
    value = open('./creds.dat').read()
    creds = json.loads(value)
    app.run(port=7000, debug=True)
