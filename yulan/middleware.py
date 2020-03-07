from aiohttp import web
import os

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
            shicifile = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'shici.html')
            with open(shicifile,'rb') as f:
                r['poetry'] = f.read().decode('utf-8')
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

middlewares = [res_middleware]