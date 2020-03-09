# yulan web framework

yulan是一个基于aiohttp3.6.2二次封装的web框架

## Key Features
* 基于asyncio，并发性能好
* 支持`get` `post` `file_post`三个方法
* 附带一个简易orm

## get start
首先创建如下目录
```python
+- www/                  <-- Web目录
|  |
|  +- static/            <-- 存放静态文件
|  |
|  +- templates/         <-- 存放模板文件
|  app.py
```
simple use
```python
from yulan import runapp
@get('/')
async def hello():
    return 'hello'

runapp()
```
GET with a query string such as `http://127.0.0.1:5000/?name=yyy`
```python
from yulan import runapp
@get('/')
async def hello(name):
    return 'hello' + name

runapp()
```
use jinja2 tamplete
```python
from yulan import runapp
@get('/')
async def hello(name):
    return {'__template__': 'hello.html',
            'name':name}

runapp()
```

json response
```python
from yulan import runapp
@get('/')
async def hello(name):
    return {'name':name}

runapp()
```

file upload
```python
@file_post('/api/file_upload')
async def file_upload(reader):
    field = await reader.next()
    filename = field.filename
    size = 0
    with open(filename, 'wb') as f:
        while True:
            chunk = await field.read_chunk()
            if not chunk:
                break
            size += len(chunk)
            f.write(chunk)
    return 'ok'
```

更改host与port
```python
runapp(host=yourhost,port=yourport)
```
## demo
[myblog](https://yulan.net.cn/) 欢迎访问！！！  
[仓库地址](https://github.com/yulansp/blog/tree/master/mybloge)
