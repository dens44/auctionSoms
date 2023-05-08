import os

from database import BaseModel
from peewee import *


class FileTable(BaseModel):
    file_id = PrimaryKeyField(null=False)
    telegram_file_id = TextField()
    file_name = TextField(unique=True)

    @staticmethod
    def check_files():
        for filename in os.listdir("data/"):
            print(filename)

    @staticmethod
    def get_file_id_by_file_name(name):
        file: FileTable = FileTable.get_or_none(file_name=name)
        if file is None:
            return None
        return file.telegram_file_id
