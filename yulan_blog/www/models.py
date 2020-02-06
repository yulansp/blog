import time, uuid
from orm import Model, StringField, BoolField, FloatField, TextField,IntegerField
import orm
import asyncio

def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)

class User(Model):
    __table__ = 'users'

    id = StringField(prime_key=True, default=next_id, column_type='varchar(50)')
    email = StringField(column_type='varchar(50)')
    passwd = StringField(column_type='varchar(50)')
    admin = BoolField()
    name = StringField(column_type='varchar(50)')
    created_at = FloatField(default=time.time)


class Blog(Model):
    __table__ = 'blogs'

    id = StringField(prime_key=True, default=next_id, column_type='varchar(50)')
    user_id = StringField(column_type='varchar(50)')
    user_name = StringField(column_type='varchar(50)')
    name = StringField(column_type='varchar(50)')
    summary = StringField(column_type='varchar(200)')
    content = TextField()
    content_html = TextField()
    created_at = FloatField(default=time.time)
    revised_at = FloatField(default=time.time)
    page_view = IntegerField()
    classfication = StringField(column_type = 'varchar(20)')

class Comment(Model):
    __table__ = 'comments'
    id = StringField(prime_key=True, default=next_id, column_type='varchar(50)')
    blog_id = StringField(column_type='varchar(50)')
    user_id = StringField(column_type='varchar(50)')
    user_name = StringField(column_type='varchar(50)')
    reply_to = StringField(column_type='varchar(50)')
    parent_id = StringField(column_type='varchar(50)')
    content = TextField()
    created_at = FloatField(default=time.time)
    blog_name = StringField(column_type='varchar(50)')
