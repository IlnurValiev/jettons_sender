from os import getenv, remove
from dotenv import load_dotenv
from uuid import uuid4
from sys import argv

from aiogram import Router, F
from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext as fsm
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.formatting import Text
from aiogram.types.reply_keyboard_remove import ReplyKeyboardRemove

from jettons_bot.crud import *
from jettons_bot.buttons_factory import *
from jettons_bot.callbacks import PostCallback, PostsListCallback

from telegram_markdown_text import *

class States(StatesGroup):
    title = State()
    post = State()
    button_text = State()
    confirm = State()
    
    change = State()
    change_title = State()
    change_post = State()
    change_button_text = State()

    change_added = State()
    change_added_title = State()
    change_added_post = State()
    change_added_button_text = State()

router = Router()

bot = Bot(token=getenv("TEST_BOT_TOKEN"))

handler_name = "posts"
db_path = f"jettons_bot/databases/{handler_name}.db"
float_reg_exp = "\d+([\.,]?\d+)?"

async def send_post(
        message: Message,
        edit_buttons: bool,
        post_id: int,
        text: str, 
        button_text: str,
        media_id: str, 
        media_type: str,
        has_spoiler: bool):
    
    buttons = await post_buttons(button_text, post_id, PostCallback)

    if not edit_buttons:
        if media_type == "photo":
            await message.answer_photo(
                photo=media_id,
                caption=text, 
                parse_mode="MarkdownV2",
                has_spoiler=has_spoiler,
                reply_markup=buttons)
        elif media_type == "video":
            await message.answer_video(
                video=media_id,
                caption=text, 
                parse_mode="MarkdownV2",
                has_spoiler=has_spoiler,
                reply_markup=buttons)
        else:        
            await message.answer(text, parse_mode="MarkdownV2", reply_markup=buttons)
    else:
        await message.edit_reply_markup(reply_markup=buttons)

async def get_post_data(message: Message):
    if message.photo or message.video:
        if message.caption:
            if message.caption_entities:
                text_obj = Text.from_entities(message.caption, message.caption_entities)
                text_len = len(text_obj)
                text = text_obj.as_markdown()
            else:
                text = message.caption
                text_len = len(text)
        else:
            text = ""
            text_len = 0
        
        if message.photo:
            media_id = message.photo[0].file_id
            media_type = "photo"
        else:
            media_id = message.video.file_id
            media_type = "video"
    else:
        if message.entities:
            text_obj = Text.from_entities(message.text, message.entities)
            text_len = len(text_obj)
            text = text_obj.as_markdown()
        else:
            text = message.text
            text_len = len(text)
        
        media_id = ""
        media_type = ""

    return text, text_len, media_id, media_type

@router.message(Command(handler_name))
async def posts_options(message: Message, state: fsm):
    await state.clear()

    if message.chat.type == "private":
        text = await get_text(f"{handler_name}/posts_options")
        keyboard = await get_options_buttons(
            item_callback_data=PostCallback,
            items_list_callback_data=PostsListCallback,
            item_name="пост")
    else:
        text = await get_text(f"common/only_private")
        keyboard = ReplyKeyboardRemove()
    
    await message.answer(text, reply_markup=keyboard)

@router.callback_query(PostCallback.filter(F.action.in_({ItemAction.add_item, ItemAction.add_item_})))
async def add_post(callback: CallbackQuery, state: fsm):
    await state.set_state(States.title)
    
    text = await get_text(f"{handler_name}/enter_title")
    await callback.message.answer(text, reply_markup=cancel_button)

    await swtich_button(callback)

@router.message(F.text, States.title)
async def title(message: Message, state: fsm):
    if message.text.lower() == "назад":
        await state.clear()
        await posts_options(message, state)
        
        mes = await message.answer("⁠⁠", reply_markup=ReplyKeyboardRemove())
        await mes.delete()

        return

    if len(message.text) > 50:
        text = await get_text(f"{handler_name}/title_too_long")
        await message.answer(text)
        
        return

    await state.set_state(States.post)
    await state.update_data(title=message.text)

    text = await get_text(f"{handler_name}/send_post")
    await message.answer(text, reply_markup=cancel_button)

@router.message(~F.media_group_id & (F.photo | F.video | F.text), States.post)
async def post(message: Message, state: fsm):
    if message.text:
        if message.text.lower() == "назад":
            await state.set_state(States.title)
    
            text = await get_text(f"{handler_name}/enter_title")
            await message.answer(text, reply_markup=cancel_button)
            
            return

    text, text_len, media_id, media_type = await get_post_data(message)

    if (text_len > 1024) and media_type:
        text = await get_text(f"{handler_name}/caption_too_long")
        await message.answer(text)
        
        return
    
    if message.has_media_spoiler:
        has_spoiler = 1
    else:
        has_spoiler = 0
    
    await state.update_data(
        text=text, 
        media_id=media_id, 
        media_type=media_type, 
        has_spoiler=has_spoiler)
    
    await state.set_state(States.button_text)

    text = await get_text(f"{handler_name}/enter_button_text")
    await message.answer(text, reply_markup=cancel_button)

@router.message(States.post)
async def post(message: Message):
    text = await get_text(f"{handler_name}/no_valid_post")
    await message.answer(text)

@router.message(F.text, States.button_text)
async def button_text(message: Message, state: fsm):
    if message.text.lower() == "назад":
        await state.set_state(States.post)

        text = await get_text(f"{handler_name}/send_post")
        await message.answer(text)
        
        return

    if len(message.text) > 50:
        text = await get_text(f"{handler_name}/button_text_too_long")
        await message.answer(text)

        return
    
    await state.set_state(States.confirm)
    await state.update_data(button_text=message.text)

    text = await get_text(f"{handler_name}/confirm_post")
    await message.answer(text, reply_markup=confirm_post_button)

@router.message(F.text.lower() == "подтвердить", States.confirm)
async def channels_actions(message: Message, state: fsm):
    data = await state.get_data()

    data_to_db = {}
    data_to_db["user_id"] = message.chat.id
    data_to_db["title"] = data.get("title")
    data_to_db["button_text"] = data.get("button_text")
    data_to_db["text"] = data.get("text")
    data_to_db["media_id"] = data.get("media_id")
    data_to_db["media_type"] = data.get("media_type")
    data_to_db["has_spoiler"] = data.get("has_spoiler")

    await create(db_path, table="posts", columns=data_to_db)
    await state.clear() 

    text = await get_text(f"{handler_name}/post_confirmed")
    await message.answer(text, reply_markup=ReplyKeyboardRemove())

@router.message(F.text.lower() == "изменить", States.confirm)
async def channels_actions(message: Message, state: fsm):
    await state.set_state(States.change) 
     
    data = await state.get_state()

    text = await get_text(f"{handler_name}/choose_what_change")
    button = await change_post_buttons(data)
    await message.answer(text, reply_markup=button)

@router.message(F.text.lower() == "название", States.change)
async def channels_actions(message: Message, state: fsm):
    await state.set_state(States.change_title)
    
    text = await get_text(f"{handler_name}/enter_title")
    await message.answer(text, reply_markup=cancel_button)

@router.message(F.text.lower() == "назад", States.change)
async def channels_actions(message: Message, state: fsm):
    await state.set_state(States.confirm)

    text = await get_text(f"{handler_name}/confirm_post")
    await message.answer(text, reply_markup=confirm_post_button)

@router.message(F.text, States.change_title)
async def channels_actions(message: Message, state: fsm):
    if len(message.text) > 50:
        text = await get_text(f"{handler_name}/title_too_long")
        await message.answer(text)
        
        return

    await state.set_state(States.confirm)
    await state.update_data(title=message.text)
    
    text = await get_text(f"{handler_name}/confirm_post")
    await message.answer(text, reply_markup=confirm_post_button)

@router.message(F.text.lower() == "пост", States.change)
async def channels_actions(message: Message, state: fsm):
    await state.set_state(States.change_post)
    
    text = await get_text(f"{handler_name}/send_post")
    await message.answer(text)

@router.message(~F.media_group_id & (F.photo | F.video | F.text), States.change_post)
async def channels_actions(message: Message, state: fsm):
    text, text_len, media_id, media_type = await get_post_data(message)

    if (text_len > 1024) and media_type:
        text = await get_text(f"{handler_name}/caption_too_long")
        await message.answer(text)
        
        return
    
    await state.update_data(text=text, media_id=media_id, media_type=media_type)
    await state.set_state(States.confirm)

    text = await get_text(f"{handler_name}/confirm_post")
    await message.answer(text, reply_markup=confirm_post_button)

@router.message(F.text.lower() == "текст кнопки", States.change)
async def channels_actions(message: Message, state: fsm):
    await button_text(message, state)

@router.callback_query(PostsListCallback.filter(F.action.in_({
    ItemsListAction.switch_page, 
    ItemsListAction.get_list,
    ItemsListAction.get_list_})))
async def get_posts_list(callback: CallbackQuery, callback_data: PostsListCallback, state: fsm):
    message = callback.message
    user_id = message.chat.id

    if callback_data.action in [ItemsListAction.get_list, ItemsListAction.get_list_]:
        await state.clear()
    
    page_index = callback_data.page_index
        
    posts = await read(db_path, f"{handler_name}", "id, title", f"user_id={user_id}")
    if not posts:
        text = await get_text(f"{handler_name}/no_posts")
        if callback_data.action in [ItemsListAction.get_list, ItemsListAction.get_list_]:
            await callback.answer(text, show_alert=True)
            await swtich_button(callback)
        else:
            await message.edit_text(text, reply_markup=add_post_button)
    else:
        keyboard = await get_items_keyboard(
            items = posts,
            page_size = 10, 
            page_index = page_index, 
            item_callback_data = PostCallback, 
            items_list_callback_data=PostsListCallback)

        text = await get_text(f"{handler_name}/choose_post")
        
        if callback_data.action in [ItemsListAction.get_list, ItemsListAction.get_list_]:
            await message.answer(text, reply_markup=keyboard)
            await swtich_button(callback)
        else:
            await message.edit_text(text, reply_markup=keyboard)
    
    await state.clear()
    await swtich_button(callback)

@router.callback_query(PostCallback.filter(F.action.in_({ItemAction.get_item, ItemAction.get_item_})))
async def get_post(callback: CallbackQuery, callback_data: PostCallback, state: fsm = None):
    user_id = callback.message.chat.id
    post_id = callback_data.id

    data = await read(
        db_path=db_path, 
        table=f"{handler_name}", 
        columns="id, text, button_text, media_id, media_type, has_spoiler", 
        conditions=f"id={post_id} AND user_id={user_id}")
    
    if not data:
        text = await get_text(f"{handler_name}/post_not_found")
        await callback.answer(text, show_alert=True)
        
        return
    
    data = data[0]
    
    if state:
        await send_post(callback.message, False, *data)
        await state.clear()
        await swtich_button(callback)
    else:
        await send_post(callback.message, True, *data)

@router.callback_query(PostCallback.filter(F.action.in_(
        {ItemAction.change_title, 
        ItemAction.change_title_})))
async def change_added_title(callback: CallbackQuery, callback_data: PostCallback, state: fsm):
    text = await get_text(f"{handler_name}/enter_title")
    await callback.message.answer(text)

    await state.set_state(States.change_added_title)
    await state.update_data(changing_post_id=callback_data.id)

    await swtich_button(callback)

@router.message(F.text, States.change_added_title)
async def change_added_title(message: Message, state: fsm):
    if message.text.lower() == "назад":
        await state.clear()
        await posts_options(message, state)
        
        return

    if len(message.text) > 50:
        text = await get_text(f"{handler_name}/title_too_long")
        await message.answer(text)
        
        return
    
    data = await state.get_data()
    post_id = data.get("changing_post_id")

    await update(
        db_path=db_path,
        table=handler_name,
        columns={
            "title":message.text
        },
        conditions=f"id={post_id}")
    
    text = await get_text(f"{handler_name}/title_changed")
    await message.answer(text)

@router.callback_query(PostCallback.filter(F.action.in_(
        {ItemAction.change_post, 
        ItemAction.change_post_})))
async def change_added_post(callback: CallbackQuery, callback_data: PostCallback, state: fsm):
    text = await get_text(f"{handler_name}/send_post")
    await callback.message.answer(text)

    await state.set_state(States.change_added_post)
    await state.update_data(changing_post_id=callback_data.id)

    await swtich_button(callback)

@router.message(~F.media_group_id & (F.photo | F.video | F.text), States.change_added_post)
async def change_added_post(message: Message, state: fsm):
    text, text_len, media_id, media_type = await get_post_data(message)

    if (text_len > 1024) and media_type:
        text = await get_text(f"{handler_name}/caption_too_long")
        await message.answer(text)
        
        return
    
    data = await state.get_data()
    post_id = data.get("changing_post_id")

    if message.has_media_spoiler:
        has_spoiler = 1
    else:
        has_spoiler = 0

    await update(
        db_path=db_path,
        table=handler_name,
        columns={
            "text":text,
            "media_id":media_id,
            "media_type":media_type,
            "has_spoiler":has_spoiler
        },
        conditions=f"id={post_id} AND user_id={message.chat.id}")
    
    text = await get_text(f"{handler_name}/post_changed")
    await message.answer(text)

    await state.clear()

@router.callback_query(PostCallback.filter(F.action.in_(
        {ItemAction.change_button_text, 
        ItemAction.change_button_text_})))
async def change_button_text(callback: CallbackQuery, callback_data: PostCallback, state: fsm):
    text = await get_text(f"{handler_name}/enter_button_text")
    await callback.message.answer(text)

    await state.set_state(States.change_added_button_text)
    await state.update_data(changing_post_id=callback_data.id)

@router.message(F.text, States.change_added_button_text)
async def change_added_title(message: Message, state: fsm):
    if len(message.text) > 50:
        text = await get_text(f"{handler_name}/button_text_too_long")
        await message.answer(text)

        return
    
    data = await state.get_data()
    post_id = data.get("changing_post_id")

    await update(
        db_path=db_path,
        table=handler_name,
        columns={
            "button_text":message.text
        },
        conditions=f"id={post_id} AND user_id={message.chat.id}")
    
    text = await get_text(f"{handler_name}/button_text_changed")
    await message.answer(text)

    await state.clear()

@router.callback_query(PostCallback.filter(F.action == ItemAction.remove_item))
async def remove_post(callback: CallbackQuery, callback_data: PostCallback):
    user_id = callback.message.chat.id
    post_id = callback_data.id

    data = await read(db_path, f"{handler_name}", "*", f"id={post_id} AND user_id={user_id}")
    if not data:
        text = await get_text(f"{handler_name}/post_not_found")
        await callback.answer(text, show_alert=True)
        
        return

    button = await confirm_remove_buttons(
        item_id = post_id,
        item_callback_data = PostCallback
    )

    await callback.message.edit_reply_markup(reply_markup=button)

@router.callback_query(PostCallback.filter(F.action == ItemAction.cancel_removing))
async def cancel_removing_post(callback: CallbackQuery, callback_data: PostCallback, state: fsm):
    await get_post(callback, callback_data)

@router.callback_query(PostCallback.filter(F.action == ItemAction.confirm_remove_item))
async def confim_delete_post(callback: CallbackQuery, callback_data: PostCallback):
    user_id = callback.message.chat.id
    post_id = callback_data.id

    data = await read(db_path, f"{handler_name}", "*", f"id={post_id} AND user_id={user_id}")
    if not data:
        text = await get_text(f"{handler_name}/post_not_found")
        await callback.answer(text, show_alert=True)
        
        return
    
    await delete(db_path, f"{handler_name}", f"id={post_id} AND user_id={user_id}")

    text = await get_text(f"{handler_name}/post_removed")
    await callback.answer(text)
    # await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.delete()