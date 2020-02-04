from aiohttp import web
import json,logging,time,hashlib
from models import User
from config import configs

_COOKIE_KEY = configs['session']['secret']
COOKIE_NAME = 'yulan'

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

#处理cookie
@web.middleware
async def cookie_middleware(request,handler):
    request.__user__ = None
    cookie_str = request.cookies.get(COOKIE_NAME)
    if cookie_str:
        user = await cookie_to_user(cookie_str)
        if user:
            request.__user__ = user
    return await handler(request)

# 返回中间件，处理返回值
@web.middleware
async def res_middleware(request, handler):
    r = await handler(request)
    if isinstance(r, web.StreamResponse):
        return r
    if isinstance(r, bytes):
        resp = web.Response(body=r, content_type='application/octet-stream')
        return resp
    if isinstance(r, str):
        if r.startswith('redirect:'):
            return web.HTTPFound(r[9:])
        resp = web.Response(body=r.encode('utf-8'), content_type='text/html', charset='utf-8')
        return resp
    if isinstance(r, dict):
        template = r.get('__template__')
        if template is None:
            return web.json_response(r)
        else:
            r['user'] = request.__user__
            resp = web.Response(
                body=request.app['__templating__'].get_template(template).render(**r).encode('utf-8'),content_type='text/html', charset='utf-8')
            return resp
    if isinstance(r, int) and r >= 100 and r < 600:
        return web.Response(r)
    if isinstance(r, tuple) and len(r) == 2:
        t, m = r
        if isinstance(t, int) and t >= 100 and t < 600:
            return web.Response(t, str(m))
        # default:
    resp = web.Response(body=str(r).encode('utf-8'), content_type='text/html', charset='utf-8')
    return resp

middlewares = [res_middleware,cookie_middleware]