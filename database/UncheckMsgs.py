from database import BaseModel
from peewee import *


class UncheckMsgsTable(BaseModel):
    msg_id = PrimaryKeyField(null=False)
    msg_text = TextField()

    @staticmethod
    def add_msg(msg_id, msg_text):
        return UncheckMsgsTable.create(msg_id=msg_id, msg_text=msg_text)


