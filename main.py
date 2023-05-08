import re
from random import random, randint

from aiogram.utils import callback_data

import database
from database import UsersTable, LotTable, OrdersTable, FileTable, CouponTable, UncheckMsgsTable
from messages import get_message_text, main_keyboard

import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, \
    InputMediaPhoto

from aiogram.contrib.fsm_storage.files import JSONStorage

from messages import get_message_text
from settings import API_TOKEN, NEED_SAVE_LOGS_TO_FILE

import os

if NEED_SAVE_LOGS_TO_FILE:
    logging.basicConfig(filename="pizzabot.log",
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.DEBUG)

if "https_proxy" in os.environ:
    proxy_url = os.environ["https_proxy"]
    bot = Bot(token=API_TOKEN, proxy=proxy_url)
else:
    bot = Bot(token=API_TOKEN)

storage = JSONStorage("states.json")

dp = Dispatcher(bot, storage=storage)


class StateMachine(StatesGroup):
    main_state = State()
    registered_state = State()
    register_waiting_phone_state = State()
    register_waiting_email_state = State()
    register_waiting_address_state = State()
    order_waiting_count_state = State()
    order_waiting_coupon_state = State()
    order_waiting_address_state = State()
    order_waiting_accept_state = State()
    order_in_work_state = State()


async def send_photo(message, filename, caption=None, reply_markup=None):
    file_id = FileTable.get_file_id_by_file_name(filename)
    if file_id is None:
        # upload_file
        with open(filename, 'rb') as photo:
            result = await message.answer_photo(
                photo,
                caption=caption,
                reply_markup=reply_markup
            )
            file_id = result.photo[0].file_id
            FileTable.create(telegram_file_id=file_id, file_name=filename)
    else:
        await bot.send_photo(
            message.from_user.id,
            file_id,
            caption=caption,
            reply_markup=reply_markup
        )


async def send_media_group(message, filenames, reply_markup=None):
    files = []
    for filename in filenames:
        file_id = FileTable.get_file_id_by_file_name(filename)
        if file_id is None:
            with open(filename, 'rb') as photo:
                files.append(InputMediaPhoto(photo, caption=f"Лот {filename[-5]}"))
        else:
            files.append(InputMediaPhoto(file_id, caption=f"Лот {filename[-5]}"))

    await bot.send_media_group(
        message.from_user.id,
        files
    )


@dp.message_handler(commands=['start', 'help'], state="*")
async def send_welcome(message: types.Message):
    telegram_id = message.from_user.id
    user = UsersTable.get_or_none(telegram_id=telegram_id)

    if user is None:
        await StateMachine.register_waiting_phone_state.set()
        await message.reply(get_message_text("hello"))
    else:
        await StateMachine.registered_state.set()
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True) \
            .add("Войти", "Удалить аккаунт")
        await message.reply(get_message_text("registered"), reply_markup=markup)

    logging.info(f"{message.from_user.username}: {message.text}")


@dp.message_handler(commands='mediagroup', state="*")
async def send_mediagroup_handler(message: types.Message):
    await send_media_group(message,
                           filenames=["data/lot_1.jpg", "data/lot_2.jpg", "data/lot_3.jpg"])

    logging.info(f"{message.from_user.username}: {message.text}")


@dp.message_handler(state=StateMachine.registered_state)
async def handle_registered(message: types.Message, state: FSMContext):
    if message.text == "Удалить аккаунт":
        telegram_id = message.from_user.id
        UsersTable.delete_user_by_telegram_id(telegram_id=telegram_id)
        await StateMachine.register_waiting_phone_state.set()
        await message.reply(get_message_text("hello"))
    else:
        await state.finish()
        await StateMachine.main_state.set()
        await message.answer(get_message_text("enter_ok"), reply_markup=main_keyboard)


@dp.message_handler(state=StateMachine.register_waiting_phone_state)
async def handle_phone(message: types.Message, state: FSMContext):
    if re.fullmatch("[0-9]{10,}", message.text):
        async with state.proxy() as data:
            data["phone"] = message.text
        await message.reply(get_message_text("phone_ok"))
        await StateMachine.register_waiting_email_state.set()
    else:
        await message.reply(get_message_text("phone_bad"))


@dp.message_handler(state=StateMachine.register_waiting_email_state)
async def handle_email(message: types.Message, state: FSMContext):
    if re.fullmatch(".*@.*", message.text):
        async with state.proxy() as data:
            data["email"] = message.text
        markup = ReplyKeyboardMarkup(resize_keyboard=True).add("Пропустить")
        await message.reply(get_message_text("email_ok"), reply_markup=markup)
        await StateMachine.register_waiting_address_state.set()
    else:
        await message.reply(get_message_text("email_bad"))


@dp.message_handler(state=StateMachine.register_waiting_address_state)
async def handle_address(message: types.Message, state: FSMContext):
    if message.text != "":
        async with state.proxy() as data:
            data["address"] = message.text if message.text != "Пропустить" else "Не указан"
            user_info = data
        await message.reply(get_message_text("address_ok"), reply_markup=main_keyboard)

        UsersTable.add_user(
            name=f"{message.from_user.first_name} {message.from_user.last_name}",
            telegram_id=message.from_user.id,
            phone=user_info["phone"],
            email=user_info["email"],
            address=user_info["address"]
        )

        await state.finish()
        await StateMachine.main_state.set()
    else:
        await message.reply(get_message_text("address_bad"))


@dp.message_handler(state=StateMachine.main_state)
async def main_state_handler(message: types.Message, state: FSMContext):
    if message.text == "Вывести список лотов":
        for lot in LotTable.get_menu():
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Сделать шаг", callback_data=f"bid_lot_{lot.lot_id}"))

            await send_photo(
                message,
                f'data/lot_{lot.lot_id}.jpg',
                caption=get_message_text("lot_show",
                                         name=lot.name,
                                         desc=lot.desc,
                                         price=lot.price),
                reply_markup=markup
            )

    elif message.text == "Сделать шаг":
        await send_media_group(message,
                               filenames=["data/lot_1.jpg", "data/lot_2.jpg", "data/lot_3.jpg"])
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Лот 1", callback_data=f"bid_lot_1"))
        markup.insert(InlineKeyboardButton("Лот 2", callback_data=f"bid_lot_2"))
        markup.insert(InlineKeyboardButton("Лот 3", callback_data=f"bid_lot_3"))

        await message.answer("Лот 1, цена 100 руб. Лот 2, цена 200 руб. Лот 3, цена 300 руб. Выберите лот", reply_markup=markup)


@dp.callback_query_handler(text_startswith="bid_lot_", state=StateMachine.main_state)
async def main_state_handler(call: types.CallbackQuery, state: FSMContext):
    lot_id = call.data.split('_')[2]

    async with state.proxy() as data:
        data["order_lot_id"] = lot_id

    lot: LotTable = LotTable.get(lot_id=lot_id)
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)

    markup.add("отменить")
    markup.add("1", "2", "3", "4", "5", "10", "15")

    await call.message.answer(get_message_text("order_get_count", name=lot.name), reply_markup=markup)
    await StateMachine.order_waiting_count_state.set()
    await call.answer()


@dp.message_handler(state=StateMachine.order_waiting_count_state)
async def order_waiting_count_handler(message: types.Message, state: FSMContext):
    if message.text == "отменить":
        await state.finish()
        await message.answer("Заказ отменён", reply_markup=main_keyboard)
        await StateMachine.main_state.set()
    elif re.fullmatch("[0-9]{1,3}", message.text):
        count = int(message.text)
        async with state.proxy() as data:
            data["order_count"] = count
            data["coupon_shown"] = 0
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("отменить", "подтвердить")
        await message.answer(get_message_text("coupon_requested"), reply_markup=markup)
        await StateMachine.order_waiting_coupon_state.set()


@dp.message_handler(state=StateMachine.order_waiting_coupon_state)
async def order_waiting_coupon_handler(message: types.Message, state: FSMContext):
    if message.text == "отменить":
        await state.finish()
        await message.answer("Заказ отменён", reply_markup=main_keyboard)
        await StateMachine.main_state.set()
        return
    elif message.text == "подтвердить":
        order_discount = 1.0
    elif re.fullmatch("[0-9]{3,4}", message.text):
        coupon_shown = int(message.text)
        coupon_existed = CouponTable.get_or_none(coupon_id=coupon_shown)
        if coupon_existed is None:
            await message.reply(get_message_text("coupon_not_existed"))
            order_discount = 1.0
        else:
            await message.reply(get_message_text("coupon_is_existed", coupon_shown, 10))
            order_discount = 0.9
            async with state.proxy() as data:
                data["coupon_shown"] = coupon_shown
    else:
        await message.reply(get_message_text("coupon_not_existed"))
        order_discount = 1.0

    current_address = UsersTable.get(telegram_id=message.from_user.id).address
    async with state.proxy() as data:
        data["order_discount"] = order_discount
        data["order_address"] = current_address
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("отменить", "подтвердить")
    await message.answer(get_message_text("order_get_address", address=current_address),
                         reply_markup=markup)
    await StateMachine.order_waiting_address_state.set()


#
# @dp.message_handler(state=StateMachine.order_waiting_count_state)
# async def order_waiting_count_handler(message: types.Message, state: FSMContext):
#     if message.text == "отменить":
#         await state.finish()
#         await StateMachine.main_state.set()
#     elif re.fullmatch("[0-9]{1,3}", message.text):
#         count = int(message.text)
#         current_address = UsersTable.get(telegram_id=message.from_user.id).address
#         async with state.proxy() as data:
#             data["order_count"] = count
#             data["order_address"] = current_address
#         markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
#         markup.add("отменить", "подтвердить")
#         await message.answer(get_message_text("order_get_address", address=current_address), reply_markup=markup)
#         await StateMachine.order_waiting_address_state.set()


@dp.message_handler(state=StateMachine.order_waiting_address_state)
async def order_waiting_address_handler(message: types.Message, state: FSMContext):
    if message.text == "отменить":
        await state.finish()
        await message.answer("Заказ отменён", reply_markup=main_keyboard)
        await StateMachine.main_state.set()
        return
    elif message.text != "подтвердить":
        async with state.proxy() as data:
            data["order_address"] = message.text

    async with state.proxy() as data:
        address = data["order_address"]
        count = data["order_count"]
        lot_id = data["order_lot_id"]
        order_discount = data["order_discount"]

    lot: LotTable = LotTable.get(lot_id=lot_id)
    price = count * lot.price * order_discount
    async with state.proxy() as data:
        data["order_price"] = price
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("отменить", "подтвердить")

    await message.answer(
        get_message_text("order_accept", name=lot.name, count=count, price=price, address=address),
        reply_markup=markup)

    await StateMachine.order_waiting_accept_state.set()


@dp.message_handler(state=StateMachine.order_waiting_accept_state)
async def order_waiting_accept_handler(message: types.Message, state: FSMContext):
    if message.text == "отменить":
        await state.finish()
        await message.answer("Заказ отменён", reply_markup=main_keyboard)
        await StateMachine.main_state.set()
        return
    elif message.text == "подтвердить":
        async with state.proxy() as data:
            address = data["order_address"]
            count = data["order_count"]
            lot_id = data["order_lot_id"]
            price = data["order_price"]
        order = OrdersTable.create(
            user_id=UsersTable.get(telegram_id=message.from_user.id).user_id,
            lot_id=lot_id,
            lot_count=count,
            address=address,
            price=price,
            status="in_work"
        )
        async with state.proxy() as data:
            data["order_id"] = order.order_id
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Получил, спасибо!")
        await message.answer(get_message_text("order_in_work", order_number=order.order_id), reply_markup=markup)
        await StateMachine.order_in_work_state.set()


@dp.message_handler(state=StateMachine.order_in_work_state)
async def order_in_work_handler(message: types.Message, state: FSMContext):
    if message.text == "Получил, спасибо!":
        async with state.proxy() as data:
            order_id = data["order_id"]
            coupon_shown = data["coupon_shown"]
        OrdersTable.set_order_done(order_id)
        CouponTable.delete_coupon_by_coupon_id(coupon_shown)
        await state.finish()
        await StateMachine.main_state.set()
        await message.answer(get_message_text("order_done"), reply_markup=main_keyboard)
        coupon_id = randint(100, 1000)
        CouponTable.add_coupon(coupon_id=coupon_id, coupon_discount=10)
        await message.answer(get_message_text("coupon_created", coupon_id))
        return
    elif re.fullmatch(".*(не*|когда|почему|ни[кч].*|задерж.*|сколь.*|курьер.*|врем.*|достав.*|ещ.*|жд.*|оп[оа]зд*).*",
                      message.text.casefold()):
        await message.answer(get_message_text("order_delayed"))
    else:
        await message.answer(get_message_text("order_fails"))
        uncheck_msg = UncheckMsgsTable.create(msg_text=message.text)
        print(uncheck_msg.msg_text)

def main():
    executor.start_polling(dp, skip_updates=True)


if __name__ == '__main__':
    main()
