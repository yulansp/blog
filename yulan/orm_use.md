# ORM reference

### import
~~~python
import time, uuid
from orm import Model, StringField, BoolField, IntegerField
import orm
import asyncio
~~~

### table define
```python
def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)

class User(Model):
    __table__ = 'users'

    id = StringField(primary_key=True, default=next_id, column_type='varchar(50)')
    email = StringField(column_type='varchar(50)')
    age = IntegerField(default=18)
   ```
**primary_key** :Primary key or not


### create connect pool
```python
async def link_db(loop):
    await orm.create_mysql(loop=loop, user='...', password='...', db='...')

loop = asyncio.get_event_loop()
loop.run_until_complete(link_db(loop))
loop.run_forever()
```

### select
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

### group select
```python
num = await User.FindNumber('count(*)')
print(num)
#num是int
```

### INSERT
```python
u = User(name='Test', email='test@example.com', passwd='1234567890', image='about:blank')
await u.insert()
```

### DELETE
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

### UPDATE
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
