import sys
import traceback
from datetime import datetime
from functools import wraps

from flask import Blueprint, make_response, render_template, request
from flask_api import status

from ..core.config import Config
from ..core.fire_command import FireCommand
from ..core.fire_controller import FireController
from ..core.hardware_controller import HardwareController
from ..core.address import Address
from ..core.master_communication import MasterCommunicator
from ..util.sys_time import set_system_time

api_bp = Blueprint('api_blueprint', __name__)


def handle_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
        except Exception:
            exc_type, exc, tb = sys.exc_info()
            content = {
                'exception_type': str(exc_type),
                'exception_args': vars(exc),
                'traceback': traceback.extract_tb(tb).format()
            }
            status_code = status.HTTP_400_BAD_REQUEST
            response = make_response((content, status_code))
        finally:
            return response
    return wrapper


@api_bp.route("/", methods=["GET"], endpoint='route_main')
def route_main():
    return render_template(
        "index.html",
        device_id=Config.get("connection", 'device_id'),
        port=Config.get("connection", 'external_port'),
        time=datetime.now()
    )


@api_bp.route("/config", methods=["GET", "POST"], endpoint='route_config')
@handle_exceptions
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
@handle_exceptions
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
@handle_exceptions
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
@handle_exceptions
def route_program_state():
    return make_response({'state': FireController.get_program_state()})


@api_bp.route("/fire", methods=["POST", "GET"], endpoint='route_fire')
@handle_exceptions
def route_fire():
    address = Address(request.get_json(force=True)['address'])
    fire_command = FireCommand(
        address=address,
        timestamp=0
    )
    fire_command.fire()
    return make_response(dict())


@api_bp.route("/fuses", methods=["GET"], endpoint='route_fuses')
@handle_exceptions
def route_fuses():
    return make_response(FireController.get_fuse_status())


@api_bp.route("/testloop", methods=["POST"], endpoint='route_testloop')
@handle_exceptions
def route_testloop():
    FireController.testloop()
    return make_response(dict())


@api_bp.route("/lock", methods=["GET", "POST"], endpoint='route_lock')
@handle_exceptions
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
@handle_exceptions
def route_errors():
    if request.method == "GET":
        response = HardwareController.errors()
    elif request.method == "DELETE":
        HardwareController.clear_error_flags()
        response = dict()
    return make_response(response)


@api_bp.route(
    "/master-registration",
    methods=["POST", "DELETE"], endpoint='route_master_listener'
)
@handle_exceptions
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
@handle_exceptions
def route_system_time():
    if request.method == "GET":
        return make_response(
            {'system_time': datetime.now().isoformat()}
        )
    elif request.method == "POST":
        time = request.get_json(force=True)['time']
        set_system_time(time)
        return make_response(dict())
