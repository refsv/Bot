import telebot
import openai
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

token = '6336411080:AAGxxpb93OXaAmd03dveLik8oax160ezD5U'
openai.api_key = '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'

bot = telebot.TeleBot(token)

@bot.message_handler(commands=['start'])
def hello(message):
    bot.send_message(message.chat.id, 'Привет, я твой ChatGpt бот. Готов тебе помочь!')

@bot.message_handler(func=lambda message: True, content_types=['text'])
def main(message):
    reply = ''
    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=message.text,
        max_tokens=200,
        temperature=0.7,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        stop=None
    )

    if response and response.choices:
        reply = response.choices[0].text.strip()
    else:
        reply = 'Error'

    bot.send_message(message.chat.id, reply)

@bot.message_handler(commands=['reset'])
def reset(message):
    # Ваш код для обработки команды "reset"
    # Например, сброс состояния или очистка данных

    bot.send_message(message.chat.id, 'Выполнен сброс.')

bot.polling(none_stop=True, interval=0)







#
# #
# import openai
# import os
# import json
# import uuid
# from aiogram import Bot, types
# from aiogram.dispatcher import Dispatcher
# from aiogram.utils import executor
#
# token = '6336411080:AAGxxpb93OXaAmd03dveLik8oax160ezD5U'
# openai.api_key = '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'
#
#
# bot = Bot(token)
# dp = Dispatcher(bot)
#
#
# @dp.message_handler()
# async def send(message: types.Message):
#     response = openai.Completion.create(
#         model="text-davinci-003",
#         prompt='''class Log:\n    def init(self, path):\n        dirname = os.path.dirname(path)\n        os.makedirs(dirname, exist_ok=True)\n        f = open(path, "a+")\n\n        # Check that the file is newline-terminated\n        size = os.path.getsize(path)\n        if size > 0:\n            f.seek(size - 1)\n            end = f.read(1)\n            if end != "\n":\n                f.write("\n")\n        self.f = f\n        self.path = path\n\n    def log(self, event):\n        event["_event_id"] = str(uuid.uuid4())\n        json.dump(event, self.f)\n        self.f.write("\n")\n\n    def state(self):\n        state = {"complete": set(), "last": None}\n        for line in open(self.path):\n            event = json.loads(line)\n            if event["type"] == "submit" and event["success"]:\n                state["complete"].add(event["id"])\n                state["last"] = event\n        return state\n\n"""\nHere's what the above class is doing, explained in a concise way:\n1.''',
#         temperature=0.7,
#         max_tokens=150,
#         top_p=1.0,
#         frequency_penalty=0.0,
#         presence_penalty=0.0,
#         stop=None
#     )
#
#     await message.answer(response.choices[0].text)
#
#
# if __name__ == '__main__':
#     executor.start_polling(dp, skip_updates=True)
