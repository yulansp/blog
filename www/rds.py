import aioredis


async def create_rds(host='127.0.0.1', port=6379,
                     db=0, password=None, ssl=None,
                     encoding=None, minsize=1,
                     maxsize=3, parser=None, loop=None,
                     create_connection_timeout=None,
                     pool_cls=None,connection_cls=None):
    global __pool
    __pool = await aioredis.create_pool((host, port),
                                        db=db,password=password,
                                        ssl=ssl,encoding=encoding,
                                        minsize=minsize,maxsize=maxsize,
                                        parser=parser,loop=loop,create_connection_timeout=create_connection_timeout,
                                        pool_cls=pool_cls,connection_cls=connection_cls)


async def execute(*args):
    global __pool
    return await __pool.execute(*args)

async def close_rds():
    global __pool
    __pool.close()
    await __pool.wait_closed()
