from sqlite3 import connect

def create_tables():
    con = connect("jettons_bot/databases/channels.db")
    cur = con.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            user_id INT,
            channel_id INT,
            title TEXT
        )''')
    
    con.commit()
    con.close()

    con = connect("jettons_bot/databases/posts.db")
    cur = con.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY,
            user_id INT,
            title TEXT,
            button_text TEXT,
            text TEXT,
            media_id TEXT,
            media_type TEXT,
            has_spoiler BOOLEAN
        )''')
    
    con.commit()
    con.close()

    con = connect("jettons_bot/databases/giveaways.db")
    cur = con.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS giveaways (
            id INTEGER PRIMARY KEY,
            title TEXT
            user_id INT,
            post_title TEXT,
            post_id TEXT,
            channel_title TEXT,
            jetton_address TEXT,
            channel_id TEXT,
            timestamp INT,
            delete_hours TEXT,
            sub_hours INT,
            onchain_count REAL,
            rocket_count REAL,
            gives_count INT,
            status TEXT,
            channel_post_id INT,
            cur_gived_count INT DEFAULT 0,
            cur_gived_total_amount REAL DEFAULT 0,
            jettons_fee REAL,
            jettons_total_amount REAL,
            ton_fee_amount REAL,
            paid_jettons_amount REAL DEFAULT 0,
            paid_ton_amount REAL DEFAULT 0,
            paid_rocket_amoint REAL DEFAULT 0
        )''')
    
    con.commit()
    con.close()

    # con = connect("jettons_bot/databases/wallets.db")
    # cur = con.cursor()

    # cur.execute('''
    #     CREATE TABLE IF NOT EXISTS wallets (
    #         user_id INT,
    #         wallet_address TEXT
    #     )''')
    
    # con.commit()
    # con.close()

    con = connect("jettons_bot/databases/claims_queue.db")
    cur = con.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS claims_queue (
            id INTEGER PRIMARY KEY,
            user_id INT,
            give_id INT,
            status TEXT,
            wallet_address TEXT
        )''')
    
    con.commit()
    con.close()

    con = connect("jettons_bot/databases/incomes.db")
    cur = con.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS incomes (
            id INTEGER PRIMARY KEY,
            address TEXT,
            give_id INT,
            amount REAL,
            type TEXT
        )''')
    
    con.commit()
    con.close()

if __name__ == "__main__":
    create_tables()