import time
import datetime
import traceback
import peewee

from .model import database, model_list
from .model import Account, Tieba, Log
from .tieba_operator import TiebaOperator, SignResult


tieba_operator_pool = {}


def get_operator(account: Account) -> TiebaOperator:
    assert not account.paused
    if account.id in tieba_operator_pool:
        return tieba_operator_pool[account.id]
    else:
        operator = TiebaOperator(account)
        tieba_operator_pool[account.id] = operator
        return operator


def prepare_database():
    need_create = []
    for model in model_list:
        if not model.table_exists():
            need_create.append(model)

    print('Creating tables: ' + ', '.join([table._meta.table_name for table in need_create]))
    database.create_tables(need_create)


@database.atomic()
def do_fetch_list_task(account: Account):
    operator = get_operator(account)

    for tieba in Tieba.select().where(Tieba.account == account):
        if tieba.paused:
            pass
        else:
            tieba.cancelled = True
            tieba.save()

    tieba_list = operator.fetch_favorite_tieba_list()

    for tieba_name in tieba_list:
        try:
            tieba = Tieba.get(account=account, name=tieba_name)
            force_insert = False
        except peewee.DoesNotExist:
            tieba = Tieba()
            tieba.account = account
            tieba.name = tieba_name
            tieba.paused = False
            force_insert = True

        if tieba.paused:
            pass
        else:
            tieba.cancelled = False
            tieba.save(force_insert=force_insert)

    account.last_fetch_list_date = datetime.date.today()
    account.save()

    log = Log()
    log.time = datetime.datetime.now()
    log.content = '成功更新账户“' + account.name + '”的贴吧列表'
    log.save()


def fetch_list_task():
    for account in Account.select():

        if account.paused:
            pass
        else:
            if account.last_fetch_list_date is None:
                do_fetch_list_task(account)
            elif datetime.date.today() > datetime.date.fromisoformat(account.last_fetch_list_date):
                do_fetch_list_task(account)
            else:
                pass


def sign_task():
    for account in Account.select():
        if account.paused:
            pass
        else:
            operator = get_operator(account)

            need_sign_list = (
                Tieba
                    .select()
                    .where(
                        (Tieba.account == account)
                        &(Tieba.paused == False)
                        &(Tieba.cancelled == False)
                        &((Tieba.last_sign_date == None)|(Tieba.last_sign_date < datetime.date.today()))
                    )
            )
            for tieba in need_sign_list:
                with database.atomic():
                    result = operator.sign_tieba(tieba.name)
                    if (result == SignResult.success) or (result == SignResult.already_signed):
                        tieba.last_sign_date = datetime.date.today()
                    tieba.save()

                log = Log()
                log.time = datetime.datetime.now()
                common_str = '账户：“' + account.name + '”，贴吧：“' + tieba.name + '”，'
                log.content = common_str + result.value
                log.save()


def limit_retry(task: callable, retry_limit: int = 10):
    counter = 0
    while counter < retry_limit:
        try:
            task()
            break
        except Exception:
            counter += 1

            log = Log()
            log.time = datetime.datetime.now()
            log.content = '遇到错误，重试次数：' + counter + '，错误信息：' + traceback.format_exc()
            log.save()

            continue


def everyday_task():
    limit_retry(lambda: fetch_list_task(), 10)
    limit_retry(lambda: sign_task(), 10)


def do_auto_task():

    with database.connection_context():
        prepare_database()

    last_date = None
    while True:
        current_date = datetime.date.today()
        if (last_date is None) or (current_date > last_date):

            with database.connection_context():
                everyday_task()

            last_date = current_date

        next_day_iso = (current_date + datetime.timedelta(days=1)).isoformat()
        next_day_datetime = datetime.datetime.fromisoformat(next_day_iso)
        total_seconds = (next_day_datetime - datetime.datetime.now()).total_seconds()
        time.sleep(total_seconds)
