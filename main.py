import os
import sys
import config
import openai
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters import ContentTypeFilter, Command
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base


token = 'YOUR_TELEGRAM_BOT_TOKEN'
openai.api_key = 'YOUR_OPENAI_API_KEY'

bot = Bot(token)
dp = Dispatcher(bot)

engine = create_engine('sqlite:///bot_stats.db')  # Создание и подключение к базе данных SQLite
Base = declarative_base()


# Определение моделей таблиц базы данных
class Dialog(Base):
    __tablename__ = 'dialogs'
    id = Column(Integer, primary_key=True)
    message = Column(String)
    chat_id = Column(Integer, ForeignKey('chats.id'))
    chat = relationship("Chat", back_populates="dialogs")


class Chat(Base):
    __tablename__ = 'chats'
    id = Column(Integer, primary_key=True)
    dialogs = relationship("Dialog", back_populates="chat")

    def __init__(self, dialogs=None):
        self.dialogs = dialogs if dialogs is not None else []


class Stats(Base):
    __tablename__ = 'stats'
    id = Column(Integer, primary_key=True)
    message_count = Column(Integer, default=0)


Base.metadata.create_all(engine)  # Создание таблиц в базе данных
Session = sessionmaker(bind=engine)
session = Session()

bot_active = True  # Флаг активности бота, изначально установлен в True


def initialize_stats():
    stats = session.query(Stats).first()
    if not stats:
        stats = Stats()
        session.add(stats)
        session.commit()


def get_bot_state(chat_id):
    chat = session.query(Chat).filter_by(id=chat_id).first()
    if chat:
        return chat.dialogs
    return []


def update_bot_state(chat_id, dialogs):
    chat = session.query(Chat).filter_by(id=chat_id).first()
    if chat:
        chat.dialogs = []  # Создаем новый пустой список
        for dialog in dialogs:
            chat.dialogs.append(dialog)
        session.commit()


initialize_stats()


@dp.message_handler(commands=['start'])
async def hello(message: types.Message):
    global bot_active  # Используем глобальную переменную

    if not bot_active:  # Проверяем, активен ли бот
        bot_active = True  # Устанавливаем флаг активности бота в True
        await message.answer('Бот активирован и готов к работе.')
        return

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        KeyboardButton(text='/reset'),
        KeyboardButton(text='/end'),
        KeyboardButton(text='/stats'),
        KeyboardButton(text='/info')
    ]
    keyboard.add(*buttons)

    await message.answer('Привет, я твой ChatGPT бот. Готов тебе помочь!', reply_markup=keyboard)


@dp.message_handler(commands=['reset'])
async def reset(message: types.Message):
    chat_id = message.chat.id
    chat = session.query(Chat).filter_by(id=chat_id).first()
    if chat:
        dialogs = chat.dialogs
        if dialogs:
            dialogs.clear()
            update_bot_state(chat_id, dialogs)
    await message.answer('Выполнен сброс.')


@dp.message_handler(commands=['end'])
async def end_conversation(message: types.Message):
    global bot_active  # Используем глобальную переменную

    bot_active = False  # Устанавливаем флаг активности бота в False

    dialogs = get_bot_state(message.chat.id)
    dialogs.clear()
    update_bot_state(message.chat.id, dialogs)
    await message.answer('Диалог завершен.')


@dp.message_handler(Command(['reset', 'end', 'stats', 'info']))
async def handle_commands(message: types.Message):
    if message.get_command() == '/reset':
        await reset(message)
    elif message.get_command() == '/end':
        await end_conversation(message)
    elif message.get_command() == '/stats':
        stats = session.query(Stats).first()
        dialogs = get_bot_state(message.chat.id)
        stats_message = f'Статистика бота:\n' \
                        f'Всего диалогов: {len(dialogs)}\n' \
                        f'Всего сообщений: {stats.message_count}'

        await message.answer(stats_message)
    elif message.get_command() == '/info':
        info_message = '''Ціль розробки полягає у створенні автоматизованого чат-бота, здатного надавати консультаційну та підтримку користувачам у різних сферах бізнесу.

                    Бот був розроблений групою №5 студентів першого курсу університету I.I. Мечникова. 

                    У складі команди були:

                    • Коцаренко Євген
                    • Константинов Олександр
                    • Шестов Микита
                    • Курило Кирил'''

        await message.answer(info_message)


@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def handle_text(message: types.Message):
    global bot_active  # Используем глобальную переменную

    if not bot_active:  # Проверяем, активен ли бот
        await message.answer('Бот сейчас не работает. Нажмите /start, чтобы активировать бота.')
        return

    stats = session.query(Stats).first()
    stats.message_count += 1
    session.commit()

    chat_id = message.chat.id
    dialogs = get_bot_state(chat_id)

    reply = ''
    if not dialogs:
        chat = Chat()
        session.add(chat)
        session.commit()
        chat_id = chat.id
    else:
        chat = session.query(Chat).filter_by(id=chat_id).first()

    prompt = message.text

    prompt_with_user_message = f"{prompt}, {message.from_user.first_name}!"

    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt_with_user_message,
        max_tokens=150,
        temperature=0.7,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        stop=None
    )

    if response and response.choices:
        reply = response.choices[0].text.strip()

    dialog = Dialog(message=reply, chat_id=chat_id)
    chat.dialogs.append(dialog)
    session.add(dialog)
    session.commit()

    await message.answer(reply)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
