from config import configs
import time,hashlib,logging
from models import User

_COOKIE_KEY = configs['session']['secret']
COOKIE_NAME = 'yulan'

def user_to_cookie(user,max_age):
    expires = str(int(time.time()) + max_age)
    s = '%s%s%s%s' %(user.id,user.passwd,expires,_COOKIE_KEY)
    L = [user.id,expires,hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)


async def cookie_to_user(cookie):
    if not cookie:
        return None
    try:
        L = cookie.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        if int(expires) < time.time():
            return None
        user = await User.Find(uid)
        if user is None:
            return None
        s = '%s%s%s%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None
