from device import app
from device.core.config import Config

debug = True

if __name__ == '__main__':
    if debug:
        app.run(
            use_debugger=True,
            use_reloader=True,
            passthrough_errors=True,
            port=Config.get("connection", 'internal_port'),
            host="0.0.0.0"
        )
    else:
        app.run(port=Config.get(
            "connection", 'internal_port'),
            host="0.0.0.0"
        )
