import logging
import os
import sys
import threading
import time
import random
import string
import subprocess

import aria2p

import telegram.ext as tg
from dotenv import load_dotenv
from pyrogram import Client
from telegraph import Telegraph

import psycopg2
from psycopg2 import Error

import socket
import faulthandler
faulthandler.enable()

socket.setdefaulttimeout(600)

botStartTime = time.time()
if os.path.exists('log.txt'):
    with open('log.txt', 'r+') as f:
        f.truncate(0)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('log.txt'), logging.StreamHandler()],
                    level=logging.INFO)

LOGGER = logging.getLogger(__name__)

load_dotenv('config.env')

Interval = []


def getConfig(name: str):
    return os.environ[name]

def mktable():
    try:
        conn = psycopg2.connect(DB_URI)
        cur = conn.cursor()
        sql = "CREATE TABLE users (uid bigint, sudo boolean DEFAULT FALSE);"
        cur.execute(sql)
        conn.commit()
        LOGGER.info("Table Created!")
    except Error as e:
        LOGGER.error(e)
        sys.exit(1)

try:
    if bool(getConfig('_____REMOVE_THIS_LINE_____')):
        logging.error('The README.md file there to be read! Exiting now!')
        sys.exit()
except KeyError:
    pass

aria2 = aria2p.API(
    aria2p.Client(
        host="http://localhost",
        port=6800,
        secret="",
    )
)

        return None


DOWNLOAD_DIR = None
BOT_TOKEN = None

download_dict_lock = threading.Lock()
status_reply_dict_lock = threading.Lock()
# Key: update.effective_chat.id
# Value: telegram.Message
status_reply_dict = {}
# Key: update.message.message_id
# Value: An object of Status
download_dict = {}
# Stores list of users and chats the bot is authorized to use in
AUTHORIZED_CHATS = set()
SUDO_USERS = set()
if os.path.exists('authorized_chats.txt'):
    with open('authorized_chats.txt', 'r+') as f:
        lines = f.readlines()
        for line in lines:
            AUTHORIZED_CHATS.add(int(line.split()[0]))
if os.path.exists('sudo_users.txt'):
    with open('sudo_users.txt', 'r+') as f:
        lines = f.readlines()
        for line in lines:
            SUDO_USERS.add(int(line.split()[0]))
try:
    achats = getConfig('AUTHORIZED_CHATS')
    achats = achats.split(" ")
    for chats in achats:
        AUTHORIZED_CHATS.add(int(chats))
except:
    pass
try:
    schats = getConfig('SUDO_USERS')
    schats = schats.split(" ")
    for chats in schats:
        SUDO_USERS.add(int(chats))
except:
    pass
try:
    BOT_TOKEN = getConfig('BOT_TOKEN')
    parent_id = getConfig('GDRIVE_FOLDER_ID')
    DOWNLOAD_DIR = getConfig('DOWNLOAD_DIR')
    if not DOWNLOAD_DIR.endswith("/"):
        DOWNLOAD_DIR = DOWNLOAD_DIR + '/'
    DOWNLOAD_STATUS_UPDATE_INTERVAL = int(getConfig('DOWNLOAD_STATUS_UPDATE_INTERVAL'))
    OWNER_ID = int(getConfig('OWNER_ID'))
    AUTO_DELETE_MESSAGE_DURATION = int(getConfig('AUTO_DELETE_MESSAGE_DURATION'))
    TELEGRAM_API = getConfig('TELEGRAM_API')
    TELEGRAM_HASH = getConfig('TELEGRAM_HASH')
    UPSTREAM_REPO = getConfig('UPSTREAM_REPO')
    UPSTREAM_BRANCH = getConfig('UPSTREAM_BRANCH')
except KeyError as e:
    LOGGER.error("One or more env variables missing! Exiting now")
    sys.exit(1)
try:
    DB_URI = getConfig('DATABASE_URL')
    if len(DB_URI) == 0:
        raise KeyError
except KeyError:
    logging.warning('Database not provided!')
    DB_URI = None
if DB_URI is not None:
    try:
        conn = psycopg2.connect(DB_URI)
        cur = conn.cursor()
        sql = "SELECT * from users;"
        cur.execute(sql)
        rows = cur.fetchall()  #returns a list ==> (uid, sudo)
        for row in rows:
            AUTHORIZED_CHATS.add(row[0])
            if row[1]:
                SUDO_USERS.add(row[0])
    except Error as e:
        if 'relation "users" does not exist' in str(e):
            mktable()
        else:
            LOGGER.error(e)
            sys.exit(1)
    finally:
        cur.close()
        conn.close()

LOGGER.info("Generating USER_SESSION_STRING")
app = Client(':memory:', api_id=int(TELEGRAM_API), api_hash=TELEGRAM_HASH, bot_token=BOT_TOKEN)

# Generate Telegraph Token
sname = ''.join(random.SystemRandom().choices(string.ascii_letters, k=8))
LOGGER.info("Generating TELEGRAPH_TOKEN using '" + sname + "' name")
telegraph = Telegraph()
telegraph.create_account(short_name=sname)
telegraph_token = telegraph.get_access_token()

try:
    HEROKU_API_KEY = getConfig('HEROKU_API_KEY')
except KeyError:
    logging.warning('HEROKU API KEY not provided!')
    HEROKU_API_KEY = None
try:
    HEROKU_APP_NAME = getConfig('HEROKU_APP_NAME')
except KeyError:
    logging.warning('HEROKU APP NAME not provided!')
    HEROKU_APP_NAME = None
try:
    UPTOBOX_TOKEN = getConfig('UPTOBOX_TOKEN')
except KeyError:
    logging.warning('UPTOBOX_TOKEN not provided!')
    UPTOBOX_TOKEN = None
try:
    INDEX_URL = getConfig('INDEX_URL')
    if len(INDEX_URL) == 0:
        INDEX_URL = None
except KeyError:
    INDEX_URL = None
try:
    TORRENT_DIRECT_LIMIT = getConfig('TORRENT_DIRECT_LIMIT')
    if len(TORRENT_DIRECT_LIMIT) == 0:
        TORRENT_DIRECT_LIMIT = None
except KeyError:
    TORRENT_DIRECT_LIMIT = None
try:
    CLONE_LIMIT = getConfig('CLONE_LIMIT')
    if len(CLONE_LIMIT) == 0:
        CLONE_LIMIT = None
except KeyError:
    CLONE_LIMIT = None
try:
    MEGA_LIMIT = getConfig('MEGA_LIMIT')
    if len(MEGA_LIMIT) == 0:
        MEGA_LIMIT = None
except KeyError:
    MEGA_LIMIT = None
try:
    TAR_UNZIP_LIMIT = getConfig('TAR_UNZIP_LIMIT')
    if len(TAR_UNZIP_LIMIT) == 0:
        TAR_UNZIP_LIMIT = None
except KeyError:
    TAR_UNZIP_LIMIT = None
try:
    TORRENT_TIMEOUT = getConfig('TORRENT_TIMEOUT')
    if len(TORRENT_TIMEOUT) == 0:
        raise KeyError
    TORRENT_TIMEOUT = int(TORRENT_TIMEOUT)
except:
    TORRENT_TIMEOUT = None
try:        
    BUTTON_FOUR_NAME = getConfig('BUTTON_FOUR_NAME')
    BUTTON_FOUR_URL = getConfig('BUTTON_FOUR_URL')
    if 0 in (len(BUTTON_FOUR_NAME), len(BUTTON_FOUR_URL)):
        raise KeyError
except KeyError:
    BUTTON_FOUR_NAME = None
    BUTTON_FOUR_URL = None
try:
    BUTTON_FIVE_NAME = getConfig('BUTTON_FIVE_NAME')
    BUTTON_FIVE_URL = getConfig('BUTTON_FIVE_URL')
    if 0 in (len(BUTTON_FIVE_NAME), len(BUTTON_FIVE_URL)):
        raise KeyError
except KeyError:
    BUTTON_FIVE_NAME = None
    BUTTON_FIVE_URL = None
try:
    BUTTON_SIX_NAME = getConfig('BUTTON_SIX_NAME')
    BUTTON_SIX_URL = getConfig('BUTTON_SIX_URL')
    if 0 in (len(BUTTON_SIX_NAME), len(BUTTON_SIX_URL)):
        raise KeyError
except KeyError:
    BUTTON_SIX_NAME = None
    BUTTON_SIX_URL = None
try:
    IMAGE_URL = getConfig('IMAGE_URL')
    if len(IMAGE_URL) == 0:
        IMAGE_URL = 'https://telegra.ph/file/7ac7fa23a5c3d2bbba654.jpg'
except KeyError:
    IMAGE_URL = 'https://telegra.ph/file/7ac7fa23a5c3d2bbba654.jpg'    
try:
    STOP_DUPLICATE = getConfig('STOP_DUPLICATE')
    STOP_DUPLICATE = STOP_DUPLICATE.lower() == 'true'
except KeyError:
    STOP_DUPLICATE = False
try:
    VIEW_LINK = getConfig('VIEW_LINK')
    VIEW_LINK = VIEW_LINK.lower() == 'true'
except KeyError:
    VIEW_LINK = False
try:
    IS_TEAM_DRIVE = getConfig('IS_TEAM_DRIVE')
    IS_TEAM_DRIVE = IS_TEAM_DRIVE.lower() == 'true'
except KeyError:
    IS_TEAM_DRIVE = False
try:
    USE_SERVICE_ACCOUNTS = getConfig('USE_SERVICE_ACCOUNTS')
    USE_SERVICE_ACCOUNTS = USE_SERVICE_ACCOUNTS.lower() == 'true'
except KeyError:
    USE_SERVICE_ACCOUNTS = False
try:
    BLOCK_MEGA_FOLDER = getConfig('BLOCK_MEGA_FOLDER')
    BLOCK_MEGA_FOLDER = BLOCK_MEGA_FOLDER.lower() == 'true'
except KeyError:
    BLOCK_MEGA_FOLDER = False
try:
    BLOCK_MEGA_LINKS = getConfig('BLOCK_MEGA_LINKS')
    BLOCK_MEGA_LINKS = BLOCK_MEGA_LINKS.lower() == 'true'
except KeyError:
    BLOCK_MEGA_LINKS = False
try:
    SHORTENER = getConfig('SHORTENER')
    SHORTENER_API = getConfig('SHORTENER_API')
    if 0 in (len(SHORTENER), len(SHORTENER_API)):
        raise KeyError
except KeyError:
    SHORTENER = None
    SHORTENER_API = None

IGNORE_PENDING_REQUESTS = False
try:
    if getConfig("IGNORE_PENDING_REQUESTS").lower() == "true":
        IGNORE_PENDING_REQUESTS = True
except KeyError:
    pass

try:
    BASE_URL = getConfig('BASE_URL_OF_BOT')
    if len(BASE_URL) == 0:
        BASE_URL = None
except KeyError:
    logging.warning('BASE_URL_OF_BOT not provided!')
    BASE_URL = None

try:
    TOKEN_PICKLE_URL = getConfig('TOKEN_PICKLE_URL')
    if len(TOKEN_PICKLE_URL) == 0:
        TOKEN_PICKLE_URL = None
    else:
        out = subprocess.run(["wget", "-q", "-O", "token.pickle", TOKEN_PICKLE_URL])
        if out.returncode != 0:
            logging.error(out)
except KeyError:
    TOKEN_PICKLE_URL = None

try:
    ACCOUNTS_ZIP_URL = getConfig('ACCOUNTS_ZIP_URL')
    if len(ACCOUNTS_ZIP_URL) == 0:
        ACCOUNTS_ZIP_URL = None
    else:
        out = subprocess.run(["wget", "-q", "-O", "accounts.zip", ACCOUNTS_ZIP_URL])
        if out.returncode != 0:
            logging.error(out)
            raise KeyError
        subprocess.run(["unzip", "-q", "-o", "accounts.zip"])
        os.remove("accounts.zip")
except KeyError:
    ACCOUNTS_ZIP_URL = None

updater = tg.Updater(token=BOT_TOKEN)
bot = updater.bot
dispatcher = updater.dispatcher
