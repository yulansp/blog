from yulan import init,get,post
from models import User

@get('/')
async def index():
    u = await User.FindAll()
    return {
        '__template__':'test.html',
        'users':u
    }

if __name__ == '__main__':
    init()