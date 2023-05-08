import logging
import aiogram
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = '5990978589:AAE6hd1_zfIUBqwmrqbqdUqeJGzvcFhEc3Q'
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot)

starting_bid = 100
current_bid = starting_bid
current_highest_bidder = None

async def start(message: types.Message):
    await message.reply('Welcome to the coin auction! The starting bid is {} coins.'.format(starting_bid))

async def bid(message: types.Message):
    global current_bid, current_highest_bidder
    user_bid = int(message.text.split()[1])
    if user_bid > current_bid:
        current_bid = user_bid
        current_highest_bidder = message.from_user
        response_message = '{} coins! New highest bid by @{}.'.format(current_bid, current_highest_bidder.username)
        await bot.send_message(chat_id=message.chat.id, text=response_message)
    else:
        await message.reply('Sorry, your bid of {} coins is not higher than the current highest bid of {} coins.'.format(user_bid, current_bid))

async def handle_message(message: types.Message):
    await message.reply('Sorry, I didn\'t understand that command. Please use /start or /bid.')

# Handlers
dispatcher.register_message_handler(start, commands=['start'])
dispatcher.register_message_handler(bid, commands=['bid'])
dispatcher.register_message_handler(handle_message)


# Define the two buttons
nearest_bid = current_bid + int(current_bid * 0.01)  # Calculate the nearest integer for 1% of the current bid
btn_nearest_bid = InlineKeyboardButton(text=f"Place Bid: {nearest_bid}", callback_data=f"bid:{nearest_bid}")
btn_custom_bid = InlineKeyboardButton(text="Place Custom Bid", callback_data="custom_bid")

# Add the buttons to an InlineKeyboardMarkup
markup = InlineKeyboardMarkup(row_width=2)
markup.add(btn_nearest_bid, btn_custom_bid)


# Start the bot
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dispatcher, skip_updates=True)


