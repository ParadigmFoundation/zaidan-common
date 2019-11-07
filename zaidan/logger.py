import json_logging
import json
import traceback
from datetime import datetime
import copy
import sys
import os
import logging

import json_logging as jl


class Logger():
    """
    A basic JSON logger for non-web server applications.
    """

    levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARN,
        "error": logging.ERROR
    }

    def __init__(self, name="logger", level="info"):
        """
        Create a new logger.

        :param name: The name of the logger (printed with each output).
        :param level: Minimum log level to output (see Logger.levels).
        """
        if level not in Logger.levels.keys():
            raise Exception("invalid log level (see Logger.levels)")

        jl.ENABLE_JSON_LOGGING = True
        jl.init_non_web(custom_formatter=Format)

        self.name = name
        self.lg = BaseLogger(name)
        self.lg.setLevel(Logger.levels[level])
        self.lg.addHandler(logging.StreamHandler(sys.stdout))

    def debug(self, message: str, fields={}):
        """
        Print a debug log.

        :param message: A description of the event.
        :param fields: Additional fields with relevant data.
        """
        self.lg.debug(message, extra=fields)

    def info(self, message: str, fields={}):
        """
        Print an info log.

        :param message: A description of the event.
        :param fields: Additional fields with relevant data.
        """
        self.lg.info(message, extra=fields)

    def warn(self, message: str, fields={}):
        """
        Print a warning log.

        :param message: A description of the warning.
        :param fields: Additional fields with relevant data.
        """
        self.lg.warn(message, extra=fields)

    def error(self, message: str, fields={}):
        """
        Print an error log.

        :param message: A description of the error.
        :param fields: Additional fields with relevant data.
        """
        self.lg.error(message, extra=fields)


class FlaskLogger(Logger):
    """
    Logger for flask web applications.
    """

    def __init__(self, app, name="flask-logger", level="info", suppress_app_logs=True):
        """
        Initialize a new flask logger.

        :param app: The flask application object.
        :param name: The name of the logger (printed with each output).
        :param level: Minimum log level to output (see FlaskLogger.levels).
        """
        if level not in FlaskLogger.levels.keys():
            raise Exception("invalid log level (see FlaskLogger.levels)")

        jl.ENABLE_JSON_LOGGING = True
        jl.init_flask(custom_formatter=Format)
        jl.init_request_instrument(app)

        if suppress_app_logs:
            logging.getLogger("flask-request-logger").disabled = True
            app.logger.disabled = True
            logging.getLogger('werkzeug').disabled = True
            os.environ['WERKZEUG_RUN_MAIN'] = 'true'

        self.name = name
        self.lg = BaseLogger(name)
        self.lg.setLevel(Logger.levels[level])
        self.lg.addHandler(logging.StreamHandler(sys.stdout))

#####################################
# HELPER IMPLEMENTATIONS BELOW HERE #
#####################################


class Format(logging.Formatter):

    def get_exc_fields(self, record):
        if record.exc_info:
            exc_info = self.format_exception(record.exc_info)
        else:
            exc_info = record.exc_text
        return {"exc_info": exc_info}

    @classmethod
    def format_exception(cls, exc_info):
        return ''.join(traceback.format_exception(*exc_info)) if exc_info else ''

    def format(self, record):
        json_log_object = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            'logger_name': record.name,
        }

        if "extra" in record.__dict__:
            for key in record.__dict__["extra"].keys():
                json_log_object[key] = record.__dict__["extra"][key]
        else:
            return json.dumps({json_log_object})

        if hasattr(record, 'props'):
            json_log_object['data'].update(record.props)

        if record.exc_info or record.exc_text:
            json_log_object['data'].update(self.get_exc_fields(record))

        return json.dumps(json_log_object)


class BaseLogger(logging.Logger):
    def makeRecord(self, name, level, fn, lno, msg, args, exc_info,
                   func=None, extra=None, sinfo=None):
        """
        A factory method which can be overridden in subclasses to create
        specialized LogRecords.
        """
        rv = logging.LogRecord(name, level, fn, lno, msg, args, exc_info, func,
                               sinfo)

        try:
            if extra is not None:
                rv.__dict__["extra"] = {}
                for key in extra:
                    if (key in ["message", "asctime"]) or (key in rv.__dict__):
                        raise KeyError(
                            "Attempt to overwrite %r in LogRecord" % key)
                    rv.__dict__["extra"][key] = extra[key]
        except:
            pass

        return rv
