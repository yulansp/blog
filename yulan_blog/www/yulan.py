import asyncio
from aiohttp import web
import logging, os, json, time;logging.basicConfig(level=logging.INFO)
from time import strftime
import orm
from jinja2 import Environment, FileSystemLoader
import inspect
from urllib import parse
import functools
from config import configs




def get_required_keyword(fn):
    # 获取无默认值的POSITIONAL_OR_KEYWORD  or  KEYWORD_ONLY
    keyword = []
    paras = inspect.signature(fn).parameters
    for name, para in paras.items():
        if (
                para.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD or para.kind == inspect.Parameter.KEYWORD_ONLY) and para.default == inspect.Parameter.empty:
            keyword.append(name)
    return tuple(keyword)


def get_named_keyword(fn):
    # 获取POSITIONAL_OR_KEYWORD  or  KEYWORD_ONLY
    keyword = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD or param.kind == inspect.Parameter.KEYWORD_ONLY:
            keyword.append(name)
    return tuple(keyword)


def has_var_keyword(fn):
    # 是否有VAR_KEYWORD (**kwargs)
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True
    return False


def has_request(fn):
    # 是否有request参数
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if name == 'request':
            return True
    return False


class RequestHanlder(object):
    def __init__(self, fn):
        self._fn = fn
        self._request = has_request(fn)  # 返回True or False
        self._has_var_keyword = has_var_keyword(fn)  # 若无返回空元组
        self._named_keyword = get_named_keyword(fn)  # 若无返回空元组
        self._required_keyword = get_required_keyword(fn)  # 若无返回空元组

    async def __call__(self, request):
        kw = {}
        if self._has_var_keyword or self._named_keyword:
            if request.method == 'POST':
                if not request.content_type:
                    return web.HTTPBadRequest('Missing Content-Type.')
                ct = request.content_type.lower()
                if ct.startswith('application/json'):
                    params = await request.json()
                    if not isinstance(params, dict):
                        return web.HTTPBadRequest('JSON body must be object.')
                    kw = dict(**params)
                elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
                    params = await request.post()
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest('Unsupported Content-Type: %s' % request.content_type)
            elif request.method == 'GET':
                qs = request.query_string
                if qs:
                    kw = dict()
                    for k, v in parse.parse_qs(qs, True).items():
                        kw[k] = v[0]

        for k, v in request.match_info.items():
            if k in kw:
                logging.warning('Duplicate arg name in named arg and kw args: %s' % k)
            kw[k] = v

        if not self._has_var_keyword and self._named_keyword:
            # 如果handler函数没有(**kwargs)便移除未命名函数
            copy = dict()
            for name in self._named_keyword:
                if name in kw:
                    copy[name] = kw[name]
            kw = copy

        if self._request:
            kw['request'] = request

        if self._required_keyword:
            for name in self._required_keyword:
                if not name in kw:
                    return web.HTTPBadRequest('Missing argument: %s' % name)
        logging.info('call with args: %s' % str(kw))

        if not asyncio.iscoroutinefunction(self._fn):
            self._fn = asyncio.coroutine(self._fn)

        r = await self._fn(**kw)
        return r


routes = []


def get(path):
    def decorator(fun):
        fn = RequestHanlder(fun)
        routes.append(web.get(path, fn))
        @functools.wraps(fun)
        def wraps(request):
            return fn(request)
        return wraps
    return decorator


def post(path):
    def decorator(fun):
        fn = RequestHanlder(fun)
        routes.append(web.post(path, fn))
        @functools.wraps(fun)
        def wraps(request):
            return fn(request)
        return wraps
    return decorator


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
            resp = web.Response(body=json.dumps(r, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8'),
                                content_type='application/json', charset='utf-8')
            return resp
        else:
            resp = web.Response(body=request.app['__templating__'].get_template(template).render(**r).encode('utf-8'),
                                content_type='text/html', charset='utf-8')
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


def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.router.add_static('/static/', path)
    logging.info('add static %s => %s' % ('/static/', path))


def init_jinja2(app, **kw):
    logging.info('init jinja2...')
    options = dict(
        autoescape=kw.get('autoescape', True),
        block_start_string=kw.get('block_start_string', '{%'),
        block_end_string=kw.get('block_end_string', '%}'),
        variable_start_string=kw.get('variable_start_string', '{{'),
        variable_end_string=kw.get('variable_end_string', '}}'),
        auto_reload=kw.get('auto_reload', True)
    )
    path = kw.get('path', None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    logging.info('set jinja2 template path: %s' % path)
    env = Environment(loader=FileSystemLoader(path), **options)
    filters = kw.get('filters', None)
    if filters is not None:
        for name, f in filters.items():
            env.filters[name] = f
    app['__templating__'] = env


def datetime_filter(t):
    return strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))


def runapp():
    app = web.Application(middlewares=[res_middleware])
    app.add_routes(routes)
    add_static(app)
    init_jinja2(app, filters=dict(datetime=datetime_filter))
    host = configs['web']['host']
    port = configs['web']['port']
    web.run_app(app, host=host, port=port)
    logging.info('======== Running on http://%s:%s ========' % (host, port))


async def link_db(loop):
    await orm.create_pool(loop=loop, **configs['db'])


def init():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(link_db(loop))
    runapp()

