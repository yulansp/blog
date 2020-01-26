import asyncio
from aiohttp import web
import logging,os,json,time;logging.basicConfig(level=logging.INFO)
from datetime import datetime

routes = web.RouteTableDef()

@routes.get('/')
async def index(request):
    return web.Response(body='<h1>Index</h1>',content_type='text/html')

@routes.get('/hello/{name}')
async def hello(request):
    text = '<h1>hello, %s!</h1>' % request.match_info['name']
    return web.Response(body=text,content_type='text/html')

def init():
    app = web.Application()
    app.add_routes(routes)
    host = '127.0.0.1'
    port = 8000
    web.run_app(app,host=host,port = port)
    print('======== Running on http://%s:%s ========' % (host,port))

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init())
    loop.run_forever()