# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Depends
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from pydantic import BaseModel
import pg8000

import logging
import re

import time
import asyncio

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
#postgres://tiktok_ethiopia_user:787ddC53ERWXkZdYjiiNHhQ5ACDVqri9@dpg-ckbvu76ct0pc738n81b0-a.oregon-postgres.render.com/tiktok_ethiopia
#postgres://tiktok_ethiopia_user:787ddC53ERWXkZdYjiiNHhQ5ACDVqri9@dpg-ckbvu76ct0pc738n81b0-a.oregon-postgres.render.com/tiktok_ethiopia
db_params = {
    'host': 'dpg-ckbvu76ct0pc738n81b0-a.oregon-postgres.render.com',
    'database': 'tiktok_ethiopia',
    'user': 'tiktok_ethiopia_user',
    'password': '787ddC53ERWXkZdYjiiNHhQ5ACDVqri9',
    'ssl_context': True
    
}
while True:
    try:
        
        conn = pg8000.connect(**db_params)
        cursor = conn.cursor()
        print('Database connection was successful')
        break

    except (pg8000.OperationalError, pg8000.InterfaceError) as e:
        print("Error connecting to PostgreSQL:", e)
        time.sleep(4)  # Wait for 4 seconds before retrying


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

async def checkForAssholes():
    while True:
        await asyncio.sleep(6000)
        print("Asshole Damage cleared")
        cursor.execute("""UPDATE users
            SET shared_status = false
            WHERE last_shared IS NOT NULL
            AND EXTRACT(EPOCH FROM (NOW() - last_shared)) > 600;""" )
        conn.commit()

loop = asyncio.get_event_loop()
loop.create_task(checkForAssholes())

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
        keyboard = [[InlineKeyboardButton("English 🇺🇸", callback_data='1'),
                 InlineKeyboardButton("Amharic 🇪🇹", callback_data='2')]]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await bot.send_message(chat_id=chat_id, text='Welcome, please choose a Language:', reply_markup=reply_markup)

        await bot.send_message(chat_id=chat_id, text="Welcome, please enter a link to your YouTube/TikTok channel.\n እንኳን ደህና መጣችሁ፣ እባኮትን ወደ YouTube/TikTok ቻናላችሁ የሚወስድ አገናኝ ሊንክ ያስገቡ።")
    elif text == "/subscribe":
        cursor.execute("""SELECT chat_id, link from users where shared_status=false ORDER BY last_shared""")
        result = cursor.fetchone()
        if result is None:
            default_values = {
                'chat_id': 6081026054,
                'link': "https://vm.tiktok.com/ZM6euGGGA/"
            }
            result = default_values

        
        link = result['link']
        cursor.execute("""UPDATE users SET shared_status=true where chat_id=%s""", (result['chat_id'],))
        cursor.execute("""UPDATE users SET viewing=%s where chat_id=%s""", (result['chat_id'], chat_id))
        conn.commit()
        await bot.send_message(chat_id=chat_id, reply_to_message_id=update.message["message_id"], text="Send the message /subscribed when your subscription is complete " + link)

    elif text == "/subscribed":
        cursor.execute("""SELECT viewing FROM users WHERE chat_id=%s""", (chat_id,))

        result = cursor.fetchone()

        if result is None:
            await bot.send_message(
                chat_id=chat_id,
                text="Please subscribe first and subscribe to somebody on our system."
            )
            return

        cursor.execute("""
            UPDATE users 
            SET last_shared = CASE 
                WHEN shares = 0 THEN NOW() 
                ELSE last_shared 
            END,
            shares = shares + 1 
            WHERE chat_id = %s
            """, (chat_id,))
        
        cursor.execute("""UPDATE users SET shares = shares - 1, last_shared = NOW(), shared_status = false where chat_id = %s""", (result["viewing"],))
        conn.commit()
        await bot.send_message(
                chat_id=chat_id,
                text="Thank You for subscribing, now someone else will subscribe to you."
            )
        await bot.send_message(
                chat_id=result["viewing"],
                text="A new user should have subscribed to you, /report if they haven't."
            )
        
    else:
        user_message = text
        # Check if the message looks like a link
        if is_valid_url(user_message):
            received_link = re.search(r'https?://\S+', user_message).group()
            cursor.execute("""INSERT INTO users (link, chat_id) VALUES (%s, %s)""", (received_link, chat_id))
            
            conn.commit()
            await bot.send_message(
                chat_id=chat_id,
                text=f"Thank you for providing the link: {received_link}"
            )
        else:
            await bot.send_message(
                chat_id=chat_id,
                text="Sorry, I don't think that is quite right. Please enter a valid link."
            )

    return {"ok": True}


def is_valid_url(text):
    # This regular expression pattern checks for a typical URL format
    url_pattern = r'(https?|ftp|file|mailto)://[\w~\/:%#\$&\?\(\)~\.=\+\-]+(\?[\w~\/:%#\$&\?\(\)~\.=\+\-]*)?(#[\w~\/:%#\$&\?\(\)~\.=\+\-]*)?'

    return re.search(url_pattern, text)
