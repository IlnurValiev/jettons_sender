from os import getenv, remove
from dotenv import load_dotenv
from uuid import uuid4
from sys import argv

from aiogram import Router, F
from aiogram import Bot
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext as fsm
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramForbiddenError

from jettons_bot.crud import *
from jettons_bot.buttons_factory import *
from jettons_bot.callbacks import (
    ChannelCallback, 
    ChannelsListCallback)

load_dotenv()

class States(StatesGroup):
    forward_post = State()

router = Router()

bot = Bot(token=getenv("TEST_BOT_TOKEN"))

handler_name = "channels"
db_path = f"jettons_bot/databases/{handler_name}.db"

@router.message(Command(handler_name))
async def channels_actions(message: Message, state: fsm):
    await state.clear()

    if message.chat.type == "private":
        text = await get_text(f"{handler_name}/channels_options")
        keyboard = await get_options_buttons(
            item_callback_data=ChannelCallback,
            items_list_callback_data=ChannelsListCallback,
            item_name="канал")
    else:
        text = await get_text(f"common/only_private")
        keyboard = None
    
    await message.answer(text, reply_markup=keyboard)

@router.callback_query(ChannelCallback.filter(F.action.in_({ItemAction.add_item, ItemAction.add_item_})))
async def add_channel(callback: CallbackQuery, state: fsm):
    await state.set_state(States.forward_post)
    
    text = await get_text(f"{handler_name}/make_admin_and_forward_post")
    await callback.message.answer(text)

    await swtich_button(callback)

@router.callback_query(ChannelsListCallback.filter(F.action.in_({
    ItemsListAction.switch_page, 
    ItemsListAction.get_list,
    ItemsListAction.get_list_})))
async def get_channels_list(callback: CallbackQuery, callback_data: ChannelsListCallback, state: fsm):
    message = callback.message
    user_id = message.chat.id

    if callback_data.action in [ItemsListAction.get_list, ItemsListAction.get_list_]:
        await state.clear()
    
    page_index = callback_data.page_index
        
    channels = await read(db_path, f"{handler_name}", "channel_id, title", f"user_id={user_id}")
    if not channels:
        text = await get_text(f"{handler_name}/no_channels")
        if callback_data.action in [ItemsListAction.get_list, ItemsListAction.get_list_]:
            await callback.answer(text, show_alert=True)
            await swtich_button(callback)
        else:
            await message.edit_text(text, reply_markup=add_channel_button)
    else:
        keyboard = await get_items_keyboard(
            items = channels,
            page_size = 10, 
            page_index = page_index, 
            item_callback_data = ChannelCallback, 
            items_list_callback_data=ChannelsListCallback)

        text = await get_text(f"{handler_name}/choose_channel")
        
        if callback_data.action in [ItemsListAction.get_list, ItemsListAction.get_list_]:
            await message.answer(text, reply_markup=keyboard)
            await swtich_button(callback)
        else:
            await message.edit_text(text, reply_markup=keyboard)

@router.callback_query(ChannelCallback.filter(F.action.in_({ItemAction.get_item, ItemAction.get_item_})))
async def get_channel(callback: CallbackQuery, callback_data: ChannelCallback, state: fsm):
    user_id = callback.message.chat.id
    channel_id = callback_data.id
    
    try:
        channel = await bot.get_chat(channel_id)
    except TelegramForbiddenError:
        text = await get_text(f"{handler_name}/kicked_or_deleted_channel")
        await callback.answer(text, show_alert=True)

        await delete(db_path, f"{handler_name}", f"channel_id={channel_id} AND user_id={user_id}")

        return

    data = await read(db_path, f"{handler_name}", "*", f"channel_id={channel_id} AND user_id={user_id}")
    if not data:
        text = await get_text(f"{handler_name}/channel_not_found")
        await callback.answer(text, show_alert=True)
        
        return

    title = channel.title
    desc = channel.description
    link = channel.invite_link
    photo = channel.photo

    button = await remove_item_button(
        item_id = channel_id,
        item_callback_data = ChannelCallback)

    text = f"<b>{title}</b>\n\n"
    if desc:
        text += f"<i>{desc}</i>\n\n"
    text += link
    
    if photo:
        photo = await bot.get_file(photo.big_file_id)
        photo_path = photo.file_path
        new_photo_path = f"jettons_bot/logos/{uuid4()}.jpg"

        await bot.download_file(photo_path, new_photo_path)
        await callback.message.answer_photo(
            photo = FSInputFile(new_photo_path),
            caption = text, 
            reply_markup = button,
            parse_mode = "HTML")
        
        remove(new_photo_path)
    else:
        await callback.message.answer(text, reply_markup=button, parse_mode="HTML")

    await state.clear()

    await swtich_button(callback)

@router.callback_query(ChannelCallback.filter(F.action == ItemAction.remove_item))
async def remove_channel(callback: CallbackQuery, callback_data: ChannelCallback):
    user_id = callback.message.chat.id
    channel_id = callback_data.id

    data = await read(db_path, f"{handler_name}", "*", f"channel_id={channel_id} AND user_id={user_id}")
    if not data:
        text = await get_text(f"{handler_name}/channel_not_found")
        await callback.answer(text, show_alert=True)
        
        return

    button = await confirm_remove_buttons(
        item_id = channel_id,
        item_callback_data = ChannelCallback
    )

    await callback.message.edit_reply_markup(reply_markup=button)

@router.callback_query(ChannelCallback.filter(F.action == ItemAction.cancel_removing))
async def cancel_removing_channel(callback: CallbackQuery, callback_data: ChannelCallback):
    buttons = await remove_item_button(
            item_id = callback_data.id,
            item_callback_data = ChannelCallback)
    
    await callback.message.edit_reply_markup(reply_markup=buttons)

@router.callback_query(ChannelCallback.filter(F.action == ItemAction.confirm_remove_item))
async def confim_delete_channel(callback: CallbackQuery, callback_data: ChannelCallback):
    user_id = callback.message.chat.id
    channel_id = callback_data.id

    data = await read(db_path, f"{handler_name}", "*", f"channel_id={channel_id} AND user_id={user_id}")
    if not data:
        text = await get_text(f"{handler_name}/channel_not_found")
        await callback.answer(text, show_alert=True)
        
        return
    
    await delete(db_path, f"{handler_name}", f"channel_id={channel_id} AND user_id={user_id}")

    text = await get_text(f"{handler_name}/channel_removed")
    await callback.answer(text)
    await callback.message.edit_reply_markup(reply_markup=None)

@router.message(lambda message: message.forward_date, States.forward_post)
async def add_forwarded_channel(message: Message, state: fsm):
    if not message.forward_from_chat:
        text = await get_text(f"{handler_name}/post_not_from_channel")
        await message.answer(text)
    elif message.forward_from_chat.type != "channel":
        text = await get_text(f"{handler_name}/post_not_from_channel")
        await message.answer(text)
    else:
        user_id = message.chat.id
        channel_id = message.forward_from_chat.id
        title =  message.forward_from_chat.title

        if not await read(db_path, f"{handler_name}", "*", f"channel_id={channel_id} AND user_id={user_id}"):
            bot_chat = await bot.get_me()
            try:
                bot_member = await bot.get_chat_member(channel_id, bot_chat.id)
            except TelegramForbiddenError:
                text = await get_text(f"{handler_name}/not_made_admin")
                await message.answer(text)

                return
            
            if bot_member.status != "administrator":
                text = await get_text(f"{handler_name}/not_made_admin")
                await message.answer(text)

                return

            user_member = await bot.get_chat_member(channel_id, user_id)
            if user_member.status != "creator":
                if user_member.status != "administrator":
                    text = await get_text(f"{handler_name}/user_not_admin")
                    await message.answer(text)

                    return
                elif not user_member.can_post_messages:
                    text = await get_text(f"{handler_name}/user_can_not_send_posts")
                    await message.answer(text)

                    return

            if not bot_member.can_post_messages:
                text = await get_text(f"{handler_name}/not_provided_rights")
                await message.answer(text)
                
                return

            await state.clear()

            data = {
                "user_id": user_id,
                "channel_id": channel_id,
                "title": title
            }

            await create(db_path, f"{handler_name}", data)

            text = await get_text(f"{handler_name}/channel_added")
            await message.answer(text)

        else:
            text = await get_text(f"{handler_name}/channel_already_added")
            await message.answer(text)