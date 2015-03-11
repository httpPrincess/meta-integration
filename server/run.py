#!/usr/bin/env python
import hmac
import os
from flask import Flask, request, Response, safe_join, render_template
from werkzeug import secure_filename
from subprocess import PIPE, Popen
import json
import hashlib

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads/'
app.config['INSTANCE_SCRIPT_NAME'] = 'mysk.sh'
app.config['NOVA_CREDENTIALS_FILE'] = 'creds.dat'
app.config.from_envvar('COOPER_SETTINGS', silent=True)

__BOOT_COMMAND__ = ['boot',
                    '--flavor', 'l8',
                    '--image', 'c18c14ff-bb66-4fc2-9085-f08b7c2efe66',
                    '--user-data', app.config['INSTANCE_SCRIPT_NAME']]

__STOP_COMMAND__ = ['delete']
__GET_CONSOLE_COMMAND__ = ['console-log']

credentials = []


@app.route('/hooker/', methods=['POST'])
def incoming_notification():
    event = request.headers['X-Github-Event']
    signature = request.headers['X-Hub-Signature']
    if not verify_signature(signature, request.data):
        return 'Signature verification failed!'

    if event == 'ping':
        return 'pong'

    if event == 'push':
        info = request.get_json()
        sha_of_head = info['head_commit']['id']

        execute_nova_command(
            __BOOT_COMMAND__ + ['testing_%s' % sha_of_head])
        return 'Ok. Integration testing started'

    return 'Unknown event %s' % event


@app.route('/logs/', methods=['GET'])
def get_logs():
    log_list = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('logs.html', logs=log_list)


@app.route('/logs/', methods=['POST'])
def log_uploader():
    auth = request.authorization
    if auth is None or auth.username != 'uploader' or auth.password != '0x0aa':
        return Response('Wrong credentials', 401,
                        {'WWW-Authenticate': 'Basic realm="Login Required"'})

    instance_id = get_instance_id(request.files['file'])
    log = execute_nova_command(__GET_CONSOLE_COMMAND__ + [instance_id])
    if log:
        save_log(log, instance_id)

    execute_nova_command(__STOP_COMMAND__ + [instance_id])
    return 'Thanks and now die'


@app.route('/logs/<log_id>', methods=['GET'])
def get_log(log_id):
    filename = safe_join(app.config['UPLOAD_FOLDER'], log_id)
    with open(filename, 'rb') as fd:
        content = fd.read()
    return render_template('log.html', instance_id=log_id, content=content)


def save_log(log, instance_id):
    filename = os.path.join(app.config['UPLOAD_FOLDER'],
                            secure_filename(instance_id))
    with open(filename, 'w+') as logfile:
        logfile.write(log)


def execute_nova_command(command):
    process = Popen(credentials + command, stdout=PIPE)
    out, err = process.communicate()
    if err:
        app.logger.error('Unable to execute nova command %s [error=%s] %s',
                         command, err, out)
    return out


def get_instance_id(uploaded_file):
    json_object = json.loads(uploaded_file.read())
    return json_object['uuid']


def verify_signature(signature, data):
    alg, sig = signature.split("=")
    if alg != 'sha1':
        return False
    if 'GITHUB_SECRET' not in os.environ:
        app.logger.error('No GitHub hook secret found in environment')
        return False

    mac = hmac.new(os.environ['GITHUB_SECRET'],
                   msg=data,
                   digestmod=hashlib.sha1)
    return sig == mac.hexdigest()


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        app.logger.info('Creating upload folder')
        os.mkdir(app.config['UPLOAD_FOLDER'])

    if not os.path.exists(app.config['INSTANCE_SCRIPT_NAME']):
        app.logger.error('Please provide instance initialization script %s',
                         app.config['INSTANCE_SCRIPT_NAME'])
        exit(-1)

    if not os.path.exists(app.config['NOVA_CREDENTIALS_FILE']):
        app.logger.error('Please provide nova credentials file %s',
                         app.config['NOVA_CREDENTIALS_FILE'])
        exit(-1)

    with open(app.config['NOVA_CREDENTIALS_FILE']) as f:
        credentials = json.loads(f.read())

    app.run(host='0.0.0.0', port=7000, debug=True)
