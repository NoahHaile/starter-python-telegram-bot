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

def checkForAssholes():
    while True:
        print("Asshole Damage cleared")
        cursor.execute("""UPDATE users
            SET shared_status = %s,
            last_shared = NOW() - INTERVAL '1 year'
            WHERE EXTRACT(EPOCH FROM (NOW() - last_shared)) > 1200 AND link != "User has not yet input a link";""", (False, ) )
        conn.commit()



def auth_telegram_token(x_telegram_bot_api_secret_token: str = Header(None)) -> str:
    return True # uncomment to disable authentication
    if x_telegram_bot_api_secret_token != secret_token:
        raise HTTPException(status_code=403, detail="Not authenticated")
    return x_telegram_bot_api_secret_token
i = 0
@app.post("/webhook/")
async def handle_webhook(update: TelegramUpdate, token: str = Depends(auth_telegram_token)):
    global i
    chat_id = ""
    text = ""
    if i % 10 == 0:
        checkForAssholes()
    i += 1

    
    if update.message:
        # Handle message update
        # Extract chat_id and text from update.message
        chat_id = update.message["chat"]["id"]
        text = update.message.get("text", "")
    print("Received message:", update.message)

    if text == "/start":
        keyboard = [[InlineKeyboardButton("English 🇺🇸", callback_data='EN'),
                 InlineKeyboardButton("አማርኛ 🇪🇹 (ሙከራ)", callback_data='AM')]]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await bot.send_message(chat_id=chat_id, text='Welcome, please choose a Language:', reply_markup=reply_markup)

        

    elif update.callback_query:
        
        query = update.callback_query
        chat_id = query["message"]["chat"]["id"]
        callback_data = query["data"]
        print(callback_data)
        
        cursor.execute("""SELECT chat_id FROM users WHERE chat_id=%s AND shares>=10""", (chat_id,))
        banned = cursor.fetchone()
        if banned is not None:
            await bot.send_message(chat_id=chat_id, text="You have been banned for suspicious activities. If you think this is a mistake, message me at @EthioLite42.")
            return
            
        # Process the callback data
        if callback_data == "EN":
            cursor.execute("""SELECT chat_id FROM users WHERE chat_id=%s""", (chat_id,))

            row = cursor.fetchone()
            if row is None:
                cursor.execute("""INSERT INTO users (link, chat_id, language, shared_status) VALUES (%s, %s, %s, %s)""", ("User has not yet input a link", chat_id, "EN", True, ))
                cursor.execute("""INSERT INTO names (chat_id, firstName) VALUES (%s, %s)""", (chat_id, update.message["chat"]["first_name"],))
            else:
                cursor.execute("""UPDATE users SET language=%s where chat_id=%s""", ("EN", chat_id,))
            
            
            conn.commit()

            keyboard = [[InlineKeyboardButton("Done 👍🏽", callback_data='DONE')]]

            reply_markup = InlineKeyboardMarkup(keyboard)

            await bot.send_message(chat_id=chat_id, text="To get started, follow this channel. If you are already subscribed, just click done... The system will verify it. https://vm.tiktok.com/ZM6euGGGA/", reply_markup=reply_markup)
            
        elif callback_data == "AM":

            cursor.execute("""SELECT chat_id FROM users WHERE chat_id=%s""", (chat_id,))

            row = cursor.fetchone()
            if row is None:
                cursor.execute("""INSERT INTO users (link, chat_id, language, shared_status) VALUES (%s, %s, %s, %s)""", ("User has not yet input a link", chat_id, "AM", True,))
                cursor.execute("""INSERT INTO names (chat_id, firstName) VALUES (%s, %s)""", (chat_id, update.message["chat"]["first_name"],))
            else:
                cursor.execute("""UPDATE users SET language=%s where chat_id=%s""", ("AM", chat_id,))
            
            conn.commit()
            keyboard = [[InlineKeyboardButton("Done 👍🏽", callback_data='DONE')]]

            reply_markup = InlineKeyboardMarkup(keyboard)

            await bot.send_message(chat_id=chat_id, text="ለመጀመር ይህን ቻናል ይከተሉ። ቀድሞውንም ተመዝጋቢ ከሆኑ በቀላሉ 'Done' ጠቅ ያድርጉ... በሲስተሙ ይጣራል። https://vm.tiktok.com/ZM6euGGGA/", reply_markup=reply_markup)
            


        elif callback_data == "DONE":
            cursor.execute("""SELECT language FROM users WHERE chat_id=%s""", (chat_id,))

            lang = cursor.fetchone()

            if lang[0] == "AM":
                await bot.send_message(chat_id=chat_id, text="እባኮትን ወደ YouTube/TikTok ቻናላችሁ የሚወስድ አገናኝ ሊንክ ላኩልን።")

            else:
                await bot.send_message(chat_id=chat_id, text="Please enter a link to your YouTube/TikTok channel.")

        elif callback_data == "SUB":
            cursor.execute("""SELECT chat_id, link 
                FROM users 
                WHERE shared_status = %s AND chat_id != %s
                ORDER BY 
                    CASE 
                        WHEN shares < 0 THEN 2 
                        WHEN shares >= 1 THEN 0 
                        ELSE 1 
                    END, 
                    last_shared ASC;""", (False, chat_id,))
            result = cursor.fetchone()
            cursor.execute("""SELECT language FROM users WHERE chat_id=%s""", (chat_id,))

            lang = cursor.fetchone()
            if result is None:
                default_values = {
                    'chat_id': 6081026054,
                    'link': "https://vm.tiktok.com/ZM6euGGGA/"
                }
                keyboard = [[InlineKeyboardButton("Get more Subscribers 👍🏽(COME BACK IN A FEW MINUTES THOUGH)", callback_data='SUB')]]

            
                reply_markup = InlineKeyboardMarkup(keyboard)
                if lang[0] == "AM":
                    await bot.send_message(chat_id=chat_id, text="ይቅርታ፣ አሁን ለእርስዎ ተዛማጅ ማግኘት አልቻልንም። ከትንሽ ቆይታ በኋላ እንደገና ይሞክሩ።", reply_markup=reply_markup)
                else:
                    await bot.send_message(chat_id=chat_id, text="Sorry, we can't pair you up right now. Check back in a little while.", reply_markup=reply_markup)
                return
                

            
            link = result[1]
            cursor.execute("""UPDATE users SET shared_status=%s, last_shared = NOW() where chat_id=%s""", (True, result[0],))
            cursor.execute("""UPDATE users SET viewing=%s where chat_id=%s""", (result[0], chat_id))
            conn.commit()
            keyboard = [[InlineKeyboardButton("Subscribed 🫡", callback_data="SUBBED"),
                         InlineKeyboardButton("Already Subscribed 🤝", callback_data="ALREADY_SUBBED")]]

            reply_markup = InlineKeyboardMarkup(keyboard)
            if lang[0] == "AM":
                await bot.send_message(chat_id=chat_id, text=link + '\nአንዴ ከተመዘገቡ በኋላ "Subscribed" የሚለውን ይጫኑ ወይም ደሞ፤ ከላይ ላለው ሊንክ ቀድሞ ከተመዘገቡ "Already Subscribed" የሚለውን ይጫኑ።', reply_markup=reply_markup)
            else:
                await bot.send_message(chat_id=chat_id, text=link + '\nPress "Subscribed" once subscribed, or "Already Subscribed" if you are already subscribed to the link above.', reply_markup=reply_markup)
           

        elif callback_data == "ALREADY_SUBBED":

            cursor.execute("""SELECT language FROM users WHERE chat_id=%s""", (chat_id,))

            lang = cursor.fetchone()

            cursor.execute("""SELECT chat_id, link 
                FROM users 
                WHERE shared_status = %s AND chat_id != %s
                ORDER BY 
                    CASE 
                        WHEN shares < 0 THEN 2 
                        WHEN shares >= 1 THEN 0 
                        ELSE 1 
                    END, 
                    last_shared ASC;""", (False, chat_id,))
            result = cursor.fetchone()
            if result is None:
                default_values = {
                    'chat_id': 6081026054,
                    'link': "https://vm.tiktok.com/ZM6euGGGA/"
                }
                keyboard = [[InlineKeyboardButton("Get more Subscribers 👍🏽(COME BACK IN A FEW MINUTES THOUGH)", callback_data='SUB')]]

            
                reply_markup = InlineKeyboardMarkup(keyboard)

                if lang[0] == "AM":
                    await bot.send_message(chat_id=chat_id, text="ይቅርታ፣ አሁን ለእርስዎ ተዛማጅ ማግኘት አልቻልንም። ከትንሽ ቆይታ በኋላ እንደገና ይሞክሩ።", reply_markup=reply_markup)
                else:
                    await bot.send_message(chat_id=chat_id, text="Sorry, we can't pair you up right now. Check back in a little while.", reply_markup=reply_markup)
                cursor.execute("""SELECT viewing FROM users WHERE chat_id=%s""", (chat_id,))

                result = cursor.fetchone()
                cursor.execute("""UPDATE users SET shared_status = %s where chat_id = %s""", (False, result[0],))
                cursor.execute("""UPDATE users SET viewing=NULL where chat_id=%s""", (chat_id,))
                conn.commit()
                return


            chat_id_store = result[0]
            link = result[1]

            cursor.execute("""SELECT viewing FROM users WHERE chat_id=%s""", (chat_id,))

            viewing = cursor.fetchone()
            cursor.execute("""UPDATE users SET shared_status = %s where chat_id = %s""", (False, viewing[0],))

            cursor.execute("""UPDATE users SET shared_status=%s, last_shared = NOW() where chat_id=%s""", (True, chat_id_store,))
            
            
            
            cursor.execute("""UPDATE users SET viewing=%s where chat_id=%s""", (chat_id_store, chat_id))
            conn.commit()
            keyboard = [[InlineKeyboardButton("Subscribed 🫡", callback_data="SUBBED"),
                         InlineKeyboardButton("Already Subscribed 🤝", callback_data="ALREADY_SUBBED")]]

            reply_markup = InlineKeyboardMarkup(keyboard)
            
            
            if lang[0] == "AM":
                await bot.send_message(chat_id=chat_id, text="ይቅርታ፣ መመዝገብ የምትችሉበትን አዲስ ቻናል እናዘጋጃለን። ተመሳሳይ ቻናሎች ደጋግመው ካገኙ ደሞ፤ ትንሽ ጊዜ ጠብቀው ይመለሱ።")
                await bot.send_message(chat_id=chat_id, text=link + '\nአንዴ ከተመዘገቡ በኋላ "Subscribed" የሚለውን ይጫኑ ወይም ደሞ፤ ከላይ ላለው ሊንክ ቀድሞ ከተመዘገቡ "Already Subscribed" የሚለውን ይጫኑ።', reply_markup=reply_markup)
                

            else:
                await bot.send_message(chat_id=chat_id, text="Sorry about that, I will generate a new channel you can subscribe to. Check back in a little while if you keep getting the same channels.")
                await bot.send_message(chat_id=chat_id, text=link + '\nPress "Subscribed" once subscribed, or "Already Subscribed" if you are already subscribed to the link above.', reply_markup=reply_markup)


        elif callback_data == "SUBBED":

            cursor.execute("""SELECT language FROM users WHERE chat_id=%s""", (chat_id,))

            lang = cursor.fetchone()
            
            cursor.execute("""SELECT viewing FROM users WHERE chat_id=%s""", (chat_id,))

            result = cursor.fetchone()

            keyboard = [[InlineKeyboardButton("Get more Subscribers 👍🏽", callback_data='SUB')]]

            
            reply_markup = InlineKeyboardMarkup(keyboard)

            if result is None:
                if lang[0] == "AM":
                    await bot.send_message(chat_id=chat_id, text='ለመመዝገብ ማንንም አላስመዘገብክም። እባክዎ ዳግም ይሞክሩ!!', reply_markup=reply_markup)
                else:
                    await bot.send_message(chat_id=chat_id, text="You haven't added anyone to subscribe to. Please try again!", reply_markup=reply_markup)
                return

            cursor.execute("""UPDATE users SET shares = shares + 1,
                viewing = NULL
                WHERE chat_id = %s
                """, (chat_id,))
            
            cursor.execute("""UPDATE users SET shares = shares - 1, shared_status = %s where chat_id = %s""", (False, result[0],))
            conn.commit()
            if lang[0] == "AM":
                await bot.send_message(
                        chat_id=chat_id,
                        text="'Subscribe' ስላደረጉ እናመሰግናለን፣ አሁን ሌላ ሰው ለናንተ 'Subscribe' ያደርግላችሗል።"
                        , reply_markup=reply_markup
                    )
                cursor.execute("""SELECT language FROM users WHERE chat_id=%s""", (result[0],))

                lang2 = cursor.fetchone()
                if lang2[0] == "AM":
                    await bot.send_message(
                            chat_id=result[0],
                            text="አዲስ 'Subscriber' ለእርስዎ መመዝገብ አለበት፣ ካላደረጉ /report ያድርጉ እና ይታገዳሉ።"
                            , reply_markup=reply_markup
                        )
                else:
                    await bot.send_message(
                    chat_id=result[0],
                    text="A new user should have subscribed to you, /report them if they haven't and they will be banned."
                    , reply_markup=reply_markup
                )
            else:
                await bot.send_message(
                        chat_id=chat_id,
                        text="Thank You for subscribing, now someone else will subscribe to you."
                        , reply_markup=reply_markup
                    )
                cursor.execute("""SELECT language FROM users WHERE chat_id=%s""", (result[0],))

                lang2 = cursor.fetchone()
                if lang2[0] == "AM":
                    await bot.send_message(
                            chat_id=result[0],
                            text="አዲስ 'Subscriber' ለእርስዎ መመዝገብ አለበት፣ ካላደረጉ /report ያድርጉ እና ይታገዳሉ።"
                            , reply_markup=reply_markup
                        )
                else:
                    await bot.send_message(
                    chat_id=result[0],
                    text="A new user should have subscribed to you, /report them if they haven't and they will be banned."
                    , reply_markup=reply_markup
                )
    elif text == '/report':
           
        cursor.execute("""SELECT language FROM users WHERE chat_id=%s""", (chat_id,))

        lang = cursor.fetchone()
        keyboard = [[InlineKeyboardButton("Start Subscribing 👍🏽", callback_data='SUB')]]

        reply_markup = InlineKeyboardMarkup(keyboard)
        if lang[0] == "AM":
                    await bot.send_message(chat_id=chat_id, text='የእርስዎ ሪፖርት ተመዝግቧል እና ለደንበኝነት መመዝገብ የነበረበት ተጠቃሚ ይታገዳል። እናመሰግናለን!', reply_markup=reply_markup)
        else:
                    await bot.send_message(
                    chat_id=chat_id,
                    text="Your Report has been noted and the system will ban the user who should have subscribed. Thank you!"
                    ,reply_markup=reply_markup
                    
           )
        
           
    else:
        user_message = text
        cursor.execute("""SELECT language FROM users WHERE chat_id=%s""", (chat_id,))

        lang = cursor.fetchone()
        # Check if the message looks like a link
        if is_valid_url(user_message):
            received_link = re.search(r'https?://\S+', user_message).group()

            cursor.execute("""SELECT chat_id FROM users WHERE chat_id=%s""", (chat_id,))

            exists = cursor.fetchone()

            if exists is None:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"Pick a Language First!"
                )
                return
            
            cursor.execute("""UPDATE users SET link = %s, shared_status = %s where chat_id = %s""", (received_link, False, chat_id, ))
            
            conn.commit()
            keyboard = [[InlineKeyboardButton("Start Subscribing 👍🏽", callback_data='SUB')]]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await bot.send_message(
                chat_id=chat_id,
                text=f"Thank you for providing the link: {received_link}"
            )
            
            if lang[0] == "AM":
                await bot.send_message(chat_id=chat_id, text='በጣም ጥሩ፣ እባክዎን ሰብስክራይብ የሚለውን ቁልፍ ይጫኑ እና ይጀምሩ!', reply_markup=reply_markup)
            else:
                await bot.send_message(chat_id=chat_id, text='Great, press subscribe and get started!', reply_markup=reply_markup)
            
        else:
            if lang[0] == "AM":
                await bot.send_message(
                    chat_id=chat_id,
                    text="ይቅርታ፣ አገናኙ ትክክል አይመስለኝም። እባክዎ ትክክለኛ አገናኝ ያስገቡ።"
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
