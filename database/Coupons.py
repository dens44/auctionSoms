from database import BaseModel
from peewee import *


class CouponTable(BaseModel):
    coupon_id = PrimaryKeyField(null=False)
    coupon_discount = IntegerField()


    @staticmethod
    def add_coupon(coupon_id, coupon_discount):
        return CouponTable.create(coupon_id=coupon_id, coupon_discount=coupon_discount)


    @staticmethod
    def get_coupon_by_coupon_id(id):
        return CouponTable.get(couopon_id=id)


    @staticmethod
    def delete_coupon_by_coupon_id(id):
        CouponTable.delete().where(CouponTable.coupon_id == id).execute()