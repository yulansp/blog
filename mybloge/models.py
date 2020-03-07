import time, uuid
from orm import Model, StringField, BoolField, FloatField, TextField,IntegerField
import orm
import asyncio

def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)

class User(Model):
    __table__ = 'users'

    id = StringField(primary_key=True, default=next_id, column_type='varchar(50)')
    email = StringField(column_type='varchar(50)')
    passwd = StringField(column_type='varchar(50)')
    admin = BoolField()
    name = StringField(column_type='varchar(50)')
    img = StringField(column_type='varchar(50)')
    created_at = FloatField(default=time.time)


class Blog(Model):
    __table__ = 'blogs'

    id = StringField(primary_key=True, default=next_id, column_type='varchar(50)')
    name = StringField(column_type='varchar(50)')
    summary = StringField(column_type='varchar(200)')
    content = TextField()
    content_html = TextField()
    created_at = FloatField(default=time.time)
    revised_at = FloatField(default=time.time)
    page_view = IntegerField()
    classfication = StringField(column_type = 'varchar(20)')
    tag = StringField(column_type = 'varchar(20)')
    top = IntegerField()

class Comment(Model):
    __table__ = 'comments'
    id = StringField(primary_key=True, default=next_id, column_type='varchar(50)')
    blog_id = StringField(column_type='varchar(50)')
    user_id = StringField(column_type='varchar(50)')
    user_name = StringField(column_type='varchar(50)')
    user_img = StringField(column_type='varchar(50)')
    reply_to = StringField(column_type='varchar(50)')
    parent_id = StringField(column_type='varchar(50)')
    content = TextField()
    created_at = FloatField(default=time.time)
    blog_name = StringField(column_type='varchar(50)')

class Timeline(Model):
    __table__ = 'timeline'
    version = StringField(primary_key=True,column_type='varchar(30)')
    content = StringField(column_type='varchar(200)')
    release_time = StringField(column_type='varchar(30)')