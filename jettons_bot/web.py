from json import dumps, loads
from jettons_bot.crud import *
from quart import Quart, request
from aiogram import Bot
from dotenv import load_dotenv
from os import getenv
import os
from crontab import CronTab
from platform import system
from datetime import datetime

current_os = system()

load_dotenv()
bot = Bot(token=getenv("TEST_BOT_TOKEN"))

app = Quart(__name__)
db_path = f"jettons_bot/databases/giveaways.db"

@app.route('/payment_data', methods=['POST'])
async def get_payment_data():
    # if request.json:
    #     data = dumps(request.json)
    # elif request.data:
    #     data = dumps(request.data)
    # elif request.args:
    #     data = dumps(request.args)
    # else:
    #     return {"status":"error", "message":"unsupported_data"}, 415

    data = await request.get_json()
    # data = loads(data)

    if data.get("payload_text"):
        if data.get("payload_text").startswith("giveaway_id:"):
            arr = data["payload_text"].split(':')
            if len(arr) == 3:
                give_id = data["payload_text"].split(':')[1]
                type = data["payload_text"].split(':')[2]

                give_data = await read(
                        db_path=db_path,
                        table="giveaways",
                        columns="user_id, title, timestamp, jetton_address",
                        conditions=f"id:{give_id}")
                
                if data["type"] == "JETTON":
                    if data["jetton_metadata"]["jetton_master_address"] != give_data[3]:
                        return

                amount = data["amount"]

                conn = connect(db_path)
                cur = conn.cursor()
                
                if type == "ton":
                    cur.execute(f"UPDATE giveaways SET paid_ton_amount=paid_ton_amount+{amount} WHERE id={give_id}")
                    
                    await bot.send_message(int(give_data[0]), f"Пополнение комиссии в размере {amount} TON для раздачи {give_data[1]}")
                elif type == "jettons":
                    cur.execute(f"UPDATE giveaways SET paid_jettons_amount=paid_jettons_amount+{amount} WHERE id={give_id}")

                    await bot.send_message(int(give_data[0]), f"Пополнение жетонов в размере {amount} {data["jetton_metadata"]["symbol"]} раздачи {give_data[1]}")
                else:
                    return

                await create(
                    db_path="jettons_bot/databases/incomes",
                    table="incomes",
                    columns={
                        "address":data["sender"],
                        "amount":amount,
                        "give_id":give_id,
                        "type":type
                    })

                conn.commit()
                conn.close()

                amounts = await read(
                    db_path=db_path,
                    table="giveaways",
                    columns="ton_fee_amount, jettons_total_amount, paid_jettons_amount, paid_ton_amount",
                    conditions=f"id:{give_id}"
                )

                ton_fee_amount = amounts[0]
                jettons_total_amount = amounts[1]
                paid_jettons_amount = amounts[2]
                paid_ton_amount = amounts[3]
                
                if (paid_jettons_amount >= jettons_total_amount) and \
                    (paid_ton_amount >= ton_fee_amount):
    
                    if current_os == "Windows":
                        cron = CronTab(user=True)
                        command = f"c:/Users/ilnur/ju_bots/ju_bots/venv/Scripts/python.exe jettons_bot/start_giveaway.py -id {give_id}"
                    else:
                        cron = CronTab(user=True)
                        command = f"python /root/ju_bots/jettons_bot/jettons_bot/start_giveaway.py -id {give_id}"
                       
                    dtime = datetime.fromtimestamp(int(give_data[2]))
                    delta = datetime.now() - dtime
                    if (datetime.now() >= dtime) or (delta.seconds <= 60):
                        await update(
                            db_path=db_path,
                            table="giveaways",
                            columns={
                                "paid_jettons_amount":amount
                            },
                            conditions=f"id={give_id}"
                        )
                        
                        os.system(command)

                        return

                    job = cron.new(command=command)

                    job.setall(dtime)

                    cron.write()

                    await update(
                        db_path=db_path,
                        table="giveaways",
                        columns={
                            "paid_jettons_amount":amount
                        },
                        conditions=f"id={give_id}"
                    )

                    await bot.send_message(int(give_data[0]), f"Раздача {give_data[1]} запланирована!")

    return {"status":"ok"}, 200

if __name__ == '__main__':
    app.run()