import os
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Depends
from telegram import Update, Bot
from pydantic import BaseModel

import logging
import re
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import asyncio

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

#postgres://tiktok_ethiopia_user:787ddC53ERWXkZdYjiiNHhQ5ACDVqri9@dpg-ckbvu76ct0pc738n81b0-a.oregon-postgres.render.com/tiktok_ethiopia
db_params = {
    'host': 'dpg-ckbvu76ct0pc738n81b0-a.oregon-postgres.render.com',
    'database': 'tiktok_ethiopia',
    'user': 'tiktok_ethiopia_user',
    'password': '787ddC53ERWXkZdYjiiNHhQ5ACDVqri9'
}
while True:
    try:
        conn = psycopg2.connect(**db_params, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        print('Database connection was successful')
        break

    except Exception as error:
        print("Connection to database failed")
        print("Error: ", error)
        time.sleep(4)

class TelegramUpdate(BaseModel):
    update_id: int
    message: dict

app = FastAPI()

# Load variables from .env file if present
load_dotenv()

# Read the variable from the environment (or .env file)
bot_token = "6533909241:AAFSwMipYM1Fd6l9iS6A50J5dRhN-BrvjrM"
secret_token = os.getenv("SECRET_TOKEN")
# webhook_url = os.getenv('CYCLIC_URL', 'http://localhost:8181') + "/webhook/"

bot = Bot(token=bot_token)
# bot.set_webhook(url=webhook_url)
# webhook_info = bot.get_webhook_info()
# print(webhook_info)

def auth_telegram_token(x_telegram_bot_api_secret_token: str = Header(None)) -> str:
    return True # uncomment to disable authentication
    if x_telegram_bot_api_secret_token != secret_token:
        raise HTTPException(status_code=403, detail="Not authenticated")
    return x_telegram_bot_api_secret_token

@app.post("/webhook/")
async def handle_webhook(update: TelegramUpdate, token: str = Depends(auth_telegram_token)):
    chat_id = update.message["chat"]["id"]
    text = update.message["text"]
    print("Received message:", update.message)

    if text == "/start":
        await bot.send_message(chat_id=chat_id, text="Welcome, please enter a link to your channel.")
    elif text == "/subscribe":
        cursor.execute("""SELECT chat_id, link from users where shared_status=false ORDER BY last_shared""")
        result = cursor.fetchone()
        if result is None:
            default_values = {
                'chat_id': 6081026054,
                'link': "https://www.youtube.com/watch?v=W9q-0tCfvKE"
            }
            result = default_values

            chat_id = result['chat_id']
            link = result['link']
            cursor.execute("""UPDATE users SET shared_status=true where chat_id=%s""", (chat_id,))
            cursor.execute("""UPDATE users SET viewing=%s where chat_id=%s""", (chat_id, update.effective_chat.id))
            conn.commit()
            await bot.send_message(chat_id=chat_id, reply_to_message_id=update.message["message_id"], text="Send the message /subscribed when your subscription is complete " + link)

    return {"ok": True}
