from crud import *
import asyncio
import sqlite3
import argparse
from pytoniq import *
from os import getenv
from dotenv import load_dotenv
from aiogram import Bot
from get_message import get_text
from json import load

load_dotenv()

bot = Bot(token=getenv("TEST_BOT_TOKEN"))

parser = argparse.ArgumentParser()
parser.add_argument('-mode')
parser.add_argument('-sec')
args = parser.parse_args()

interval_seconds = int(args.sec)
db_path = f"jettons_bot/databases/giveaways.db"

async def send_jettons(address, jetton_address, amount):
  with open("ls_cfg.json") as cfg:
    cfg = load(cfg)
  
  client = LiteClient.from_config(
    config=cfg,
    trust_level=9999999,
    timeout=99
  )
  
  mnemonics = getenv("MNEMONICS").split()

  await client.connect()
  wallet = await BaseWallet.from_mnemonic(provider=client, mnemonics=mnemonics, version='v4r2')


  body = begin_cell() \
    .store_uint(0x0f8a7ea5,32) \
    .store_uint(0,64) \
    .store_coins(int(amount)*(10**9)) \
    .store_address(Address(address)) \
    .store_address(Address(wallet.address)) \
    .store_bool(False) \
    .store_coins(1) \
    .store_maybe_ref(begin_cell().store_uint(0,32).store_string("?").end_cell()) \
    .end_cell()


  await wallet.transfer(
    destination=jetton_address,
    amount=int(float(amount)*(10**9)), 
    body=body
  )

  await client.close()



async def send_ton(address, amount):
  with open("ls_cfg.json") as cfg:
    cfg = load(cfg)
  
  client = LiteClient.from_config(
    config=cfg,
    trust_level=9999999,
    timeout=99
  )
  
  mnemonics = getenv("MNEMONICS").split()

  await client.connect()
  wallet = await BaseWallet.from_mnemonic(provider=client, mnemonics=mnemonics, version='v4r2')
  await wallet.get_seqno()

  await wallet.transfer(
    destination=address,
    amount=int(float(amount)*(10**9)), 
  )

  await client.close()

async def sender():
    claims = await read(
        db_path="jettons_bot/databases/claims_queue.db",
        table="claims_queue",
        columns="*",
        conditions="status='user_claim' OR status='stop_giveaway'"
    )
    if len(claims) > 0:
      claim = claims[0]

      claim_id = claim[0]
      user_id = claim[1]
      give_id = claim[2]
      status = claim[3]
      address = claim[4]

      give_data = await read(
          db_path=db_path,
          table="giveaways",
          columns="gives_count, cur_gived_count, status, jetton_address, ton_fee_amount, jettons_total_amount, cur_gived_total_amount, jetton_address",
          conditions=f"id={give_id}"
      )

      if status == "user_claim":
        if give_data[2] != "active":
          await update(
              db_path="jettons_bot/databases/claims_queue.db",
              table="claims_queue",
              columns={
                  "status":"inactive_giveaway"
              },
              conditions=f"id={claim_id}"
          )

          text = get_text("giveaways/not_valid_giveaway")
          await bot.send_message(user_id, text)

          return False

        if give_data[0]==give_data[1]:
            await update(
                db_path="jettons_bot/databases/claims_queue.db",
                table="claims_queue",
                columns={
                    "status":"lated"
                },
                conditions=f"id={claim_id}"
            )
            text = get_text("giveaways/user_lated")
            await bot.send_message(user_id, text)

            return False
        else:
          amount = await read(
              db_path=db_path,
              table="giveaways",
              columns="onchain_count",
              conditions=f"id={give_id}"
          )[0][0]

          await send_jettons(
            address=address,
            jetton_address=give_data[3],
            amount=amount)
          
          await update(
              db_path="jettons_bot/databases/claims_queue.db",
              table="claims_queue",
              columns={
                  "status":"claimed"
              },
              conditions=f"id={claim_id}"
          )

          conn = connect(db_path)
          cur = conn.cursor()
                  
          cur.execute(f"UPDATE giveaways SET cur_gived_count=cur_gived_count+1 WHERE id={give_id}")
          conn.commit()

          cur.execute(f"UPDATE giveaways SET cur_gived_total_amount=cur_gived_total_amount+onchain_count*(1+jettons_fee/100) WHERE id={give_id}")
          conn.commit()

          conn.close()

          text = f"Жетоны в размере {amount} отправлены на кошелек, который Вы подключали при получении!"
          await bot.send_message(user_id, text)

          return True
      elif status == "stop_giveaway":
          ton_income = await read(
            db_path="jettons_bot/databases/incomes",
            table="incomes",
            columns="address",
            conditions=f"give_id={give_id} AND type='ton'"
          )

          
          if len(ton_income) > 0:
            ton_fee = float(getenv("TON_FEE"))
            amount = float(give_data[4])-int(give_data[1])*ton_fee
            if amount > 0:
              await send_ton(ton_income[0], amount)
              
              await asyncio.sleep(interval_seconds)

          income = await read(
            db_path="jettons_bot/databases/incomes",
            table="incomes",
            columns="address",
            conditions=f"give_id={give_id} AND type='jettons'"
          )
          
          if len(income) == 0:
             await update(
                db_path="jettons_bot/databases/claims_queue.db",
                table="claims_queue",
                columns={
                    "status":"claimed"
                },
                conditions=f"id={claim_id}"
            )
             
             return False

          amount = float(give_data[5])-float(give_data[6])
          if amount > 0:
            await send_jettons(income[0], give_data[7], amount)

            await update(
                db_path="jettons_bot/databases/claims_queue.db",
                table="claims_queue",
                columns={
                    "status":"claimed"
                },
                conditions=f"id={claim_id}"
            )

            return True
    else:
       return False

async def run_sender():
    while True:
        res = await sender()
        if res:
          await asyncio.sleep(interval_seconds)
        else:
          await asyncio.sleep(1)

asyncio.get_event_loop().create_task(run_sender())
asyncio.get_event_loop().run_forever()
