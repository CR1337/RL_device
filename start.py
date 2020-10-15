from device import app
from device.core.environment import Environment

debug = True

if __name__ == '__main__':
    if debug:
        app.run(
            use_debugger=True,
            use_reloader=True,
            passthrough_errors=True,
            port=Environment.get('INTERNAL_PORT'),
            host="0.0.0.0"
        )
    else:
        app.run(port=Environment.get(
            'INTERNAL_PORT'),
            host="0.0.0.0"
        )
