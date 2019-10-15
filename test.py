import datetime
import logging
import sys
import os
import json_logging
import flask

from zaidan import FlaskLogger

app = flask.Flask(__name__)
app.logger.disabled = True
log = logging.getLogger('werkzeug')
os.environ['WERKZEUG_RUN_MAIN'] = 'true'
log.disabled = True

logger = FlaskLogger(app, __name__, "debug", True)
logger.info("server started", {"port": 5000})


@app.route('/')
def home():
    logger.info("test log statement", {"got req": True})
    return "Hello world : " + str(datetime.datetime.now())


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(5000), use_reloader=False)
    logger.info('application started', {'port': 5000})
