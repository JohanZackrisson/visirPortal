
#from flask import Flask, render_template
#app = Flask(__name__)
# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.

import logging
from flask import Flask, redirect, url_for, session, request, jsonify, render_template, abort
from flask_oauthlib.client import OAuth

import os

#import visir_sessions

DEV = os.environ['SERVER_SOFTWARE'].startswith('Development')

app = Flask(__name__)
    
if DEV:
    app.config.from_pyfile("settings.local.cfg")
else:
    app.config.from_pyfile("settings.cfg")
app.debug = True
app.secret_key = 'development'
oauth = OAuth(app)

google = oauth.remote_app(
    'google',
    consumer_key=app.config.get('GOOGLE_ID'),
    consumer_secret=app.config.get('GOOGLE_SECRET'),
    request_token_params={
        'scope': 'email'
    },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)

@app.route('/')
def hello():
    return render_template('base.html', language="en", page_title="main")

@app.route("/experiment")
def invalidExperiment():
    return abort(404)

@app.route("/experiment/<session>")
def experiment(session):
    return render_template("client.html")

#@app.route('/')
#def index():
#    if 'google_token' in session:
#        me = google.get('userinfo')
#        return jsonify({"data": me.data})
#    return redirect(url_for('login'))

@app.route('/auth/google')
#@app.route('/login')
def login():
    return google.authorize(callback=url_for('authorized', _external=True))

@app.route('/logout')
def logout():
    session.pop('google_token', None)
    return redirect(url_for('index'))

@app.route('/auth/google/authorized')
def authorized():
    resp = google.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    session['google_token'] = (resp['access_token'], '')
    me = google.get('userinfo')
    return jsonify({"data": me.data})

@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500

if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.config.from_pyfile("settings.local.cfg")
    app.run(debug=True)
