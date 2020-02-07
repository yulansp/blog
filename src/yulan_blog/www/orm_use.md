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

### 初始连接数据库，创建连接池
```python
async def link_db(loop):
    await orm.create_pool(loop=loop, user='...', password='...', db='...')

loop = asyncio.get_event_loop()
loop.run_until_complete(link_db(loop))
loop.run_forever()
```

### 查找select
```python
u =await User.FindAll(where = 'name',args = 'Test')
print(u)
#u是一个[{},{}]
```
or
```python
u =await User.FindAll(where = ('name','image'),args = ('Test','about:blank'))
print(u)
#u是一个[{},{}]
```

### 查询数目
```python
num = await User.FindNumber('count(*)')
print(num)
#num是int
```

### 插入表INSERT
```python
u = User(name='Test', email='test@example.com', passwd='1234567890', image='about:blank')
await u.insert()
```

### 删除DELETE
```python
id = '001580039117160dfdf31cf27ea4aa497d82f10ad55b8dd000'
u =await User().Find(id)
await u.delete()
```

or
```python
users =await User.FindAll(where = 'name',args = 'Test')
if len(users) == 1:
    u = users[0]
else:
    raise RuntimeError('find %s users' % len(users))
await u.delete()
```

### 更新UPDATE
```python
id = '001580039117160dfdf31cf27ea4aa497d82f10ad55b8dd000'
u =await User().Find(id)
u.passwd = '11111'
await u.update()
```
or
```python
users =await User.FindAll(where = 'name',args = 'Test')
if len(users) == 1:
    u = users[0]
else:
    raise RuntimeError('find %s users' % len(users))
u.passwd = '22222'
await u.update()
```
