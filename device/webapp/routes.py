import sys
from datetime import datetime
from functools import wraps

from flask import (Blueprint, make_response, render_template,
                   request, send_file)
from flask_api import status

from ..core.config import Config
from ..core.fire_command import FireCommand
from ..core.fire_controller import FireController
from ..core.hardware_controller import HardwareController
from ..core.logger import Logger
from ..core.address import Address
from ..core.master_communication import MasterCommunicator
from .auth import authenticate, sign_message
from ..util.sys_time import set_system_time

api_bp = Blueprint('api_blueprint', __name__)
logger = Logger(logger_type='rest')


def authentify(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
        # TODO: do authentication
        if not authenticate(request) and not request.method == 'GET':
            logger.warning(
                f"Unauthorized request from {request.host} to {request.url}.")
            return "", status.HTTP_401_UNAUTHORIZED
        else:
            return func(*args, **kwargs)
    return wrapper


def handle_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
        except Exception:
            exc_type, exc, _ = sys.exc_info()
            content = {
                'exception_type': str(exc_type),
                'exception_args': vars(exc)
            }
            status_code = status.HTTP_400_BAD_REQUEST
            response = make_response((content, status_code))
            logger.exception(f"Exception occured in {request.url}.")
        finally:
            return response
    return wrapper


def sign_response(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        message = response.data
        response.headers['Signature'] = sign_message(message)
        return response
    return wrapper


def log(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method == 'GET':
            logger.info(f"GET Request from {request.host}: {request.args}")
        else:
            logger.info(
                f"{request.method} Request from {request.host} "
                + f"to {request.url}: {request.get_json(force=True)}"
            )
        return func(*args, **kwargs)
    return wrapper


@api_bp.route("/", methods=["GET"], endpoint='route_main')
@log
def route_main():
    return render_template(
        "index.html",
        device_id=Config.get("connection", 'device_id'),
        port=Config.get("connection", 'external_port'),
        time=datetime.now()
    )


@api_bp.route("/config", methods=["GET", "POST"], endpoint='route_config')
@authentify
@handle_exceptions
@sign_response
@log
def route_config():
    if request.method == "GET":
        if 'category' in request.args:
            if 'key' in request.args:
                value = Config.get(
                    request.args['category'],
                    request.args['key']
                )
                return {request.args['key']: value}
            else:
                response = Config.get_category(request.args['category'])
        else:
            response = Config.get_all()
    elif request.method == "POST":
        Config.update_many(request.get_json(force=True)['entries'])
        response = dict()
    return make_response(response)


@api_bp.route("/program", methods=["POST", "DELETE"], endpoint='route_program')
@authentify
@handle_exceptions
@sign_response
@log
def route_program():
    if request.method == "DELETE":
        FireController.delete_program()
    elif request.method == "POST":
        FireController.load_program(request.get_json(force=True)['commands'])

    return make_response(dict())


@api_bp.route(
    "/program/control",
    methods=["POST"], endpoint='route_program_control'
)
@authentify
@handle_exceptions
@sign_response
@log
def route_program_control():
    action = request.get_json(force=True)['action']
    if action == 'run':
        FireController.run_program()
    elif action == 'pause':
        FireController.pause_program()
    elif action == 'continue':
        FireController.continue_program()
    elif action == 'stop':
        FireController.stop_program()
    elif action == 'schedule':
        FireController.schedule_program(
            request.get_json(force=True)['schedule_time']
        )
    elif action == 'unschedule':
        FireController.unschedule_program()
    else:
        raise ValueError()

    return make_response(dict())


@api_bp.route(
    "/program/state",
    methods=["GET"], endpoint='route_program_state'
)
@authentify
@handle_exceptions
@sign_response
@log
def route_program_state():
    return make_response({'state': FireController.get_program_state()})


@api_bp.route("/fire", methods=["POST", "GET"], endpoint='route_fire')
@authentify
@handle_exceptions
@sign_response
@log
def route_fire():
    address = Address(request.get_json(force=True)['address'])
    fire_command = FireCommand(
        address=address,
        timestamp=0
    )
    fire_command.fire()
    return make_response(dict())


@api_bp.route("/fuses", methods=["GET"], endpoint='route_fuses')
@authentify
@handle_exceptions
@sign_response
@log
def route_fuses():
    return make_response(FireController.get_fuse_status())


@api_bp.route("/testloop", methods=["POST"], endpoint='route_testloop')
@authentify
@handle_exceptions
@sign_response
@log
def route_testloop():
    FireController.testloop()
    return make_response(dict())


@api_bp.route("/lock", methods=["GET", "POST"], endpoint='route_lock')
@authentify
@handle_exceptions
@sign_response
@log
def route_lock():
    if request.method == "GET":
        return make_response({'locked': HardwareController.is_locked()})
    elif request.method == "POST":
        action = request.get_json(force=True)['action']
        if action == 'lock':
            HardwareController.lock()
        elif action == 'unlock':
            HardwareController.unlock()
        else:
            raise ValueError

        return make_response(dict())


@api_bp.route("/errors", methods=["GET", "DELETE"], endpoint='route_errors')
@authentify
@handle_exceptions
@sign_response
@log
def route_errors():
    if request.method == "GET":
        response = HardwareController.errors()
    elif request.method == "DELETE":
        HardwareController.clear_error_flags()
        response = dict()
    return make_response(response)


@api_bp.route("/logs", methods=["GET"], endpoint='route_logs')
@authentify
@handle_exceptions
@sign_response
@log
def route_logs():
    response = send_file(
        Logger.get_logfiles(amount=request.args['amount']),
        attachment_filename="_".join([
            Config.get("connection", 'device_id'), "logs.zip"
        ]),
        as_attachment=True,
        mimetype="application/zip"
    )
    response.direct_passthrough = False
    return response


@api_bp.route(
    "/master-registration",
    methods=["POST", "DELETE"], endpoint='route_master_listener'
)
@authentify
@handle_exceptions
@sign_response
@log
def route_master_listener():
    if request.method == "POST":
        MasterCommunicator.register_master(
            # address=request.get_json(force=True)['address'],
            address=request.remote_addr,
            port=request.get_json(force=True)['port']
        )
        response = (
            {'device_id': Config.get("connection", 'device_id')},
            status.HTTP_202_ACCEPTED
        )
    elif request.method == "DELETE":
        MasterCommunicator.deregister_master()
        response = dict()

    return make_response(response)


@api_bp.route(
    "/system-time", methods=["GET", "POST"],
    endpoint='route_system_time'
)
@authentify
@handle_exceptions
@sign_response
@log
def route_system_time():
    if request.method == "GET":
        return make_response(
            {'system_time': datetime.now().isoformat()}
        )
    elif request.method == "POST":
        data = request.get_json(force=True)
        time_params = {
            'year': 0, 'month': 0, 'day': 0,
            'hour': 0, 'minute': 0, 'second': 0, 'millisecond': 0
        }
        for key in time_params.keys():
            try:
                time_params[key] = int(data[key])
            except (ValueError, KeyError):
                continue
        set_system_time(**time_params)
        return make_response(dict())


@api_bp.after_request
def after_request(response):
    response.direct_passthrough = False
    return response
