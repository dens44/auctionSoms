from peewee import Model, SqliteDatabase

database = SqliteDatabase('sqlite.db')


class BaseModel(Model):
    class Meta:
        database = database


from database.Users import UsersTable
from database.Lots import LotTable
from database.Orders import OrdersTable
from database.Files import FileTable
from database.Coupons import CouponTable
from database.UncheckMsgs import UncheckMsgsTable

UsersTable.create_table()
LotTable.create_table()
OrdersTable.create_table()
FileTable.create_table()
CouponTable.create_table()
UncheckMsgsTable.create_table()

# FileTable.check_files()

