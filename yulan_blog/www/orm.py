import asyncio, logging, aiomysql


def logsql(sql, args=()):
    logging.info('SQL : %s   args : %s' % (sql, args))


# 创建sql连接池
async def create_pool(loop, **kwargs):
    logging.info('*** create database connection pool ***')
    global __pool
    __pool = await aiomysql.create_pool(host=kwargs.get('host', '127.0.0.1'),
                                        port=kwargs.get('port', 3306),
                                        user=kwargs['user'],
                                        password=kwargs['password'],
                                        db=kwargs['db'],
                                        charset=kwargs.get('charset', 'utf8'),
                                        autocommit=kwargs.get('autocommit', True),
                                        maxsize=kwargs.get('maxsize', 10),
                                        minsize=kwargs.get('minsize', 1),
                                        loop=loop
                                        )


# select 查询
async def select(sql, args, size=None):
    logsql(sql, args)
    global __pool
    async with  __pool.acquire() as conn:
        cur = await conn.cursor(aiomysql.DictCursor)
        await cur.execute(sql.replace('?', '%s'), args or ())
        if size:
            rs = await cur.fetchmany(size)
        else:
            rs = await cur.fetchall()
        await cur.close()
        logging.info('select return %s rows' % len(rs))
        return rs


# insert，delete，update
async def execute(sql, args, autocommit=True):
    logsql(sql, args)
    global __pool
    async with __pool.acquire() as conn:
        if not autocommit:
            await  conn.begin()
        try:
            cur = await conn.cursor(aiomysql.DictCursor)
            await cur.execute(sql.replace('?', '%s'), args or ())
            if not autocommit:
                await conn.commit()
        except Exception as e:
            if not autocommit:
                conn.roolback()
                raise
        rs = cur.rowcount
        if rs:
            return rs
        else:
            return -1


def creatr_args_string(num):
    l = []
    for i in range(num):
        l.append('?')
    return ','.join(l)


class Field(object):
    def __init__(self, name, column_type, prime_key, default):
        self.name = name
        self.column_type = column_type
        self.prime_key = prime_key
        self.default = default

    def __str__(self):
        return '<%s %s %s>' % (self.__class__.__name__, self.column_type, self.name)

    __repr__ = __str__


class StringField(Field):
    def __init__(self, name=None, column_type='varchar(100)', prime_key=False, default=None):
        super().__init__(name, column_type, prime_key, default)


class IntegerField(Field):
    def __init__(self, name=None, column_type='int', prime_key=False, default=0):
        super().__init__(name, column_type, prime_key, default)


class BoolField(Field):
    def __init__(self, name=None, column_type='boolean', prime_key=False, default=False):
        super().__init__(name, column_type, prime_key, default)


class FloatField(Field):
    def __init__(self, name=None, column_type='real', prime_key=False, default=0.0):
        super().__init__(name, column_type, prime_key, default)


class DatetimeField(Field):
    def __init__(self, name=None, column_type='datetime', prime_key=False, default=None):
        super().__init__(name, column_type, prime_key, default)


class TextField(Field):
    def __init__(self, name=None, column_type='text', prime_key=False, default=None):
        super().__init__(name, column_type, prime_key, default)


class ModelMeatclass(type):
    def __new__(cls, name, bases, attrs):
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)

        tablename = attrs.get('__table__', None) or name
        logging.info('Found Model: %s (%s)' % (name, tablename))

        mapping = dict()  # 存储映射表，即列名：列Field
        fields = []  # 存储非key的列名
        primekey = None  # 存储key列名

        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info('Find mapping %s ==> %s' % (k, v))
                mapping[k] = v
                if v.prime_key:
                    logging.info('Find Primekey %s' % k)
                    if primekey:
                        raise RuntimeError("Duplicated prime key")
                    primekey = k
                else:
                    fields.append(k)

        if not primekey:
            raise RuntimeError("Can not find a prime key")

        # 删掉Field属性，防止乱引用
        for i in mapping.keys():
            attrs.pop(i)

        # 加上``防止与mysql保留字冲突，提高兼容性
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))

        attrs['__table__'] = tablename
        attrs['__mappings__'] = mapping
        attrs['__prime_key__'] = primekey
        attrs['__fields__'] = fields
        attrs['__select__'] = 'SELECT `%s`,%s FROM `%s`' % (primekey, ','.join(escaped_fields), tablename)
        attrs['__insert__'] = 'INSERT INTO `%s` (`%s`,%s) VALUES (%s)' % (
            tablename, primekey, ','.join(escaped_fields), creatr_args_string(len(escaped_fields) + 1))
        attrs['__delete__'] = 'DELETE FROM `%s` WHERE `%s` = ?' % (tablename, primekey)
        attrs['__update__'] = 'UPDATE `%s` set %s where `%s`=?' % (
            tablename, ', '.join(map(lambda f: '`%s`=?' % f, fields)),
            primekey)
        return type.__new__(cls, name, bases, attrs)


class Model(dict, metaclass=ModelMeatclass):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)

    def getValueorDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value

    @classmethod
    async def FindAll(cls, where=None, args=None, **kw):
        ' 可以接受一个或多个where，多个时where和args使用tuple'
        sql = [cls.__select__]
        countwhere = 0

        if where:
            sql.append('where')
            if isinstance(where, str):
                sql.append(where)
                sql.append('= ?')
                countwhere = 1
            if isinstance(where, tuple):
                where = list(where)
                countwhere = len(where)
                for index, s in enumerate(where):
                    where[index] = s + ' = ?'
                sql.append(' and '.join(where))

        if args is None:
            args = []
        if isinstance(args, str):
            args = [args]
        if isinstance(args, tuple):
            args = list(args)

        if countwhere != len(args):
            raise ValueError('Need %s args but receive %s' % (countwhere, len(args)))

        orderBy = kw.get('orderBy', None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)
        limit = kw.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?, ?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        # execute SQL
        rs = await select(' '.join(sql), args)
        # 将每条记录作为对象返回
        return [cls(**r) for r in rs]

    # 返回主键的一条记录
    @classmethod
    async def Find(cls, pk):
        rs = await select('%s WHERE `%s` = ?' % (cls.__select__, cls.__prime_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    # 使用聚合查询如count(*)
    @classmethod
    async def FindNumber(cls, selectField, where=None, args=None):
        sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]
        countwhere = 0
        if where:
            sql.append('where')
            if isinstance(where, str):
                sql.append(where)
                sql.append('= ?')
                countwhere = 1
            if isinstance(where, tuple):
                where = list(where)
                countwhere = len(where)
                for index, s in enumerate(where):
                    where[index] = s + ' = ?'
                sql.append(' and '.join(where))

        if args is None:
            args = []
        if isinstance(args, str):
            args = [args]
        if isinstance(args, tuple):
            args = list(args)

        if countwhere != len(args):
            raise ValueError('Need %s args but receive %s' % (countwhere, len(args)))
        rs = await select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']

    # INSERT command
    async def insert(self):
        args = list(map(self.getValueorDefault, self.__fields__))
        args.insert(0, self.getValueorDefault(self.__prime_key__))
        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.info('Faield to insert record:affected rows: %s' % rows)

    # UPDATE command
    async def update(self):
        args = list(map(self.getValueorDefault, self.__fields__))
        args.append(self.getValue(self.__prime_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.info('Faield to update by primary_key:affectesd rows: %s' % rows)
            print('Faield to update by primary_key:affectesd rows: %s' % rows)

    # DELETE command
    async def delete(self):
        args = [self.getValue(self.__prime_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.info('Faield to remove by primary key:affected: %s' % rows)
