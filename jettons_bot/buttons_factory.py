from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters.callback_data import CallbackData
from jettons_bot.actions import ItemAction, ItemsListAction
from jettons_bot.callbacks import (
    GetJettonsCallback,
    GiveDateCallback, 
    GiveawayCallback, 
    GiveDeleteTimeCallback,
    GiveSubCheckHours)

from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.deep_linking import create_start_link
from jettons_bot.get_message import get_text
from typing import Union
from typing import Any, Dict, List
import datetime as dt
from platform import system
from locale import setlocale, LC_ALL

setlocale(LC_ALL, 'ru_RU.UTF-8')

current_os = system()
if current_os == "Windows":
    time_sep = '#'
else:
    time_sep = '-'

def genitive_month_name(month: int):
    month_names = [
        None,
        'января',
        'февраля',
        'марта',
        'апреля',
        'мая',
        'июня',
        'июля',
        'августа',
        'сентября',
        'октября',
        'ноября',
        'декабря'
    ]

    return month_names[month]

async def split_array_fixed(arr: list, size: int):
    return [arr[i:i+size] for i in range(0, len(arr), size)]

async def get_items_keyboard(
    items: list[tuple], 
    page_size: int, 
    page_index: int, 
    item_callback_data: CallbackData,
    items_list_callback_data: CallbackData):
    
    builder = InlineKeyboardBuilder()
    
    items = await split_array_fixed(items, page_size)

    if page_index >= len(items):
        page_index = len(items) - 1

    for row in items[page_index]:
        call_data = item_callback_data(
            action = ItemAction.get_item, 
            id = row[0])
        
        builder.button(text=row[1], callback_data=call_data)
    
    builder.adjust(1)

    if len(items) > 1:
        next_page_data = items_list_callback_data(
            action = ItemsListAction.get_list, 
            page_index = page_index + 1)
        next_page_button = InlineKeyboardButton(text="След ▶️", callback_data=next_page_data)

        prev_page_data = items_list_callback_data(
            action = ItemsListAction.get_list, 
            page_index = page_index - 1)
        prev_page_button = InlineKeyboardButton(text="Пред ◀️", callback_data=prev_page_data)

        if page_index == 0:
            builder.row(next_page_button)
        elif page_index == len(items) - 1:
           builder.row(prev_page_button)
        else:
            builder.row(
                prev_page_button,
                next_page_button
            )
    
    return builder.as_markup()

async def remove_item_button(
    item_id: int,
    item_callback_data: CallbackData):
    
    builder = InlineKeyboardBuilder()
    builder.button(
        text = "Удалить из спиcка",
        callback_data = item_callback_data(
            action = ItemAction.remove_item, 
            id = item_id)
    )

    return builder.as_markup()

async def confirm_remove_buttons(
    item_id: int,
    item_callback_data: CallbackData):
    
    builder = InlineKeyboardBuilder()
    builder.button(
        text = "Подтвердите удаление",
        callback_data = item_callback_data(
            action = ItemAction.confirm_remove_item, 
            id = item_id)
    )
    builder.button(
        text = "Отмена",
        callback_data = item_callback_data(
            action = ItemAction.cancel_removing, 
            id = item_id)
    )

    builder.adjust(1)

    return builder.as_markup()

async def swtich_button(callback: CallbackQuery):
    splitted_data = callback.data.split(':')
    if len(splitted_data) == 1:
        index = 0
    else:
        index = 1

    if splitted_data[index].endswith('_'):
        splitted_data[index] = splitted_data[index][:-1]
    else:
        splitted_data[index] = f"{splitted_data[index]}_"

    for button in callback.message.reply_markup.inline_keyboard:
        if button[0].callback_data == callback.data:
            button[0].callback_data = ':'.join(splitted_data)
            break
        
    new_buttons = callback.message.reply_markup
    try:
        await callback.message.edit_reply_markup(reply_markup=new_buttons)
    except TelegramBadRequest:
        text = await get_text("common/do_not_hurry")
        await callback.answer(text, show_alert=True)

async def get_options_buttons(
    item_callback_data: CallbackData,
    items_list_callback_data: CallbackData, 
    item_name: str):
    
    builder = InlineKeyboardBuilder()

    builder.button(
        text=f"Мои {item_name}ы",
        callback_data=items_list_callback_data(
            action = ItemsListAction.get_list,
            page_index = 0))
    builder.button(
        text=f"Добавить {item_name}", 
        callback_data=item_callback_data(
            action = ItemAction.add_item, 
            id = 0))

    builder.adjust(1)

    return builder.as_markup()

async def give_options_buttons(
    item_callback_data: CallbackData,
    items_list_callback_data: CallbackData, 
    item_name: str):
    
    builder = InlineKeyboardBuilder()

    builder.button(
        text=f"Мои {item_name}и",
        callback_data=items_list_callback_data(
            action = ItemsListAction.get_list,
            page_index = 0))
    builder.button(
        text=f"Добавить {item_name}у", 
        callback_data=item_callback_data(
            action = ItemAction.add_item, 
            id = 0))

    builder.adjust(1)

    return builder.as_markup()

async def add_give_button():
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text=f"Добавить раздачу", 
        callback_data=GiveawayCallback(
            action = ItemAction.add_item, 
            id = 0))
    builder.adjust(1)

    return builder.as_markup()

async def get_gieveaways_options_buttons(
    item_callback_data: CallbackData,
    items_list_callback_data: CallbackData):
    
    builder = InlineKeyboardBuilder()

    builder.button(
        text=f"Запланированные раздачи",
        callback_data=items_list_callback_data(
            action = ItemsListAction.get_scheduled_list,
            page_index = 0))
    builder.button(
        text=f"Созданные раздачи",
        callback_data=items_list_callback_data(
            action = ItemsListAction.get_list,
            page_index = 0))
    builder.button(
        text=f"Добавить раздачу", 
        callback_data=item_callback_data(
            action = ItemAction.add_item, 
            id = 0))

    builder.adjust(1)

    return builder.as_markup()

add_channel_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Добавить канал", callback_data="add_channel")]])

add_post_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Добавить пост", callback_data="add_post")]])

transaction_types = ReplyKeyboardMarkup(
    keyboard=
        [[KeyboardButton(text="Ончейн")],
        [KeyboardButton(text="Рокет")],
        [KeyboardButton(text="Оба")],
        [KeyboardButton(text="Назад")]],
    resize_keyboard = True)

confirm_post_button = ReplyKeyboardMarkup(
    keyboard=
        [[KeyboardButton(text="Подтвердить пост")],
        [KeyboardButton(text="Изменить пост")]],
    resize_keyboard=True)

confirm_give_buttons = ReplyKeyboardMarkup(
    keyboard=
        [[KeyboardButton(text="Подтвердить раздачу")],
        [KeyboardButton(text="Изменить раздачу")]],
    resize_keyboard=True)

cancel_button = ReplyKeyboardMarkup(
    keyboard=
        [[KeyboardButton(text="Назад")]],
    resize_keyboard=True)

async def change_post_buttons():
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="Название")
    builder.button(text="Пост")
    builder.button(text="Текст кнопки")
    builder.button(text="Назад")

    builder.adjust(1)

    markup = builder.as_markup()
    markup.resize_keyboard = True

    return markup

async def change_give_buttons():
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="Название")
    builder.button(text="Адрес жетона")
    builder.button(text="Пост")
    builder.button(text="Канал")
    builder.button(text="Дата")
    builder.button(text="Время")
    builder.button(text="Время удаления")
    builder.button(text="Проверка подписки")
    builder.button(text="Количество токенов на руки")
    builder.button(text="Количество раздач")
    builder.button(text="Назад")

    builder.adjust(2, repeat=True)

    markup = builder.as_markup()
    markup.resize_keyboard = True

    return markup

async def post_buttons(text: str, post_id: int, callback: CallbackData):
    builder = InlineKeyboardBuilder()

    builder.button(
        text=text,
        callback_data=GetJettonsCallback(id=-1, wallet_type="none")
    )

    buttons_dict = {
        "Изменить название": ItemAction.change_title,
        "Изменить пост": ItemAction.change_post,
        "Изменить текст кнопки": ItemAction.change_button_text,
        "Удалить пост": ItemAction.remove_item
    }
    
    for text, action in buttons_dict.items():
        builder.button(
            text=text,
            callback_data=callback(
                id=post_id,
                action=action)
        )
    
    builder.adjust(1)

    return builder.as_markup()

async def get_jettons_button(give_id: int, button_text: str, bot):
    link = await create_start_link(bot, str(give_id), encode=True)

    builder = InlineKeyboardBuilder()

    builder.button(
        text=button_text,
        url=link
    )

    return builder.as_markup()

async def get_url_button(link: str, text: str):
    builder = InlineKeyboardBuilder()

    builder.button(
        text=text,
        url=link
    )

    return builder.as_markup()

async def get_wallet_type_buttons(give_id: int, callback: CallbackQuery):
    builder = InlineKeyboardBuilder()

    builder.button(
        text="TonKeeper",
        callback_data=callback(
            id=give_id,
            wallet_type="tonkeeper"
        )
    )
    builder.button(
        text="TonHub",
        callback_data=callback(
            id=give_id,
            wallet_type="tonhub"
        )
    )

    builder.adjust(1)

    return builder.as_markup()

async def create_week_keyboard():
    now = dt.datetime.now()
    builder = InlineKeyboardBuilder()
    
    for i in range(7):
        day = now + dt.timedelta(days=i)
        month = genitive_month_name(day.month)
        button_text = day.strftime(f"%a, %{time_sep}d {month}")
        builder.button(
            text=button_text, 
            callback_data=GiveDateCallback(day=day.day, month=day.month, year=day.year))
    
    builder.adjust(1)

    return builder.as_markup()

async def when_delete_buttons():
    builder = InlineKeyboardBuilder()
    
    for time in range(12,50,12):
        builder.button(
            text=f"{time} ч.",
            callback_data=GiveDeleteTimeCallback(
                hours=time
            ))
    
    builder.adjust(1)

    return builder.as_markup()

async def sub_check_buttons():
    builder = InlineKeyboardBuilder()

    builder.button(
        text="1 день",
        callback_data=GiveSubCheckHours(
            hours=24
        ))
    
    builder.button(
        text="7 дней",
        callback_data=GiveSubCheckHours(
            hours=24*7
        ))
        
    builder.button(
        text="2 недели",
        callback_data=GiveSubCheckHours(
            hours=24*14
        ))
    
    builder.button(
        text="1 мес.",
        callback_data=GiveSubCheckHours(
            hours=24*30
        ))
    
    builder.button(
        text="2 мес.",
        callback_data=GiveSubCheckHours(
            hours=24*60
        ))
    
    builder.button(
        text="6 мес.",
        callback_data=GiveSubCheckHours(
            hours=24*180
        ))
    
    builder.button(
        text="Без проверки",
        callback_data=GiveSubCheckHours(
            hours=0
        ))

    builder.adjust(1)

    return builder.as_markup()

async def resend_post_button(give_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Отправить еще раз",
        callback_data=GiveawayCallback(
            id=give_id, 
            action=ItemAction.resend_post))
    
    return builder.as_markup()

async def paymend_buttons(jettons_url, ton_url):
    builder = InlineKeyboardBuilder()
    if jettons_url:
        builder.button(
            text="Отправить жетоны",
            url=jettons_url)
    if ton_url:
        builder.button(
            text="Отправить TON",
            url=ton_url
        )
    builder.adjust(1)

    return builder.as_markup()

async def stop_giveaway_button(give_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Остановить раздачу",
        callback_data=GiveawayCallback(
            id=give_id,
            action="stop"
        ))
    builder.adjust(1)

    return builder.as_markup()

async def confirm_stopping_button(give_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Подтвердить остановку",
        callback_data=GiveawayCallback(
            id=give_id,
            action="yes_stop"
        ))
    builder.button(
        text="Отмена",
        callback_data=GiveawayCallback(
            id=give_id,
            action="no_stop"
        )
    )