from yulan import runapp,get,post,file_post
@get('/')
async def hello():
    return 'hello'

runapp()