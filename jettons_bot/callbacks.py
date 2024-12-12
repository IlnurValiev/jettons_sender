from aiogram.filters.callback_data import CallbackData

class ChannelCallback(CallbackData, prefix="ch"):
    action: str
    id: int

class ChannelsListCallback(CallbackData, prefix="ch_ls"):
    action: str
    page_index: int

class PostCallback(CallbackData, prefix="post"):
    action: str
    id: int

class PostsListCallback(CallbackData, prefix="posts_ls"):
    action: str
    page_index: int

class GetJettonsCallback(CallbackData, prefix="jet"):
    wallet_type: str
    id: int

class GiveawayCallback(CallbackData, prefix="give"):
    action: str
    id: int

class GiveawaysListCallback(CallbackData, prefix="gives_ls"):
    action: str
    page_index: int

class GivePostCallback(CallbackData, prefix="g_post"):
    action: str
    id: int

class GivePostsListCallback(CallbackData, prefix="g_post_ls"):
    action: str
    page_index: int

class GiveChannelCallback(CallbackData, prefix="g_chan"):
    action: str
    id: int

class GiveChannelsListCallback(CallbackData, prefix="g_chan_ls"):
    action: str
    page_index: int

class GiveDateCallback(CallbackData, prefix="g_date"):
    day: int
    month: int
    year: int

class GiveDeleteTimeCallback(CallbackData, prefix="g_del_time"):
    hours: int

class GiveSubCheckHours(CallbackData, prefix="g_sub_hours"):
    hours: int

class StopGiveawayCallback(CallbackData, prefix="stop_give"):
    wallet_type: str
    give_id: int