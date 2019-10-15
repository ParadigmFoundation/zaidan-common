# Zaidan utilities (python)

Zaidan common utility classes/functions for the Zaidan system in python.

## Exports

Classes/functions exported by `zaidan` (PyPi package).

### `Logger` (base class)

A simple logger class that outputs a standardized JSON format.

#### Constructor
```python
def __init__(self, name: str, level: str) -> Logger
```

Create a new logger. Provide a `name` for the underlying `logging.logger` instance, and a level, for which messages below that level will be ignored.

Accepted levels are (correspond to levels from standard library `logging` module):
- `"debug"` - More verbose, specific state information.
- `"info"` - General, normal-operation information.
- `"warn"` - Warnings about extreme cases, etc.
- `"error"` - Standard errors.

No levels less than "debug" or higher than "error" (critical, etc.) are supported at this time.

#### `logger.debug`
```python
def debug(self, message: str, extra: object) -> None
```

Log an `debug` level message. Currently, `extra` fields must be provided, along with a `message` string.

#### `logger.info`
```python
def info(self, message: str, extra: object) -> None
```

Log an `info` level message. Currently, `extra` fields must be provided, along with a `message` string.

#### `logger.warn`
```python
def warn(self, message: str, extra: object) -> None
```

Log an `warn` level message. Currently, `extra` fields must be provided, along with a `message` string.

#### `logger.error`
```python
def error(self, message: str, extra: object) -> None
```

Log an `error` level message. Currently, `extra` fields must be provided, along with a `message` string.

### `FlaskLogger(Logger)`

For use with Flask web-applications. Extends the `Logger` class, so all log methods are the same.

#### Constructor
```python
def __init__(self, app: flask.App, name: str, level: str, suppress_app_logs: bool) -> FlaskLogger
```

Create a new Flask logger. Required parameters:
- `app` - The Flask application instance.
- `name` - The name of the application or logger.
- `level` - Log level (see `Logger`).
- `suppress_app_logs` - Set to `True` to suppress all flask request and werkzug logs.