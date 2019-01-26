from src import *


@database.connection_context()
def prepare_database():
    need_create = []
    for model in model_list:
        if not database.table_exists(model):
            need_create.append(model)

    database.create_tables(need_create)


prepare_database()
