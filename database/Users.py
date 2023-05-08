from database import BaseModel
from peewee import *


class UsersTable(BaseModel):
    user_id = PrimaryKeyField(null=False)
    name = TextField()
    telegram_id = IntegerField(unique=True)
    phone = TextField()
    email = TextField()
    address = TextField()

    @staticmethod
    def add_user(name, telegram_id, phone, email, address):
        return UsersTable.create(name=name, telegram_id=telegram_id, phone=phone, email=email, address=address)

    @staticmethod
    def get_user_by_id(id):
        return UsersTable.get(user_id=id)

    @staticmethod
    def delete_user_by_telegram_id(telegram_id):
        UsersTable.delete().where(UsersTable.telegram_id == telegram_id).execute()

    def print_user(self):
        print(self.user_id, self.name, self.telegram_id)

    def change_telegram_id(self, new_telegram_id):
        self.update(telegram_id=new_telegram_id).execute()

    @staticmethod
    def change_telegram_id_by_user_id(user_id, new_telegram_id):
        UsersTable.update(telegram_id=new_telegram_id).where(UsersTable.user_id == user_id).execute()
