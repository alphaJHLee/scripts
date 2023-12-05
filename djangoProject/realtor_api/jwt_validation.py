

import jwt
import re
import time
from .models import LandAptMember
from idodb_key.ido_jwt import jwt_key

def jwt_validation(token):
    token_map = re.split(' ',token)
    if token_map[0] != 'Bearer':
        raise ValueError('invalid jwt token')
    decoded_jwt = jwt.decode(token_map[1],
                             key = 'jwt_key',algorithms='HS256')
    sub = decoded_jwt['sub']
    exp = decoded_jwt['exp']
    if exp <= time.time():
        raise ValueError('token expired')
    if bool(LandAptMember.objects.filter(mb_no = int(sub)).values()) == False:
        raise ValueError('invalid login access.')


