#!/usr/bin/env python
from babel import dates
from flask import Flask, request, Response, safe_join, render_template
import hashlib
import hmac
import json
import os
import requests
from pytz import timezone
from subprocess import PIPE, Popen
from werkzeug import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads/'
app.config['INSTANCE_SCRIPT_NAME'] = 'mysk.sh'
app.config.from_envvar('COOPER_SETTINGS', silent=True)

__NOVA_COMMAND__ = ['nova', '--insecure']
__BOOT_COMMAND__ = ['boot',
                    '--flavor', 'l8',
                    '--image', 'c18c14ff-bb66-4fc2-9085-f08b7c2efe66',
                    '--user-data', app.config['INSTANCE_SCRIPT_NAME']]

__STOP_COMMAND__ = ['delete']
__GET_CONSOLE_COMMAND__ = ['console-log']

credentials = []


def start_testing(instance_name):
    out = execute_nova_command(
        __BOOT_COMMAND__ + ['testing_%s' % instance_name])
    instance_id = extract_instance_id(out) or 'None'
    save_log('Tests are running', instance_id)


@app.route('/hooker/', methods=['POST'])
def incoming_notification():
    if not verify_signature(request):
        return 'Signature verification failed!'

    event = request.headers['X-Github-Event']
    if event != 'push':
        return 'Ignoring event %s' % event

    info = request.get_json()
    sha_of_head = info['head_commit']['id']
    start_testing(instance_name=sha_of_head)
    return 'Ok. Integration testing started'


@app.route('/docker/', methods=['POST'])
def incoming_docker_notification():
    info = request.get_json()
    if 'push_data' not in info:
        return 'Ignoring event'

    pushed_at = info['push_data']['pushed_at']
    start_testing(instance_name=pushed_at)
    callback_url = info['callback_url']
    resp = requests.post(callback_url,
                         data={'state': 'success',
                               'description': 'testing started'})
    return 'Ok. Integration testing started %s' % resp


@app.route('/logs/', methods=['GET'])
def get_logs():
    dir = app.config['UPLOAD_FOLDER']
    log_list = []
    for file_name in os.listdir(dir):
        log_list.append(
            {"name": file_name,
             "ts": os.stat(os.path.join(dir, file_name)).st_mtime}
        )
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


@app.template_filter('datetime')
def format_datetime(value):
    return dates.format_datetime(value,
                                 format='H:mm dd/MM/yy',
                                 locale='en_US',
                                 tzinfo=timezone('Europe/Berlin'))


def save_log(log, instance_id):
    filename = os.path.join(app.config['UPLOAD_FOLDER'],
                            secure_filename(instance_id))
    with open(filename, 'w+') as logfile:
        logfile.write(log)


def execute_nova_command(command):
    process = Popen(__NOVA_COMMAND__ + command, stdout=PIPE)
    out, err = process.communicate()
    if err:
        app.logger.error('Unable to execute nova command %s [error=%s] %s',
                         command, err, out)
    return out


def get_instance_id(uploaded_file):
    json_object = json.loads(uploaded_file.read())
    return json_object['uuid']


def extract_instance_id(out):
    for line in out.splitlines():
        spp = line.split('|')
        if len(spp) < 3:
            continue
        if spp[1].strip().startswith('id'):
            return spp[2].strip()
    return None


def verify_signature(incoming_request):
    signature = incoming_request.headers['X-Hub-Signature']
    alg, sig = signature.split("=")
    if alg != 'sha1':
        return False

    mac = hmac.new(os.environ['GITHUB_SECRET'],
                   msg=incoming_request.data,
                   digestmod=hashlib.sha1)
    if len(mac.hexdigest()) != len(sig):
        return False
    result = 0
    for x, y in zip(sig, mac.hexdigest()):
        result |= (x != y)
    return result == 0


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        app.logger.info('Creating upload folder')
        os.mkdir(app.config['UPLOAD_FOLDER'])

    if not os.path.exists(app.config['INSTANCE_SCRIPT_NAME']):
        app.logger.error('Please provide instance initialization script %s',
                         app.config['INSTANCE_SCRIPT_NAME'])
        exit(-1)

    if 'GITHUB_SECRET' not in os.environ:
        app.logger.error('No GitHub hook secret found in environment')
        exit(-1)

    if 'OS_TENANT_NAME' not in os.environ:
        app.logger.error('Please provide nova credentials')
        exit(-1)

    app.run(host='0.0.0.0', port=7000, debug=True)
