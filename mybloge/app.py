import handlers
from yulan import runapp
from config import configs
import asyncio
from orm import create_mysql,close_mysql
from rds import create_rds,close_rds


def init():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_mysql(loop=loop, **configs['mysql']))
    loop.run_until_complete(create_rds(loop=loop,**configs['rds']))
    runapp(host = configs['web']['host'],port = configs['web']['port'],static='static')
    close_mysql()
    close_rds()
    loop.stop()
    loop.close()

if __name__ == '__main__':
    init()