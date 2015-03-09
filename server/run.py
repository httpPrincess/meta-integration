#!/usr/bin/env python
import os
from flask import Flask, request, jsonify, send_from_directory, Response
from werkzeug import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp/uploads/'


@app.route('/hooker/', methods=['POST'])
def incoming_notification():
    event = request.headers['User-Agent']
    print 'Event %s ' % event
    print '%r ' % request.headers
    print '%r ' % request.data
    print 'JSON content %r ' % request.get_json()
    return 'Ok'


@app.route('/logs/', methods=['GET'])
def get_logs():
    log_list = os.listdir(app.config['UPLOAD_FOLDER'])
    return '%s' % log_list, 200


# curl --form file=@file.log -u uploader:0x0aa localhost:7000/logs/
@app.route('/logs/', methods=['POST'])
def log_uploader():
    auth = request.authorization
    if auth is None or auth.username != 'uploader' or auth.password != '0x0aa':
        return Response('Wrong credentials', 401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'})

    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return 'Saved as %s' % filename


@app.route('/logs/<log_id>', methods=['GET'])
def get_log(log_id):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               log_id)


if __name__ == '__main__':
    app.run(port=7000, debug=True)
