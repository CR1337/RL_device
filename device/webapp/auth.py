import hmac
from hashlib import sha1

_SECRET_FILENAME = "device/config/secret"
# _SECRET_FILENAME = "device/config/secret"

# with open(_SECRET_FILENAME, 'rb') as file:
#     _secret = file.read()

_secret = b"blubb"


def sign_message(message):
    mac = hmac.new(_secret, msg=message, digestmod=sha1)
    return mac.hexdigest()


def authenticate(request):
    if 'Signature' not in request.headers:
        return False
    header_signature = request.headers['Signature']
    signature = sign_message(request.data)
    return signature == header_signature
