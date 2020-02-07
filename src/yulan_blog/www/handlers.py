from yulan import init,get,post
from models import User,Blog,Comment
import time,uuid,json,os
from apis import APIError,APIValueError,APIResourceNotFoundError,APIPermissionError
import re,hashlib,logging
from aiohttp import web
from config import configs
from lxml import etree
from time import strftime

item_per_page = 15
_COOKIE_KEY = configs['session']['secret']
COOKIE_NAME = 'yulan'
_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)

@get('/')
async def index(page=1):
    page = int(page)
    total = await Blog.FindNumber('count(*)')
    page_count = total // item_per_page + (1 if total % item_per_page > 0 else 0)
    if page < 1 or page > page_count:
        page = 1
    blogs = await Blog.FindAll(orderBy='revised_at desc' ,limit=((page-1)*item_per_page,item_per_page))
    return {
        '__template__': 'mainpage.html',
        'blogs': blogs,
        'classfication' : 'main',
        'total_item' : total,
        'current_page': page,
        'title': '首页'
    }

@get('/skill')
async def index(page=1):
    page = int(page)
    total = await Blog.FindNumber('count(*)',where='classfication',args='skill')
    page_count = total // item_per_page + (1 if total % item_per_page > 0 else 0)
    if page < 1 or page > page_count:
        page = 1
    blogs = await Blog.FindAll(where='classfication',args='skill',orderBy='revised_at desc')
    return {
        '__template__': 'mainpage.html',
        'blogs': blogs,
        'classfication' : 'skill',
        'total_item': total,
        'current_page': page,
        'title': '技术'
    }

@get('/read')
async def index(page=1):
    page = int(page)
    total = await Blog.FindNumber('count(*)',where='classfication',args='read')
    page_count = total // item_per_page + (1 if total % item_per_page > 0 else 0)
    if page < 1 or page > page_count:
        page = 1
    blogs = await Blog.FindAll(where='classfication',args='read',orderBy='revised_at desc')
    return {
        '__template__': 'mainpage.html',
        'blogs': blogs,
        'classfication' : 'read',
        'total_item': total,
        'current_page': page,
        'title': '读书'
    }

@get('/something')
async def index(page=1):
    page = int(page)
    total = await Blog.FindNumber('count(*)',where='classfication',args='something')
    page_count = total // item_per_page + (1 if total % item_per_page > 0 else 0)
    if page < 1 or page > page_count:
        page = 1
    blogs = await Blog.FindAll(where='classfication',args='something',orderBy='revised_at desc')
    return {
        '__template__': 'mainpage.html',
        'blogs': blogs,
        'classfication' : 'something',
        'total_item': total,
        'current_page': page,
        'title': '杂谈'
    }

@get('/about')
async def show_blog():
    blog = {}
    return {
        '__template__' : 'about.html',
    }

@get('/blog')
async def show_blog(id):
    blog = await Blog.Find(id)
    if not blog:
        return web.HTTPNotFound()
    blog.page_view += 1
    await blog.update()
    return {
        '__template__' : 'show_blog.html',
        'blog' : blog,
        'classfication' : blog.classfication
    }

def user_to_cookie(user,max_age):
    expires = str(int(time.time()) + max_age)
    s = '%s%s%s%s' %(user.id,user.passwd,expires,_COOKIE_KEY)
    L = [user.id,expires,hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

@post('/api/register')
async def register(email,name,passwd):
    if not name:
        raise APIValueError('name','缺少昵称')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email','请输入正确的邮箱')
    if not passwd:
        raise APIValueError('passwd','缺少密码')
    users = await User.FindAll(where = 'email',args = email)
    if len(users) > 0:
        raise APIError('register:failed', 'email', '邮箱已存在,请直接登录')
    uid = next_id()
    sha1_passwd = '%s:%s' % (uid, passwd)
    user = User(id=uid, name=name.strip(), email=email, passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest())
    await user.insert()
    # make session cookie:
    r = web.Response(content_type='application/json')
    r.set_cookie(COOKIE_NAME, user_to_cookie(user, 864000), max_age=864000, httponly=True)
    return r

@post('/api/signin')
async def signin(email,passwd):
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email','请输入正确的邮箱')
    if not passwd:
        raise APIValueError('passwd','缺少密码')
    user = await User.FindAll(where='email',args=email)
    if len(user) == 0:
        raise APIValueError('email','邮箱不存在')
    u = user[0]
    uid = u.id
    sha1_passwd = '%s:%s' % (uid, passwd)
    if u.passwd != str(hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest()):
        raise APIValueError('passwd','密码错误')
    r = web.Response(content_type='application/json')
    r.set_cookie(COOKIE_NAME, user_to_cookie(u, 864000), max_age=864000, httponly=True)
    return r

@get('/api/signout')
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    return r

@get('/admin')
def admin(request):
    if request.__user__:
        if request.__user__.admin:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates','admin.html')
            with open(path,'r',encoding='utf-8') as f:
                return web.Response(text=f.read(),content_type='text/html')

    logging.warning('Try get admin page without authorize')
    return web.HTTPForbidden()

@get('/edit')
def edit(request):
    if request.__user__:
        if request.__user__.admin:
            template = 'edit.html'
            r = {}
            r['user'] = request.__user__
            resp = web.Response(
                body=request.app['__templating__'].get_template(template).render(**r).encode('utf-8'),
                content_type='text/html', charset='utf-8')
            resp.set_cookie('blog_id', '1', max_age=86400, httponly=True)
            return resp

    logging.warning('Try edit without authorize')
    return web.HTTPForbidden()

@get('/revise')
async def revise_blog(request,blog_id):
    if request.__user__:
        if request.__user__.admin:
            blog = await Blog.Find(blog_id)
            if not blog:
                resp = web.Response(
                    body=json.dumps({'message': '您的文件消失在了火星'}, ensure_ascii=False, default=lambda o: o.__dict__).encode(
                        'utf-8'),
                    content_type='application/json', charset='utf-8')
                return resp
            template = 'edit.html'
            blog.content = blog.content.replace('\n', '\\n')
            blog.content = blog.content.replace('"', '\\"')
            blog.content = blog.content.replace("'", "\\'")
            print(blog.content)
            blog.name = blog.name.replace('\n', '\\n')
            blog.name = blog.name.replace('"', '\\"')
            blog.name = blog.name.replace("'", "\\'")
            r = {'blog':blog}
            r['user'] = request.__user__
            resp = web.Response(
                body=request.app['__templating__'].get_template(template).render(**r).encode('utf-8'),
                content_type='text/html', charset='utf-8')
            resp.set_cookie('blog_id', blog.id, max_age=86400, httponly=True)
            return resp

    logging.warning('Try revise without authorize')
    return web.HTTPForbidden()

@post('/api/release')
async def release(request,name,content,content_html,classfication):
    if request.__user__:
        if request.__user__.admin:
            blog_id = request.cookies.get('blog_id')
            if not blog_id:
                raise APIPermissionError('您的cookie已过期')
            if not content_html:
                return web.json_response({'message':'内容不能为空'})
            et = etree.HTML(content_html)
            summary = ''
            ss = et.xpath('//text()')
            if not classfication:
                classfication = 'main'
            for s in ss:
                summary = summary + s.replace('\n','')
                summary = summary + ' '
                if len(summary) >= 15:
                    break
            if len(summary) > 30:
                summary = summary[0:30]
            if blog_id == '1':
                blog = Blog(name=name, summary=summary, content=content,content_html = content_html,classfication = classfication)
                r = await blog.insert()
                if r:
                    resp = web.Response(content_type='application/json')
                    resp.set_cookie('blog_id', '-deleted-', max_age=0, httponly=True)
                    return resp
                else:
                    return {'message':'发布失败,请重试'}
            else:
                blog = await Blog.Find(blog_id)
                if not blog:
                    resp = web.json_response({'message': '您的文件消失在了火星'})
                    resp.set_cookie('blog_id', '-deleted-', max_age=0, httponly=True)
                    return resp
                else :
                    blog.name = name
                    blog.summary = summary
                    blog.content = content
                    blog.content_html = content_html
                    blog.classfication = classfication
                    blog.revised_at = time.time()
                    r = await blog.update()
                    if r:
                        resp = web.Response(content_type='application/json')
                        resp.set_cookie('blog_id', '-deleted-', max_age=0, httponly=True)
                        return resp
                    else:
                        return {'message': '发布失败,请重试'}

    logging.warning('Try release without authorize')
    return web.HTTPForbidden()

item_per_page_manage = 20
@get('/api/blogmanage')
async def blog_manage(request,page = 1):
    if request.__user__:
        if request.__user__.admin:
            page = int(page)
            total = await Blog.FindNumber('count(*)')
            page_count = total // item_per_page_manage + (1 if total % item_per_page > 0 else 0)
            if page < 1 or page > page_count:
                page = 1
            blogs = await Blog.FindAll(orderBy='revised_at desc', limit=((page - 1) * item_per_page_manage, item_per_page_manage))
            return {
                'total_item' : total,
                'blogdata' : [
                    {'name' : blog.name,
                     'date' : strftime('%Y-%m-%d', time.localtime(blog.revised_at)),
                     'hot' : blog.page_view,
                     'id' : blog.id}
                    for blog in blogs
                ]
            }
    logging.warning('Try blogmanage without authorize')
    return web.HTTPForbidden()

@get('/api/commentmanage')
async def comment_manage(request,page = 1):
    if request.__user__:
        if request.__user__.admin:
            page = int(page)
            total = await Comment.FindNumber('count(*)')
            page_count = total // item_per_page_manage + (1 if total % item_per_page > 0 else 0)
            if page < 1 or page > page_count:
                page = 1
            comments = await Comment.FindAll(orderBy='created_at desc', limit=((page - 1) * item_per_page_manage, item_per_page_manage))
            return {
                'total_item' : total,
                'commentdata' : [
                    {'content' : comment.content,
                     'date' : strftime('%Y-%m-%d', time.localtime(comment.created_at)),
                     'comefrom' : comment.blog_name,
                     'id' : comment.id}
                    for comment in comments
                ]
            }
    logging.warning('Try commentmanage without authorize')
    return web.HTTPForbidden()

@get('/api/usermanage')
async def user_manage(request,page = 1):
    if request.__user__:
        if request.__user__.admin:
            page = int(page)
            total = await User.FindNumber('count(*)')
            page_count = total // item_per_page_manage + (1 if total % item_per_page > 0 else 0)
            if page < 1 or page > page_count:
                page = 1
            users = await User.FindAll(orderBy='created_at desc', limit=((page - 1) * item_per_page_manage, item_per_page_manage))
            return {
                'total_item' : total,
                'userdata' : [
                    {'name' : user.name,
                     'created_at' : strftime('%Y-%m-%d', time.localtime(user.created_at))}
                    for user in users
                ]
            }
    logging.warning('Try usermanage without authorize')
    return web.HTTPForbidden()

@get('/api/delete')
async def delete(request,id,operation):
    if request.__user__:
        if request.__user__.admin:
            if operation=='blog':
                blog = await Blog.Find(id)
                if not blog:
                    return web.HTTPNotFound()
                r = await blog.delete()
                comments = await Comment.FindAll(where='blog_id',args=id)
                for comment in comments:
                    await comment.delete()
                if r:
                    return web.Response(content_type='application/json')
                else:
                    return {'message': '删除失败,请重试'}
            elif operation == 'comment':
                delete_id = [id]
                parent_comment = await Comment.Find(id)
                if not parent_comment:
                    return web.HTTPNotFound()
                if parent_comment.parent_id=='0':
                    comments = await Comment.FindAll(where='parent_id', args=id)
                    for comment in comments:
                        delete_id.append(comment.id)
                        await comment.delete()
                await parent_comment.delete()
                return web.json_response(delete_id)
            else:
                logging.warning('Try delete without permission')
                return web.HTTPForbidden()

    logging.warning('Try delete without permission')
    return web.HTTPForbidden()

@post('/api/manage_reply')
async def manage_reply(request,reply_to_id,content):
    if request.__user__:
        if request.__user__.admin:
            reply_to_comment = await Comment.Find(reply_to_id)
            comment = Comment(blog_id=reply_to_comment.blog_id,
                              user_id=request.__user__.id,
                              user_name=request.__user__.name,
                              reply_to=reply_to_comment.user_name,
                              parent_id=reply_to_id if reply_to_comment.parent_id == '0' else reply_to_comment.parent_id,
                              content=content,
                              blog_name=reply_to_comment.blog_name)
            print(comment)
            await comment.insert()
            return web.json_response()
    logging.warning('Try reply without permission')
    return web.HTTPForbidden()

@post('/api/comment')
async def comment(request,blog_id,parent_id,content,reply_to,blog_name):
    if request.__user__:
        user_id = request.__user__.id
        name = request.__user__.name
    else:
        user_id='0'
        name = '游客'
    id = next_id()
    comment = Comment(id=id,blog_id=blog_id,user_id=user_id,user_name=name,reply_to=reply_to,parent_id=parent_id,content=content,blog_name=blog_name)
    await comment.insert()
    return {
        'id' : id,
        'name' : name
    }

def time_filtter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta < 86400:
        return u'%s小时前' % (delta // 3600)
    if delta < 604800:
        return u'%s天前' % (delta // 86400)
    else :
        return strftime('%Y-%m-%d', time.localtime(t))


@get('/api/commentlist')
async def get_comment_list(blog_id):
    blog_id = str(blog_id)
    comments = await Comment.FindAll(where='blog_id',args=blog_id,orderBy='created_at desc')
    parentcomment = []
    id_to_index = {}
    index = 0
    for i in range(len(comments)-1,-1,-1):
        comment = comments[i]
        if comment.parent_id == '0':
            id_to_index[comment.id] = index
            idnex = index + 1
            r_comment = {
                'id' : comment.id,
                'content' : comment.content,
                'name' : comment.user_name,
                'time' : time_filtter(comment.created_at),
                'reply_to' : comment.reply_to,
                'subcomment' : []
            }
            parentcomment.append(r_comment)
            comments.pop(i)
    for comment in comments :
        r_comment = {
            'id': comment.id,
            'content': comment.content,
            'name': comment.user_name,
            'time': time_filtter(comment.created_at),
            'reply_to': comment.reply_to,
            'subcomment': []
        }
        parentcomment[id_to_index[comment.parent_id]]['subcomment'].append(r_comment)
    return web.json_response(parentcomment)


def main():
    init()

