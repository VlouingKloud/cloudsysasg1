import base64
import hmac
import hashlib
import json
import time

# the key used for generating the signature
KEY = "strongkey"

def createJWT(user, period = 30 * 60):
    """ create a new JWT, by default the token will be expired after 30min
    """
    # construct the header and payload part of a JWT
    header = {'alg': 'HS256', 'typ': 'JWT'}
    payload = {'user': user, 'exp': time.time() + period}

    # encode the header and payload
    enc_header = base64.urlsafe_b64encode(json.dumps(header).encode('utf-8')).rstrip(b'=')
    enc_payload = base64.urlsafe_b64encode(json.dumps(payload).encode('utf-8')).rstrip(b'=')

    # now we create the signature
    temp = enc_header + b"." + enc_payload
    sig = hmac.new(KEY.encode('utf-8'), temp, hashlib.sha256).digest()
    enc_sig = base64.urlsafe_b64encode(sig).rstrip(b'=')

    return (temp + b"." + enc_sig).decode("utf-8")

def verifyJWT(jwt):
    """ verify if a JWT is valid,
        raise an exception if invalid
        return False if expired
        return the user name if everything is ok
    """
    # decode the jwt, we dont need to try catch here
    enc_header, enc_payload, enc_sig = jwt.decode().split(".")

    # get the jsons
    header = json.loads(base64.urlsafe_b64decode(enc_header + '==').decode('utf-8'))
    payload = json.loads(base64.urlsafe_b64decode(enc_payload + '==').decode('utf-8'))

    # calculate the expected signature
    temp = enc_header + "." + enc_payload
    sig = hmac.new(KEY.encode('utf-8'), temp.encode("utf-8"), hashlib.sha256).digest()
    expected_sig = base64.urlsafe_b64encode(sig).rstrip(b'=')

    # check the signature
    assert(expected_sig == enc_sig.encode('utf-8'))

    # check if its expired
    exp = payload['exp']
    if time.time() > exp:
        return False
    return payload['user']
