from database import BaseModel
from peewee import *


class LotTable(BaseModel):
    lot_id = PrimaryKeyField(null=False)
    name = TextField()
    desc = TextField()
    price = IntegerField()

    @staticmethod
    def get_menu():
        return LotTable.select().execute()
