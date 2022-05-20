# Implement By - @anasty17 (https://github.com/Spark-X-Cloud/SparkXcloud-Gdrive-MirrorBot/commit/0bfba523f095ab1dccad431d72561e0e002e7a59)
# (c) https://github.com/Spark-X-Cloud/SparkXcloud-Gdrive-MirrorBot
# All rights reserved

import time
import requests
import os
import subprocess
from dotenv import load_dotenv

CONFIG_FILE_URL = os.environ.get('CONFIG_FILE_URL', None)
if CONFIG_FILE_URL is not None:
    out = subprocess.run(["wget", "-q", "-O", "config.env", CONFIG_FILE_URL])

load_dotenv('config.env')

BASE_URL = os.environ.get('BASE_URL_OF_BOT', None)
if len(BASE_URL) == 0:
    BASE_URL = None

IS_VPS = os.environ.get('IS_VPS', 'False')
IS_VPS = IS_VPS.lower() == 'true'

if not IS_VPS and BASE_URL is not None:
    while True:
        time.sleep(1000)
        status = requests.get(BASE_URL).status_code
