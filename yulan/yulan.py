import asyncio
from aiohttp import web
import logging, os, time;
from time import strftime
from jinja2 import Environment, FileSystemLoader
import inspect
from urllib import parse
import functools
from apis import APIError
from middleware import middlewares


def get_required_keyword(fn):
    # get POSITIONAL_OR_KEYWORD  or  KEYWORD_ONLY
    keyword = []
    paras = inspect.signature(fn).parameters
    for name, para in paras.items():
        if (
                para.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD or para.kind == inspect.Parameter.KEYWORD_ONLY) and para.default == inspect.Parameter.empty:
            keyword.append(name)
    return tuple(keyword)


def get_named_keyword(fn):
    # get POSITIONAL_OR_KEYWORD  or  KEYWORD_ONLY
    keyword = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD or param.kind == inspect.Parameter.KEYWORD_ONLY:
            keyword.append(name)
    return tuple(keyword)


def has_var_keyword(fn):
    # Whether there is VAR_KEYWORD (**kwargs)
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True
    return False


def has_request(fn):
    # Whether there is param request
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if name == 'request':
            return True
    return False


class RequestHandler(object):
    def __init__(self, fn):
        self._fn = fn
        self._kw = {}
        self._request = has_request(fn)
        self._has_var_keyword = has_var_keyword(fn)
        self._named_keyword = get_named_keyword(fn)
        self._required_keyword = get_required_keyword(fn)

    async def __call__(self, request):
        await self.handelkw(request)
        if not asyncio.iscoroutinefunction(self._fn):
            self._fn = asyncio.coroutine(self._fn)
        try :
            r = await self._fn(**self._kw)
            return r
        except APIError as e:
            return dict(error=e.error, data=e.data, message=e.message)

    async def handelkw(self,request):
        for k, v in request.match_info.items():
            if k in self._kw:
                logging.warning('Duplicate arg name in named arg and kw args: %s' % k)
            self._kw[k] = v

        if not self._has_var_keyword and self._named_keyword:
            # remove the param which is not need
            copy = dict()
            for name in self._named_keyword:
                if name in self._kw:
                    copy[name] = self._kw[name]
            self._kw = copy

        if self._request:
            self._kw['request'] = request

        if self._required_keyword:
            for name in self._required_keyword:
                if not name in self._kw:
                    return web.HTTPBadRequest(text='Missing argument: %s'%name)

class GETHandler(RequestHandler):
    async def __call__(self, request):
        if self._has_var_keyword or self._named_keyword:
            qs = request.query_string
            if qs:
                for k, v in parse.parse_qs(qs, True).items():
                    self._kw[k] = v[0]

        return await super().__call__(request)

class POSTHandler(RequestHandler):
    async def __call__(self, request):
        if self._has_var_keyword or self._named_keyword:
            if not request.content_type:
                return web.HTTPBadRequest('Missing Content-Type.')
            ct = request.content_type.lower()
            if ct.startswith('application/json'):
                params = await request.json()
                if not isinstance(params, dict):
                    return web.HTTPBadRequest('JSON body must be object.')
                self._kw = dict(**params)
            elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
                params = await request.post()
                self._kw = dict(**params)
            else:
                return web.HTTPBadRequest('Unsupported Content-Type: %s' % request.content_type)
        return await super().__call__(request)


class FilePostHandler(RequestHandler):
    async def __call__(self, request):
        if not request.content_type:
            return web.HTTPBadRequest('Missing Content-Type.')
        ct = request.content_type.lower()
        if  ct.startswith('multipart/form-data'):
            reader = await request.multipart()
            self._kw['reader'] = reader
        else:
            return web.HTTPBadRequest('Unsupported Content-Type: %s' % request.content_type)
        return await super().__call__(request)

routes = []

def get(path):
    def decorator(fun):
        fn = GETHandler(fun)
        routes.append(web.get(path, fn))
        @functools.wraps(fun)
        def wraps(request):
            return fn(request)
        return wraps
    return decorator

def post(path):
    def decorator(fun):
        fn = POSTHandler(fun)
        routes.append(web.post(path, fn))
        @functools.wraps(fun)
        def wraps(request):
            return fn(request)
        return wraps
    return decorator

def file_post(path):
    def decorator(fun):
        fn = FilePostHandler(fun)
        routes.append(web.post(path, fn))
        @functools.wraps(fun)
        def wraps(request):
            return fn(request)
        return wraps
    return decorator

def add_static(app,static_path='static'):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), static_path)
    app.router.add_static('/static/', path)
    logging.info('add static %s => %s' % ('/static/', path))

def init_jinja2(app, **kw):
    # init jinja2,kw: the config as same as jinja2
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


def runapp(host='127.0.0.1',port = 5000):
    app = web.Application(middlewares=middlewares)
    app.add_routes(routes)
    add_static(app)
    init_jinja2(app, filters=dict(datetime=datetime_filter))
    web.run_app(app,host=host,port=port)



