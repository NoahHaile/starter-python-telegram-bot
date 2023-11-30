# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Depends
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from pydantic import BaseModel
import pg8000

import logging
import re
from typing import Optional, Dict
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
    message: Optional[Dict] = None
    callback_query: Optional[Dict] = None

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
            AND EXTRACT(EPOCH FROM (NOW() - last_shared)) > 1200;""" )
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
    chat_id = ""
    text = ""
    if update.message:
        # Handle message update
        # Extract chat_id and text from update.message
        chat_id = update.message["chat"]["id"]
        text = update.message.get("text", "")
    print("Received message:", update.message)

    if text == "/start":
        keyboard = [[InlineKeyboardButton("English 🇺🇸", callback_data='EN'),
                 InlineKeyboardButton("አማርኛ 🇪🇹", callback_data='AM')]]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await bot.send_message(chat_id=chat_id, text='Welcome, please choose a Language:', reply_markup=reply_markup)

        

    elif update.callback_query:
        query = update.callback_query
        chat_id = query["message"]["chat"]["id"]
        callback_data = query["data"]
        
        # Acknowledge the callback query
        await bot.answer_callback_query(callback_query_id=query["id"])

        # Process the callback data
        if callback_data == "EN":
            
            await bot.send_message(chat_id=chat_id, text="Please enter a link to your YouTube/TikTok channel.")
        elif callback_data == "AM":
            
            await bot.send_message(chat_id=chat_id, text="እባኮትን ወደ YouTube/TikTok ቻናላችሁ የሚወስድ አገናኝ ሊንክ ያስገቡ።")

        elif callback_data == "SUB":
            cursor.execute("""SELECT chat_id, link from users where shared_status=false ORDER BY last_shared""")
            result = cursor.fetchone()
            if result is None:
                default_values = {
                    'chat_id': 6081026054,
                    'link': "https://vm.tiktok.com/ZM6euGGGA/"
                }
                await bot.send_message(chat_id=chat_id, text="Sorry, we can't pair you up right now. Check back in a little while.")
                await bot.send_message(chat_id=chat_id, text="Brought to you by... " + default_values["link"])
                return
                

            
            link = result[1]
            cursor.execute("""UPDATE users SET shared_status=true where chat_id=%s""", (result[0],))
            cursor.execute("""UPDATE users SET viewing=%s where chat_id=%s""", (result[0], chat_id))
            conn.commit()
            keyboard = [[InlineKeyboardButton("Subscribed 🫡", callback_data='SUBBED'),
                         InlineKeyboardButton("Already Subscribed 🤝", callback_data='ALREADY_SUBBED')]]

            reply_markup = InlineKeyboardMarkup(keyboard)

            await bot.send_message(chat_id=chat_id, text=link)
            await bot.send_message(chat_id=chat_id, text=link + '\nPress "Subscribed" once subscribed, or "Already Subscribed" if you are already subscribed to the link above.', reply_markup=reply_markup)
           

        elif text == "ALREADY_SUBBED":

            cursor.execute("""SELECT chat_id, link from users where shared_status=false ORDER BY last_shared""")
            result = cursor.fetchone()
            if result is None:
                default_values = {
                    'chat_id': 6081026054,
                    'link': "https://vm.tiktok.com/ZM6euGGGA/"
                }

                await bot.send_message(chat_id=chat_id, text="Sorry, we can't pair you up right now. Check back in a little while.")
                await bot.send_message(chat_id=chat_id, text="Brought to you by... " + default_values["link"])
                return


            chat_id_store = result[0]
            link = result[1]
            cursor.execute("""UPDATE users SET shared_status=true where chat_id=%s""", (chat_id_store,))
            cursor.execute("""UPDATE users SET viewing=%s where chat_id=%s""", (chat_id_store, chat_id))
            conn.commit()
            cursor.execute("""SELECT viewing FROM users WHERE chat_id=%s""", (chat_id,))

            result = cursor.fetchone()
            cursor.execute("""UPDATE users SET shared_status = false where chat_id = %s""", (result["viewing"],))
            conn.commit()
            keyboard = [[InlineKeyboardButton("Subscribed 🫡", callback_data='SUBBED'),
                         InlineKeyboardButton("Already Subscribed 🤝", callback_data='ALREADY_SUBBED')]]

            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await bot.send_message(chat_id=chat_id, text="Sorry about that, I will generate a new channel you can subscribe to. Check back in a little while if we can't pair you up.")
            await bot.send_message(chat_id=chat_id, text=link)
            await bot.send_message(chat_id=chat_id, text=link + '\nPress "Subscribed" once subscribed, or "Already Subscribed" if you are already subscribed to the link above.', reply_markup=reply_markup)


        elif text == "SUBBED":
            cursor.execute("""SELECT viewing FROM users WHERE chat_id=%s""", (chat_id,))

            result = cursor.fetchone()

            keyboard = [[InlineKeyboardButton("Start Subscribing 👍🏽", callback_data='SUB')]]

            reply_markup = InlineKeyboardMarkup(keyboard)

            if result is None:
                
                await bot.send_message(chat_id=chat_id, text='You have taken more than 20 minutes to subscribe, please try again!', reply_markup=reply_markup)
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
                    , reply_markup=reply_markup
                )
            await bot.send_message(
                    chat_id=result["viewing"],
                    text="A new user should have subscribed to you, /report them if they haven't and they will be banned."
                    , reply_markup=reply_markup
                )
    elif text == '/report':
           await bot.send_message(
                    chat_id=chat_id,
                    text="Your Report has been noted and the system will put the user under review. Thank you."
                    
           )
    else:
        user_message = text
        # Check if the message looks like a link
        if is_valid_url(user_message):
            received_link = re.search(r'https?://\S+', user_message).group()
            cursor.execute("""INSERT INTO users (link, chat_id) VALUES (%s, %s)""", (received_link, chat_id))
            
            conn.commit()
            keyboard = [[InlineKeyboardButton("Start Subscribing 👍🏽", callback_data='SUB')]]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await bot.send_message(
                chat_id=chat_id,
                text=f"Thank you for providing the link: {received_link}"
            )
            await bot.send_message(chat_id=chat_id, text='Great, press subscribe and get started!', reply_markup=reply_markup)
            
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
