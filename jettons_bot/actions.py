from enum import Enum

class ItemAction(str, Enum):
    get_item = "get"
    get_item_ = "get_"
    
    remove_item = "remove"
    confirm_remove_item = "confirm_remove"
    cancel_removing = "cancel_remove"
    
    add_item = "add"
    add_item_ = "add_"

    change_title = "change_title"
    change_post = "change_post"
    change_button_text = "change_button_text"

    change_jetton_address = "change_jetton_address"
    change_onchain_count = "change_onchain_count"
    change_rocket_count = "change_rocket_count"
    
    change_title_ = "change_title_"
    change_post_ = "change_post_"
    change_button_text_ = "change_button_text_"

    change_jetton_address_ = "change_jetton_address_"
    change_onchain_count_ = "change_onchain_count_"
    change_rocket_count_ = "change_rocket_count_"

    resend_post = "resend"
    resend_post_ = "resend_"

class ItemsListAction(str, Enum):
    switch_page = "switch_page"
    get_list = "get_list"
    get_list_ = "get_list_"