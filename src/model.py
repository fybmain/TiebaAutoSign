from peewee import Model, CompositeKey
from peewee import CharField, TextField, ForeignKeyField, DateTimeField, DateField, BooleanField
from playhouse import db_url


DATABASE_URL = 'sqlite:///TiebaAutoSign.db'
database = db_url.connect(url=DATABASE_URL)


class BaseModel(Model):
    class Meta:
        database = database


class Account(BaseModel):
    name = CharField(null=False, unique=True)
    cookie = TextField(null=False)

    paused = BooleanField(null=False, default=False)

    last_fetch_list_date = DateField(formats='%Y-%m-%d', null=True)


class Tieba(BaseModel):
    account = ForeignKeyField(Account, null=False)
    name = CharField(null=False)

    paused = BooleanField(null=False, default=False)

    cancelled = BooleanField(null=False)
    last_sign_date = DateField(formats='%Y-%m-%d',null=True)

    class Meta:
        primary_key = CompositeKey('account', 'name')


class Log(BaseModel):
    time = DateTimeField(formats='%Y-%m-%d %H:%M:%S.%f', null=False)
    content = TextField(null=False)


model_list = [
    Account,
    Tieba,
    Log,
]
