from os import getenv, remove
from dotenv import load_dotenv
from uuid import uuid4
from sys import argv
import datetime as dt
from pytoniq import LiteClient, LiteBalancer
from pytoniq_core.boc.address import AddressError
from json import load

from aiogram import Router, F
from aiogram import Bot
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.filters.command import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext as fsm
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types.reply_keyboard_remove import ReplyKeyboardRemove
from aiogram.utils.markdown import text as Txt
from aiogram.utils.deep_linking import decode_payload

from jettons_bot.crud import *
from jettons_bot.buttons_factory import *
from jettons_bot.callbacks import (
    GiveawayCallback, 
    GiveawaysListCallback,
    GivePostCallback,
    GivePostsListCallback, 
    GiveChannelCallback,
    GiveChannelsListCallback)
from jettons_bot.delete_giveaway import delete_giveaway
from jettons_bot.start_giveaway import start_giveaway

from pyrogram import Client
from pyrogram.enums import ChatMemberStatus

from datetime import datetime

load_dotenv()

from connect_and_check import TonConnect
from connect_and_check import generate_qr_code

setlocale(LC_ALL, 'ru_RU.UTF-8')

class States(StatesGroup):
    giveaway_title = State()
    jetton_address = State()
    transaction_type = State()
    onchain_count = State()
    rocket_count = State()
    both_onchain = State()
    both_rocket = State()
    gives_count = State()
    giveaway_post = State()
    giveaway_channel = State()
    date = State()
    time = State()
    delete_after = State()
    sub_hours = State()
    top_up_pool = State()
    
    change_giveaway = State()
    change_giveaway_title = State()
    change_giveaway_post = State()
    change_giveaway_channel = State()
    change_time = State()
    change_date = State()
    change_delete_after = State()
    change_sub_hours = State()
    change_jetton_address = State()
    change_gives_count = State()
    change_tr_type = State()
    confirm_giveaway = State()
    change_jettons_count = State()

router = Router()

bot = Bot(token=getenv("TEST_BOT_TOKEN"))

pg_bot = Client(".pg_bot",api_id = 25957850, api_hash="76689b3424fd067c4482dc58c32e2265", bot_token=getenv("TEST_BOT_TOKEN"))
pg_bot.start()

handler_name = "giveaways"
db_path = f"jettons_bot/databases/{handler_name}.db"
posts_db_path = f"jettons_bot/databases/posts.db"
float_reg_exp = "\d+([\.,]?\d+)?"

async def check_user_status(message: Message, give_id: int):

    try:
        give_id = int(give_id)
    except ValueError:
        text = await get_text(f"{handler_name}/not_valid_giveaway")
        message.answer(text)

        return False
    
    queue = await read(
        db_path="jettons_bot/databases/claims_queue.db",
        table="claims_queue",
        columns="*",
        conditions=f"user_id={message.chat.id} AND give_id={give_id}"
    )

    if queue:
        text = await get_text(f"{handler_name}/already_claimed")
        message.answer(text)

        return
    
    data = await read(
        db_path=db_path,
        table=handler_name,
        columns="channel_id, sub_hours",
        conditions=f"id={give_id}, status='active'"
    )

    if not data:
        text = await get_text(f"{handler_name}/not_valid_giveaway")
        message.answer(text)
        
        return False

    channel_id = data[0]

    try:
        channel = await bot.get_chat(channel_id)
    except TelegramForbiddenError:
        text = await get_text(f"{handler_name}/not_valid_giveaway")
        message.answer(text)
        
        return False
    
    try:
        member = await pg_bot.get_chat_member(channel_id, message.chat.id)
    except:
        message.answer(f"К сожалению, вы не являтесь подписчиком канала {channel.title} и не можете получить токены")
        
        return False
    
    if (member.status == ChatMemberStatus.BANNED) or \
        (member.status == ChatMemberStatus.LEFT):
        message.answer(f"К сожалению, вы не являтесь подписчиком канала {channel.title} и не можете получить токены")

        return False
    
    try:
        sub_hours = int(data[1])
    except ValueError:
        sub_hours = None

    if not (sub_hours is None):
        sub_dt = member.joined_date
        user_sub_hours = (datetime.now() - sub_dt).days*24

        if user_sub_hours < sub_hours:
            sub_td = dt.timedelta(hours=sub_hours)
            if sub_td.days >= 30:
                sub_time = f"{int(sub_td.days/30)} мес."
            elif sub_td.days >= 7:
                sub_time = f"{int(sub_td.days/7)} нед."
            else:
                sub_time = f"{sub_td.days} д."

            user_sub_td = dt.timedelta(hours=user_sub_hours)
            if user_sub_td.days >= 30:
                user_sub_time = f"{int(sub_td.days/30)} мес."
            elif user_sub_td.days >= 7:
                user_sub_time = f"{int(sub_td.days/7)} нед."
            else:
                user_sub_time = f"{sub_td.days} д."

            message.answer(f"Вы должны быть подписаны на канал {channel.title} не менее {sub_time} чтобы получить токены\nВы подписаны: {user_sub_time}")

            return False

    return True

async def get_giveaway_data(data: dict):
    date = dt.datetime.strptime(data.get("date"), "%d/%m/%Y")
    month = genitive_month_name(date.month)
    date = date.strftime(f"%{time_sep}d {month}")

    if not data.get("sub_hours"):
        sub_time = "нет"
    else:
        sub_hours = int(data.get("sub_hours"))
        sub_td = dt.timedelta(hours=sub_hours)
        if sub_td.days >= 30:
            sub_time = f"{int(sub_td.days/30)} мес."
        elif sub_td.days >= 7:
            sub_time = f"{int(sub_td.days/7)} нед."
        else:
            sub_time = f"{sub_td.days} д."
    
    if data.get("onchain_count"):
        onchain_count = data.get("onchain_count")
    else:
        onchain_count = 0
    
    if data.get("rocket_count"):
        rocket_count = data.get("rocket_count")
    else:
        rocket_count = 0 


    text_list = [
        f'{data.get("giveaway_title")}',
        f'Пост: {data.get("post_giveaway_title")}',
        f'Канал {data.get("channel_giveaway_title")}',
        f'Дата: {date}',
        f'Время: {data.get("time")}',
        f'Удалить через: {data.get("delete_hours")} ч.',
        f'Проверка подписки: {sub_time}',
        f'Жетон: {data.get("jetton_address")}',
        f'Количество жетонов в руки: {onchain_count}',
        f'Количество раздач: {data.get("gives_count")}']

    for line in text_list:
        line = Txt(line)

    text_list[0] = f"<b>{text_list[0]}</b>"

    return '\n\n'.join(text_list)

@router.message(Command(handler_name))
async def gives_options(message: Message, state: fsm):
    await state.clear()

    if message.chat.type == "private":
        text = await get_text(f"{handler_name}/giveaways_options")
        keyboard = await give_options_buttons(
            item_callback_data=GiveawayCallback,
            items_list_callback_data=GiveawaysListCallback,
            item_name="раздач")
    else:
        text = await get_text(f"common/only_private")
        keyboard = ReplyKeyboardRemove()
    
    await message.answer(text, reply_markup=keyboard)

@router.callback_query(GiveawayCallback.filter(F.action.in_({ItemAction.add_item, ItemAction.add_item_})))
async def add_give(callback: CallbackQuery, state: fsm):
    await state.update_data(onchain_count = None)
    # await state.update_data(rocket_count = None)

    await state.set_state(States.giveaway_title)

    text = await get_text(f"{handler_name}/enter_giveaway_title")
    await callback.message.answer(text, reply_markup=cancel_button)

    await swtich_button(callback)

@router.message(F.text, States.giveaway_title)
async def giveaway_title(message: Message, state: fsm):
    user_id = message.chat.id

    if message.text.lower() == "назад":
        await state.clear()
        await gives_options(message, state)
        
        mes = await message.answer("⁠⁠", reply_markup=ReplyKeyboardRemove())
        await mes.delete()

        return

    if len(message.text) > 20:
        text = await get_text(f"{handler_name}/giveaway_title_too_long")
        await message.answer(text)
        
        return

    await state.set_state(States.giveaway_post)
    await state.update_data(giveaway_title=message.text)

    posts = await read("jettons_bot/databases/posts.db", "posts", "id, title", f"user_id={user_id}")
    if not posts:
        text = await get_text(f"{handler_name}/no_posts")
        await message.answer(text, reply_markup=add_post_button)
        await state.clear()
    else:
        keyboard = await get_items_keyboard(
            items = posts,
            page_size = 10, 
            page_index = 0, 
            item_callback_data = GivePostCallback, 
            items_list_callback_data = GivePostsListCallback)

        text = await get_text(f"{handler_name}/choose_post")
        await message.answer(text, reply_markup=keyboard)

@router.callback_query(GivePostCallback.filter(F.action.in_({ItemAction.get_item, ItemAction.get_item_})), States.giveaway_post)
async def get_post(callback: CallbackQuery, callback_data: GivePostCallback, state: fsm):
    post_id = callback_data.id
    user_id = callback.message.chat.id

    post_giveaway_title = await read("jettons_bot/databases/posts.db", "posts", "title", f"user_id={user_id}")
    if not post_giveaway_title:
        text = await get_text(f"{handler_name}/post_not_found")
        await callback.message.answer(text, reply_markup=add_post_button)
        await state.clear()
    else:
        channels = await read("jettons_bot/databases/channels.db", "channels", "channel_id, title", f"user_id={user_id}")
        if not channels:
            text = await get_text(f"{handler_name}/no_channels")
            await callback.message.answer(text, reply_markup=add_channel_button)
            await state.clear()
        else:
            await state.update_data(post_giveaway_title=post_giveaway_title[0][0], post_id=post_id)
            await state.set_state(States.giveaway_channel)

            keyboard = await get_items_keyboard(
                items = channels,
                page_size = 10, 
                page_index = 0, 
                item_callback_data = GiveChannelCallback, 
                items_list_callback_data = GiveChannelsListCallback)

            text = await get_text(f"{handler_name}/choose_channel")
            await callback.message.answer(text, reply_markup=keyboard)
            
            await callback.message.edit_text(
                text=f"Выбранный пост: {post_giveaway_title[0][0]}",
                reply_markup=None)

@router.callback_query(GivePostsListCallback.filter(F.action.in_({
    ItemsListAction.switch_page,})), States.giveaway_post)
async def get_posts_list(callback: CallbackQuery, callback_data: GivePostsListCallback, state: fsm):
    message = callback.message
    user_id = message.chat.id
    page_index = callback_data.page_index
        
    posts = await read("jettons_bot/databases/posts.db", "posts", "id, title", f"user_id={user_id}")
    if not posts:
        text = await get_text(f"{handler_name}/no_posts")
        await callback.answer(text, reply_markup=add_post_button)
        await state.clear()
    else:
        keyboard = await get_items_keyboard(
            items = posts,
            page_size = 10, 
            page_index = page_index, 
            item_callback_data = GivePostCallback, 
            items_list_callback_data=GivePostsListCallback)

        text = await get_text(f"{handler_name}/choose_post")
        await message.edit_text(text, reply_markup=keyboard)
    
    await swtich_button(callback)

@router.callback_query(GiveChannelCallback.filter(F.action.in_({ItemAction.get_item, ItemAction.get_item_})), States.giveaway_channel)
async def get_channel(callback: CallbackQuery, callback_data: GivePostCallback, state: fsm):
    channel_id = callback_data.id
    user_id = callback.message.chat.id

    channel_giveaway_title = await read("jettons_bot/databases/channels.db", "channels", "title", f"channel_id={channel_id} AND user_id={user_id}")
    if not channel_giveaway_title:
        text = await get_text(f"{handler_name}/post_not_found")
        await callback.message.answer(text, reply_markup=add_post_button)
        await state.clear()
    else:
        try:
            bot_chat = await bot.get_me()
            bot_member = await bot.get_chat_member(channel_id, bot_chat.id)
        except TelegramForbiddenError:
            text = await get_text(f"{handler_name}/kicked_or_deleted_channel")
            await callback.answer(text, show_alert=True)

            await delete("jettons_bot/databases/channels.db", "channels", f"channel_id={channel_id} AND user_id={user_id}")

            return

        if not bot_member.can_post_messages:
            text = await get_text(f"{handler_name}/not_provided_rights")
            await callback.answer(text)
            
            return

        await state.update_data(channel_id=channel_id, channel_giveaway_title=channel_giveaway_title[0][0])

        text = await get_text(f"{handler_name}/choose_date")
        buttons = await create_week_keyboard()

        await callback.message.answer(text, reply_markup=buttons)
        
        await callback.message.edit_text(
                text=f"Выбранный канал: {channel_giveaway_title[0][0]}",
                reply_markup=None)

        await state.set_state(States.date)

@router.callback_query(GiveChannelsListCallback.filter(F.action.in_({
    ItemsListAction.switch_page,})), States.giveaway_channel)
async def get_channels_list(callback: CallbackQuery, callback_data: GiveChannelsListCallback, state: fsm):
    message = callback.message
    user_id = message.chat.id
    page_index = callback_data.page_index
        
    channels = await read(db_path, f"{handler_name}", "id, title", f"user_id={user_id}")
    if not channels:
        text = await get_text(f"{handler_name}/no_channels")
        await callback.answer(text, reply_markup=add_channel_button)
        await state.clear()
    else:
        keyboard = await get_items_keyboard(
            items = channels,
            page_size = 10, 
            page_index = page_index, 
            item_callback_data = GiveChannelCallback, 
            items_list_callback_data=GiveChannelsListCallback)

        text = await get_text(f"{handler_name}/choose_channels")
        await message.edit_text(text, reply_markup=keyboard)
    
    await swtich_button(callback)

@router.callback_query(GiveDateCallback.filter(), States.date)
async def get_channels_list(callback: CallbackQuery, callback_data: GiveDateCallback, state: fsm):
    day = callback_data.day
    month = callback_data.month
    year = callback_data.year

    await state.update_data(date=f"{day}/{month}/{year}")
    await state.set_state(States.time)

    text = await get_text(f"{handler_name}/enter_time")
    await callback.message.answer(text)

    date = f"{day} {genitive_month_name(month)}"
    await callback.message.edit_text(f"Выбранная дата: {date}", reply_markup=None)

@router.message(F.text.regexp("^([01]?[0-9]|2[0-3]):[0-5][0-9]$"), States.time)
async def time(message: Message, state: fsm):
    data = await state.get_data()

    date = data["date"].split('/')
    time = message.text.split(':')

    dtime = dt.datetime(*date, hour=int(time[0]), minute=int(time[1]))
    if (dtime <= datetime.now()):
        text = await get_text(f"{handler_name}/past_time")
        await message.answer(text)

        return
    elif (dtime - datetime.now()).seconds <= 60:
        text = await get_text(f"{handler_name}/past_time")
        await message.answer(text)

        return
                             
    await state.update_data(time=message.text)
    await state.set_state(States.delete_after)

    text = await get_text(f"{handler_name}/enter_when_delete")
    buttons = await when_delete_buttons()
    
    await message.answer(text, reply_markup=buttons)

@router.message(States.time)
async def incorrect_time(message: Message):
    text = await get_text(f"{handler_name}/incorrect_time")
    await message.answer(text)

@router.callback_query(GiveDeleteTimeCallback.filter(), States.delete_after)
async def delete_time(callback: CallbackQuery, callback_data: GiveDeleteTimeCallback, state: fsm):
    hours = callback_data.hours

    await state.update_data(delete_hours=hours)
    await state.set_state(States.sub_hours)

    text = await get_text(f"{handler_name}/enter_subscribe_check")
    buttons = await sub_check_buttons()
    await callback.message.answer(text, reply_markup=buttons)

    await callback.message.edit_text(f"Выбранное время удаления: через {hours} ч.")

@router.callback_query(GiveSubCheckHours.filter(), States.sub_hours)
@router.callback_query(GiveSubCheckHours.filter(), States.change_sub_hours)
async def sub_hours(callback: CallbackQuery, callback_data: GiveSubCheckHours, state: fsm):
    sub_hours = callback_data.hours
    
    await state.update_data(sub_hours=sub_hours)
    
    cur_state = await state.get_state()
    if cur_state == States.sub_hours:
        await state.set_state(States.jetton_address)

        text = await get_text(f"{handler_name}/enter_jetton_address")
        await callback.message.answer(text, reply_markup=ReplyKeyboardRemove())
    else:
        await state.set_state(States.confirm_giveaway)
        data = await state.get_data()
        text = await get_giveaway_data(data)
        await callback.message.answer(text, reply_markup=confirm_give_buttons, parse_mode="HTML")

    if not sub_hours:
        sub_time = "нет"
    else:
        sub_td = dt.timedelta(hours=sub_hours)
        if sub_td.days >= 30:
            sub_time = f"{int(sub_td.days/30)} мес."
        elif sub_td.days >= 7:
            sub_time = f"{int(sub_td.days/7)} нед."
        else:
            sub_time = f"{sub_td.days} д."
        
    await callback.message.edit_text(f"Выбранное время подписки: {sub_time}", reply_markup=None)

@router.message(F.text, States.sub_hours)
async def incorrect_sub_hours(message: Message, state: fsm):
    text = await get_text(f"{handler_name}/incorrect_sub_time")
    await message.answer(text)

@router.message(F.text, States.jetton_address)
async def jetton_address(message: Message, state: fsm):
    if message.text.lower() == "назад":
        text = await get_text(f"{handler_name}/enter_giveaway_title")
        await message.answer(text, reply_markup=cancel_button)
        await state.set_state(States.giveaway_title)
        
        return

    address = message.text
    with open("jettons_bot/ls_cfg.json") as cfg:
        cfg = load(cfg)
  
    client = LiteClient.from_config(
        config=cfg,
        trust_level=9999999,
        timeout=99
    )

    client = LiteBalancer.from_mainnet_config(trust_level=2)

    await client.connect()

    try:
        jetton_data = await client.run_get_method(
            address=address, 
            method='get_jetton_data', 
            stack = [])
    except AddressError:
        text = await get_text(f"{handler_name}/unknown_jetton_address")
        await message.answer(text)

        await client.close()
        
        return

    await client.close()

    await state.update_data(jetton_address=address)

    # text = await get_text(f"{handler_name}/enter_transaction_type")
    # await message.answer(text, reply_markup=transaction_types)

    text = await get_text(f"{handler_name}/enter_count_onchain")
    await state.set_state(States.onchain_count)

# @router.message(F.text.lower().in_({"ончейн", "рокет", "оба", "назад"}), States.transaction_type)
# @router.message(F.text.lower().in_({"ончейн", "рокет", "оба", "назад"}), States.change_tr_type)
# async def transaction_type(message: Message, state: fsm):
#     if message.text.lower() == "назад":
#         cur_state = await state.get_state()
#         if cur_state == States.transaction_type:
#             await giveaway_title(message, state)
            
#             return
#         else:
#             await state.set_state(States.confirm_giveaway)
#             data = await state.get_data()
#             text = await get_giveaway_data(data)
#             await message.answer(text, reply_markup=confirm_give_buttons, parse_mode="HTML")
    
#     if message.text.lower() == "оба":
#         text = await get_text(f"{handler_name}/enter_count_onchain")
#         await state.set_state(States.both_onchain)
#     elif message.text.lower() == "ончейн":
#         text = await get_text(f"{handler_name}/enter_count_onchain")
#         await state.set_state(States.onchain_count)
#     elif message.text.lower() == "рокет":
#         text = await get_text(f"{handler_name}/enter_count_rocket")
#         await state.set_state(States.rocket_count)

#     await message.answer(text)

# @router.message(F.text.regexp(f"^{float_reg_exp}$"), States.both_onchain)
# async def both_onchain(message: Message, state: fsm):
    # if message.text.lower() == "назад":
    #     await jetton_address(message, state)

    #     return

    # text = message.text.replace(',','.')
    # await state.update_data(onchain_count=text)

    # await state.set_state(States.both_rocket)  

    # text = await get_text(f"{handler_name}/enter_count_rocket")
    # await message.answer(text)

@router.message(F.text.regexp(f"^{float_reg_exp}$"), States.onchain_count)
# @router.message(F.text.regexp(f"^{float_reg_exp}$"), States.rocket_count)
# @router.message(F.text.regexp(f"^{float_reg_exp}$"), States.both_rocket)
async def channels_actions(message: Message, state: fsm):
    cur_state = await state.get_state()

    if message.text.lower() == "назад":
        if cur_state == States.both_rocket:
            await state.set_state(States.both_onchain)

            text = await get_text(f"{handler_name}/enter_count_onchain")
            await message.answer(text, reply_markup=ReplyKeyboardRemove())
        else:
            await state.set_state(States.jetton_address)

            text = await get_text(f"{handler_name}/enter_jetton_address")
            await message.answer(text, reply_markup=ReplyKeyboardRemove())
        
        return
    
    await state.set_state(States.gives_count)
    text = message.text.replace(',','.')

    if cur_state == States.onchain_count:
        await state.update_data(onchain_count=text)
    else:
        await state.update_data(rocket_count=text)
    
    text = await get_text(f"{handler_name}/enter_gives_count")
    await message.answer(text)

@router.message(F.text.regexp(f"^[^0]\d*$"), States.gives_count)
async def channels_actions(message: Message, state: fsm):
    await state.set_state(States.confirm_giveaway)

    await state.update_data(gives_count=message.text)
    data = await state.get_data()
    text = await get_giveaway_data(data)
    
    buttons = confirm_give_buttons
    await message.answer(text, reply_markup=buttons, parse_mode="HTML")

@router.message(States.gives_count)
async def jetton_address(message: Message, state: fsm):
    text = await get_text(f"{handler_name}/incorrect_gives_count")
    await message.answer(text)

@router.message(F.text.lower() == "подтвердить", States.confirm_giveaway)
async def confirm_giveaway(message: Message, state: fsm):
    wallet_address = getenv("WALLET_ADDRESS")
    fee = float(getenv("FEE"))
    ton_fee = float(getenv("TON_FEE"))

    data = await state.get_data()

    date = data["date"].split('/')
    date += data["time"].split(':')
    
    dtime = dt.datetime(*date)

    data_to_db = {}
    data_to_db["user_id"] = message.chat.id
    data_to_db["title"] = data.get("giveaway_title")
    data_to_db["post_title"] = data.get("post_giveaway_title")
    data_to_db["post_id"] = data.get("post_id")
    data_to_db["channel_title"] = data.get("channel_giveaway_title")
    data_to_db["channel_id"] = data.get("channel_id")
    data_to_db["jetton_address"] = data.get("jetton_address")
    data_to_db["timestamp"] = int(dtime.strftime('%s'))
    data_to_db["delete_hours"] = int(data.get("delete_hours"))
    data_to_db["sub_hours"] = data.get("sub_hours")
    data_to_db["onchain_count"] = float(data.get("onchain_count"))
    data_to_db["rocket_count"] = float(data.get("rocket_count"))
    data_to_db["gives_count"] = int(data.get("gives_count"))
    data_to_db["cur_gives_count"] = int(data.get("gives_count"))
    data_to_db["status"] = data.get("need_payment")
    data_to_db["jettons_fee"] = fee
    
    jettons_amount = data_to_db["onchain_count"]*data_to_db["gives_count"]*(1+fee/100)
    ton_fee_amount = data_to_db["gives_count"]*ton_fee

    data_to_db["jettons_total_amount"] = jettons_amount
    data_to_db["ton_fee_amount"] = ton_fee_amount

    row_id = await create(
        db_path,
        table=handler_name, 
        columns=data_to_db,
        get_last_row=True)
    
    jettons_address = data_to_db["jetton_address"]

    jettons_payment_link = f"ton://transfer/{wallet_address}?\
        jetton={jettons_address}&\
        amount={jettons_amount}&\
        text=giveaway_id:{row_id}:jettons"

    ton_payment_link = f"ton://transfer/{wallet_address}?\
        amount={ton_fee_amount}&\
        text=giveaway_id:{row_id}:ton"

    buttons = await paymend_buttons(
        jettons_url=jettons_payment_link,
        ton_url=ton_payment_link)

    text = await get_text(f"{handler_name}/giveaway_confirmed")
    await message.answer(text, reply_markup=buttons)


@router.message(F.text.lower() == "изменить раздачу", States.confirm_giveaway)
async def change(message: Message, state: fsm):
    text = await get_text(f"{handler_name}/choose_what_change")
    buttons = await change_give_buttons()
    await message.answer(text, reply_markup=buttons)

    await state.set_state(States.change_giveaway)

@router.message(F.text.lower() == "назад", States.change_giveaway)
async def cancel_changing(message: Message, state: fsm):
    data = await state.get_data()
    text = await get_giveaway_data(data)
    
    buttons = confirm_give_buttons
    await message.answer(text, reply_markup=buttons, parse_mode="HTML")

@router.message(F.text.lower() == "название", States.change_giveaway)
async def change_giveaway_title(message: Message, state: fsm):
    await state.set_state(States.change_giveaway_title)
    
    text = await get_text(f"{handler_name}/enter_giveaway_title")
    await message.answer(text, reply_markup=cancel_button)

@router.message(F.text, States.change_giveaway_title)
async def changing_giveaway_title(message: Message, state: fsm):
    if message.text.lower() == "назад":
        await state.clear()
        await gives_options(message, state)
        
        mes = await message.answer("⁠⁠", reply_markup=ReplyKeyboardRemove())
        await mes.delete()

        return

    if len(message.text) > 50:
        text = await get_text(f"{handler_name}/giveaway_title_too_long")
        await message.answer(text)
        
        return

    await state.set_state(States.confirm_giveaway)
    await state.update_data(giveaway_title=message.text)

    data = await state.get_data()
    text = await get_giveaway_data(data)
    
    buttons = confirm_give_buttons
    await message.answer(text, reply_markup=buttons, parse_mode="HTML")

@router.message(F.text.lower() == "адрес жетона", States.change_giveaway)
async def change_jetton_address(message: Message, state: fsm):
    await state.set_state(States.change_jetton_address)
    
    text = await get_text(f"{handler_name}/enter_jetton_address")
    await message.answer(text, reply_markup=cancel_button)

@router.message(F.text, States.change_jetton_address)
async def changing_jetton_address(message: Message, state: fsm):
    if message.text.lower() == "назад":
        await state.clear()
        await gives_options(message, state)
        
        mes = await message.answer("⁠⁠", reply_markup=ReplyKeyboardRemove())
        await mes.delete()

        return

    address = message.text
    with open("jettons_bot/ls_cfg.json") as cfg:
        cfg = load(cfg)
  
    client = LiteClient.from_config(
        config=cfg,
        trust_level=9999999,
        timeout=99
    )
    
    await client.connect()

    try:
        jetton_data = await client.run_get_method(
            address=address, 
            method='get_jetton_data', 
            stack = [])
    except AddressError:
        text = await get_text(f"{handler_name}/unknown_jetton_address")
        await message.answer(text)

        await client.close()
        
        return
    
    await client.close()

    await state.set_state(States.transaction_type)
    await state.update_data(jetton_addres=message.text)

    data = await state.get_data()
    text = await get_giveaway_data(data)
    
    buttons = confirm_give_buttons
    await message.answer(text, reply_markup=buttons, parse_mode="HTML")

@router.message(F.text.lower() == "пост", States.change_giveaway)
async def change_post(message: Message, state: fsm):
    await state.set_state(States.change_giveaway_post)

    user_id = message.chat.id

    text = await get_text(f"{handler_name}/choose_post")
    await message.answer(text, reply_markup=cancel_button)

    posts = await read("jettons_bot/databases/posts.db", "posts", "id, giveaway_title", f"user_id={user_id}")
    if not posts:
        text = await get_text(f"{handler_name}/no_posts")
        await message.answer(text, reply_markup=add_post_button)
        await state.clear()
    else:
        keyboard = await get_items_keyboard(
            items = posts,
            page_size = 10, 
            page_index = 0, 
            item_callback_data = GivePostCallback, 
            items_list_callback_data = GivePostsListCallback)

        text = await get_text(f"{handler_name}/choose_post")
        await message.answer(text, reply_markup=keyboard)
        
        msg = await message("", reply_markup=cancel_button)
        await msg.delete()

@router.callback_query(
    GivePostCallback.filter(
        F.action.in_({
            ItemAction.get_item, 
            ItemAction.get_item_})), 
        States.change_giveaway_post)
async def changing_post(callback: CallbackQuery, callback_data: GivePostCallback, state: fsm):
    post_id = callback_data.id
    user_id = callback.message.chat.id

    post_giveaway_title = await read("jettons_bot/databases/posts.db", "posts", "giveaway_title", f"user_id={user_id}")
    if not post_giveaway_title:
        text = await get_text(f"{handler_name}/post_not_found")
        await callback.message.answer(text, reply_markup=add_post_button)
        await state.clear()
    else:
        await state.update_data(post_giveaway_title=post_giveaway_title[0][0], post_id=post_id)
        await state.set_state(States.confirm_giveaway)

        data = await state.get_data()
        text = await get_giveaway_data(data)
        await callback.message.answer(text, reply_markup=confirm_give_buttons, parse_mode="HTML")

@router.message(F.text.lower() == "канал", States.change_giveaway)
async def change_channel(message: Message, state: fsm):
    user_id = message.chat.id
    channels = await read("jettons_bot/databases/channels.db", "channels", "channel_id, giveaway_title", f"user_id={user_id}")
    if not channels:
        text = await get_text(f"{handler_name}/no_channels")
        await message.answer(text, reply_markup=add_channel_button)
        await state.clear()
    else:
        await state.set_state(States.change_giveaway_channel)

        keyboard = await get_items_keyboard(
            items = channels,
            page_size = 10, 
            page_index = 0, 
            item_callback_data = GiveChannelCallback, 
            items_list_callback_data = GiveChannelsListCallback)

        text = await get_text(f"{handler_name}/choose_channel")
        await message.answer(text, reply_markup=keyboard)

@router.callback_query(
    GiveChannelCallback.filter(
        F.action.in_({
            ItemAction.get_item, 
            ItemAction.get_item_})), 
        States.change_giveaway_channel)
async def changing_channel(callback: CallbackQuery, callback_data: GiveChannelCallback, state: fsm):
    channel_id = callback_data.id
    user_id = callback.message.chat.id

    channel_giveaway_title = await read("jettons_bot/databases/channels.db", "channels", "giveaway_title", f"channel_id={channel_id} AND user_id={user_id}")
    if not channel_giveaway_title:
        text = await get_text(f"{handler_name}/post_not_found")
        await callback.message.answer(text, reply_markup=add_post_button)
        await state.clear()
    else:
        try:
            bot_chat = await bot.get_me()
            bot_member = await bot.get_chat_member(channel_id, bot_chat.id)
        except TelegramForbiddenError:
            text = await get_text(f"{handler_name}/kicked_or_deleted_channel")
            await callback.answer(text, show_alert=True)

            await delete("jettons_bot/databases/channels.db", "channels", f"channel_id={channel_id} AND user_id={user_id}")

            return

        if not bot_member.can_post_messages:
            text = await get_text(f"{handler_name}/not_provided_rights")
            await callback.answer(text)
            
            return

        await state.update_data(channel_id=channel_id, channel_giveaway_title=channel_giveaway_title[0][0])
        await state.set_state(States.confirm_giveaway)

        data = await state.get_data()
        text = await get_giveaway_data(data)
        await callback.message.answer(text, reply_markup=confirm_give_buttons, parse_mode="HTML")

@router.message(F.text.lower() == "дата", States.change_giveaway)
async def change_date(message: Message, state: fsm):
    text = await get_text(f"{handler_name}/choose_date")
    buttons = await create_week_keyboard()
    
    await message.answer(text, reply_markup=buttons)

    await state.set_state(States.change_date)

@router.message(GiveDateCallback.filter(), States.change_date)
async def changing_date(callback: CallbackQuery, callback_data: GiveDateCallback, state: fsm):
    day = callback_data.day
    month = callback_data.month
    year = callback_data.year

    await state.update_data(date=f"{day}/{month}/{year}")
    data = await state.get_data()
    text = await get_giveaway_data(data)
    await state.set_state(States.confirm_giveaway)
    await callback.message.answer(text, reply_markup=confirm_give_buttons, parse_mode="HTML")

    date = f"{day} {genitive_month_name(month)}"
    await callback.message.edit_text(f"Выбранная дата: {date}", reply_markup=None)

@router.message(F.text.lower() == "время", States.change_giveaway)
async def change_time(message: Message, state: fsm):
    await state.set_state(States.change_time)

    text = await get_text(f"{handler_name}/enter_time")
    await message.answer(text)

@router.message(F.text.regexp("^([01]?[0-9]|2[0-3]):[0-5][0-9]$'"), States.change_time)
async def changing_time(message: Message, state: fsm):
    await state.update_data(time=message.text)

    data = await state.get_data()
    text = await get_giveaway_data(data)
    await state.set_state(States.confirm_giveaway)
    await message.answer(text, reply_markup=confirm_give_buttons, parse_mode="HTML")

@router.message(States.change_time)
async def incorrect_time(message: Message):
    text = await get_text(f"{handler_name}/incorrect_time")
    await message.answer(text)

@router.message(F.text.lower() == "время удаления", States.change_giveaway)
async def change_delete_time(message: Message, state: fsm):
    await state.set_state(States.change_delete_after)

    text = await get_text(f"{handler_name}/enter_when_delete")
    buttons = when_delete_buttons()
    
    await message.answer(text, reply_markup=buttons)

@router.message(F.text.regexp("^\d+ ч.$"), States.change_delete_after)
async def changing_delete_time(message: Message, state: fsm):
    await state.update_data(delete_hours=message.text.split()[1])
    
    data = await state.get_data()
    text = await get_giveaway_data(data)
    await state.set_state(States.confirm_giveaway)
    await message.answer(text, reply_markup=confirm_give_buttons, parse_mode="HTML")

@router.message(F.text.lower() == "проверка подписки", States.change_giveaway)
async def change_delete_time(message: Message, state: fsm):
    await state.set_state(States.change_sub_hours)

    text = await get_text(f"{handler_name}/enter_subscribe_check")
    buttons = await sub_check_buttons()
    await message.answer(text, reply_markup=buttons)

@router.message(F.text.lower() == "количество токенов на руки", States.change_giveaway)
async def change_tr_type(message: Message, state: fsm):
    await state.set_state(States.change_jettons_count)

    text = await get_text(f"{handler_name}/enter_count_onchain")
    await message.answer(text, reply_markup=ReplyKeyboardRemove)

@router.message(F.text.regexp(f"^{float_reg_exp}$"), States.change_jettons_count)
async def change_jettons_count(message: Message, state: fsm):
    text = message.text.replace(',','.')
    await state.update_data(onchain_count=text)
    
    data = await state.get_data()
    text = await get_giveaway_data(data)
    await state.set_state(States.confirm_giveaway)
    await message.answer(text, reply_markup=confirm_give_buttons, parse_mode="HTML")

@router.message(GiveawayCallback.filter(F.action.in_({
    ItemAction.resend_post,
    ItemAction.resend_post_})))
async def resend_post(callback: CallbackQuery, callback_data: GiveawayCallback):
    await start_giveaway(callback_data.id)

    await swtich_button(callback)

@router.message(F.text.lower() == "количество раздач", States.change_giveaway)
async def change_gives_count(message: Message, state: fsm):
    await state.set_state(States.change_gives_count)

    text = await get_text(f"{handler_name}/enter_gives_count")
    await message.answer(text)

@router.message(F.text.regexp(f"^[^0]\d*$"), States.change_gives_count)
async def changing_gives_count(message: Message, state: fsm):
    await state.set_state(States.confirm_giveaway)

    await state.update_data(gives_count=message.text)
    data = await state.get_data()
    text = await get_giveaway_data(data)
    
    buttons = confirm_give_buttons
    await message.answer(text, reply_markup=buttons, parse_mode="HTML")


@router.callback_query(CommandStart(deep_link=True))
async def get_address(message: Message, command: CommandObject):
    args = command.args
    give_id = decode_payload(args)

    status = await check_user_status(message, give_id)
    if not status:
        return

    wallet_type_buttons = await get_wallet_type_buttons(give_id, GetJettonsCallback)

    text = await get_text(f"{handler_name}/choose_wallet_type")
    message.answer(text, reply_markup=wallet_type_buttons)


@router.callback_query(GetJettonsCallback.filter())
async def get_jettons(callback: CallbackQuery, callback_data: GetJettonsCallback):
    await swtich_button(callback)

    message = callback.message

    give_id = callback_data.id

    if give_id == -1:
        text = await get_text(f"{handler_name}/this_is_template")
        callback.answer(text)

        return

    wallet_typе = callback_data.wallet_type

    status = await check_user_status(message, give_id)
    if not status:
        return

    payload = f"{callback.id}_{uuid4()}"

    connector, url = await TonConnect(f'https://killmore.xyz/lifeyt/ton-connect.json', wallet_typе, payload)

    qr_code_path = f'jettons_bot/qr_codes/{callback.id}.png'
    await generate_qr_code(url, qr_code_path)

    url_button = await get_url_button(link=url, text=f"Открыть {wallet_typе.capitalize()}")
    await callback.message.reply_photo(
        qr_code_path,
        caption=open("tokens_url_message.txt",'r', encoding='utf-8').read(),
        reply_markup=url_button)

    try:
        remove(qr_code_path)
    except Exception:
        pass

    try:
        address = await connector.get_address()
    except Exception:
        await callback.message.reply_text("Ошибка подключения, попробуйте позже")

        return
    
    await create(
        db_path="jettons_bot/databases/claims_queue.db",
        table="claims_queue",
        columns={
            "user_id":message.chat.id,
            "give_id":give_id,
            "status":"user_claim",
            "wallet_address": address
        }
    )

    text = await get_text(f"{handler_name}/in_pending")
    message.answer(text)

@router.callback_query(GiveawaysListCallback.filter(F.action.in_({
    ItemsListAction.switch_page, 
    ItemsListAction.get_list,
    ItemsListAction.get_list_})))
async def get_giveaways_list(callback: CallbackQuery, callback_data: GiveawaysListCallback, state: fsm):
    message = callback.message
    user_id = message.chat.id

    if callback_data.action in [ItemsListAction.get_list, ItemsListAction.get_list_]:
        await state.clear()

    page_index = callback_data.page_index

    giveaways = await read(db_path, f"{handler_name}", "id, title", f"user_id={user_id}")
    if not giveaways:
        text = await get_text(f"{handler_name}/no_giveaways")
        if callback_data.action in [ItemsListAction.get_list, ItemsListAction.get_list_]:
            await callback.answer(text, show_alert=True)
            await swtich_button(callback)
        else:
            button = await add_give_button()
            await message.edit_text(text, reply_markup=button)
    else:
        keyboard = await get_items_keyboard(
            items = giveaways,
            page_size = 10, 
            page_index = page_index, 
            item_callback_data = GiveawayCallback, 
            items_list_callback_data=GiveawaysListCallback)

        text = await get_text(f"{handler_name}/choose_giveaway")
        
        if callback_data.action in [ItemsListAction.get_list, ItemsListAction.get_list_]:
            await message.answer(text, reply_markup=keyboard)
            await swtich_button(callback)
        else:
            await message.edit_text(text, reply_markup=keyboard)

@router.callback_query(GiveawayCallback.filter(F.action.in_({ItemAction.get_item, ItemAction.get_item_})))
async def get_giveaway(callback: CallbackQuery, callback_data: GiveawayCallback, state: fsm):
    user_id = callback.message.chat.id
    giveaway_id = callback_data.id

    data = await read(db_path, f"{handler_name}", "*", f"id={giveaway_id} AND user_id={user_id}", in_dict=True)
    if not data:
        text = await get_text(f"{handler_name}/giveaway_not_found")
        await callback.answer(text, show_alert=True)
        
        return
    
    date = dt.datetime.strptime(data.get("timestamp"), "%s")
    month = genitive_month_name(date.month)
    date_str = date.strftime(f"%{time_sep}d {month}")
    time = date.strftime(f"%{time_sep}M:%H")

    if not data.get("sub_hours"):
        sub_time = "нет"
    else:
        sub_hours = int(data.get("sub_hours"))
        sub_td = dt.timedelta(hours=sub_hours)
        if sub_td.days >= 30:
            sub_time = f"{int(sub_td.days/30)} мес."
        elif sub_td.days >= 7:
            sub_time = f"{int(sub_td.days/7)} нед."
        else:
            sub_time = f"{sub_td.days} д."
    
    if data.get("onchain_count"):
        onchain_count = data.get("onchain_count")
    else:
        onchain_count = 0
    
    if data.get("rocket_count"):
        rocket_count = data.get("rocket_count")
    else:
        rocket_count = 0 

    buttons = await stop_giveaway_button(give_id=giveaway_id)

    if data["status"] == "active":
        status = "раздается"
    elif data["status"] == "scheduled":
        status = "запланировано"
    elif data["status"] == "completed":
        status = "завершено"
        buttons = None
    elif data["status"] == "need_paiment":
        status = "ожидает пополнения кошелька"
        
        wallet_address = getenv("WALLET_ADDRESS")
        
        jettons_payment_link = None
        ton_payment_link = None

        if data["paid_jettons_amount"] < data["jettons_total_amount"]:
            jettons_payment_link = f"ton://transfer/{wallet_address}?\
                jetton={data["jettons_address"]}&\
                amount={data["jettons_total_amount"]}&\
                text=giveaway_id:{data["id"]}:jetton"
        
        if data["paid_ton_amount"] < data["ton_fee_amount"]:
            ton_payment_link = f"ton://transfer/{wallet_address}?\
                amount={data["ton_fee_amount"]}&\
                text=giveaway_id:{data["id"]}:ton"

        buttons = await paymend_buttons(jettons_payment_link, ton_payment_link)

    text_list = [
        f'{data.get("title")}',
        f'Пост: {data.get("post_title")}',
        f'Канал {data.get("channel_title")}',
        f'Дата: {date_str}',
        f'Время: {time}',
        f'Удалить через: {data.get("delete_hours")} ч.',
        f'Проверка подписки: {sub_time}',
        f'Жетон: {data.get("jetton_address")}',
        f'Количество жетонов в руки: {onchain_count}',
        f'Макс. количество получателей: {data.get("gives_count")}',
        f'Статус: {status}']

    for line in text_list:
        line = Txt(line)

    text_list[0] = f"<b>{text_list[0]}</b>"

    text = '\n\n'.join(text_list)

    await callback.message.answer(text, reply_markup=buttons, parse_mode="HTML" )

@router.callback_query(GiveawayCallback.filter(F.action == "stop"))
async def stop_giveaway(callback: CallbackQuery, callback_data: GiveawayCallback):
    status = await read(
        db_path=db_path,
        table=handler_name,
        columns="status",
        conditions=f"id={callback_data.id}"
    )

    await swtich_button(callback)

    if status:
        if status[0] != "active":
            text = await get_text(f"{handler_name}/not_valid_giveaway")
            await callback.answer(text)

            return
    else:
        text = await get_text(f"{handler_name}/not_valid_giveaway")
        await callback.answer(text)

        return

    text = await get_text(f"{handler_name}/confirm_stop_giveaway")
    await callback.answer(text)

    buttons = await confirm_stopping_button(callback_data.id)
    callback.message.edit_reply_markup(reply_markup=buttons)

@router.callback_query(GiveawayCallback.filter(F.action == "yes_stop"))
async def confirm_stop(callback: CallbackQuery, callback_data: GiveawayCallback):
    status = await read(
        db_path=db_path,
        table=handler_name,
        columns="status",
        conditions=f"id={callback_data.id}"
    )

    await swtich_button(callback)

    if status:
        if status[0] != "active":
            text = await get_text(f"{handler_name}/not_valid_giveaway")
            await callback.answer(text)

            return
    else:
        text = await get_text(f"{handler_name}/not_valid_giveaway")
        await callback.answer(text)

        return

    await update(
        db_path=db_path,
        table = handler_name,
        columns={
            "status":"completed"
        },
        conditions=f"id={callback_data.id}"
    )
    
    await create(
        db_path="jettons_bot/databases/claims_queue.db",
        table="claims_queue",
        columns={
            "user_id":callback.message.chat.id,
            "give_id":callback_data.id,
            "status":"stop_giveaway",
            "wallet_address": ""
        }
    )

    await get_text(f"{handler_name}/giveaway_stopped")
    await callback.answer(text)

    await callback.message.edit_reply_markup(reply_markup=None)

@router.callback_query(GiveawayCallback.filter(F.action == "no_stop"))
async def no_stop_giveaway(callback: CallbackQuery, callback_data: GiveawayCallback):
    button = await stop_giveaway(callback_data.id)
    await callback.message.edit_reply_markup(reply_markup=button)
