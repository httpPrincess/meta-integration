#!/usr/bin/env python
import os
from flask import Flask, request, send_from_directory, Response
from werkzeug import secure_filename
from subprocess import PIPE, Popen
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads/'

__BOOT_COMMAND__ = ['boot',
                    '--flavor', 'l8',
                    '--image', 'c18c14ff-bb66-4fc2-9085-f08b7c2efe66',
                    '--user-data', 'mysk.sh']

__STOP_COMMAND__ = ['delete']
__GET_CONSOLE_COMMAND__ = ['console-log']

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

    instance_id = get_instance_id(request.files['file'])
    log = execute_nova_command(__GET_CONSOLE_COMMAND__+[instance_id])
    if log:
        save_log(log, instance_id)

    execute_nova_command(__STOP_COMMAND__+[instance_id])
    return 'Thanks and now die'

@app.route('/logs/<log_id>', methods=['GET'])
def get_log(log_id):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               log_id)


def save_log(log, instance_id):
    filename = os.path.join(app.config['UPLOAD_FOLDER'],
                            secure_filename(instance_id))
    with open(filename, 'w+') as logfile:
        logfile.write(log)


def execute_nova_command(command):
    process = Popen(creds + command, stdout=PIPE)
    out, err = process.communicate()
    if err:
        app.logger.error('Unable to execute nova command %s [error=%s] %s',
                         command, err, out)
    return out


def get_instance_id(uploaded_file):
    json_object = json.loads(uploaded_file.read())
    return json_object['uuid']


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        app.logger.info('Creating upload folder')
        os.mkdir(app.config['UPLOAD_FOLDER'])

    with open('./creds.dat') as f:
        app.logger.info('Loading nova credentials')
        creds = json.loads(f.read())

    app.run(host='0.0.0.0', port=7000, debug=True)
