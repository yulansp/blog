# ORM使用方法

### 导入包
~~~python
import time, uuid
from orm import Model, StringField, BoolField, FloatField, TextField
import orm
import asyncio
~~~

### 创建表对象
```python
def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)

class User(Model):
    __table__ = 'users'

    id = StringField(prime_key=True, default=next_id, column_type='varchar(50)')
    email = StringField(column_type='varchar(50)')
    passwd = StringField(column_type='varchar(50)')
    admin = BoolField()
    name = StringField(column_type='varchar(50)')
    image = StringField(column_type='varchar(500)')
    created_at = FloatField(default=time.time)
   ```

### 查找select
```python
async def test(loop):
    await orm.create_pool(loop = loop,user='...', password='...', db='...')
    u =await User.FindAll(where = 'name',args = 'Test')
    print(u)

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.run_forever()
```
or
```python
async def test(loop):
    await orm.create_pool(loop = loop,user='...', password='...', db='...')
    u =await User.FindAll(where = ('name','image'),args = ('Test','about:blank'))
    print(u)

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.run_forever()
```

### 插入表INSERT
```python
async def test(loop):
    await orm.create_pool(loop = loop,user='...', password='...', db='...')

    u = User(name='Test', email='test@example.com', passwd='1234567890', image='about:blank')

    await u.insert()

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.run_forever()
```

### 删除DELETE
```python
async def test(loop):
    await orm.create_pool(loop = loop,user='...', password='...', db='...')
    id = '001580039117160dfdf31cf27ea4aa497d82f10ad55b8dd000'
    u =await User().Find(id)
    await u.delete()

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.run_forever()
```

or
```python
async def test(loop):
    await orm.create_pool(loop = loop,user='...', password='...', db='...')
    users =await User.FindAll(where = 'name',args = 'Test')
    if len(users) == 1:
        u = users[0]
    else:
        raise RuntimeError('find %s users' % len(users))
    await u.delete()

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.run_forever()
```

### 更新UPDATE
```python
async def test(loop):
    await orm.create_pool(loop = loop,user='...', password='...', db='...')
    id = '001580039117160dfdf31cf27ea4aa497d82f10ad55b8dd000'
    u =await User().Find(id)
    u['passwd'] = '11111'
    await u.update()

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.run_forever()
```
or
```python
async def test(loop):
    await orm.create_pool(loop = loop,user='...', password='...', db='...')
    users =await User.FindAll(where = 'name',args = 'Test')
    if len(users) == 1:
        u = users[0]
    else:
        raise RuntimeError('find %s users' % len(users))
    u['passwd'] = '22222'
    await u.update()

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.run_forever()
```
