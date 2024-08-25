## Recommendation before use

# 🔥🔥 Use PYTHON 3.10 🔥🔥

## Features  
| Feature                                                   | Supported |
|-----------------------------------------------------------|:---------:|
| Multithreading                                            |     ✅     |
| Proxy binding to session                                  |     ✅     |
| Support for tdata / pyrogram .session / telethon .session |     ✅     |
| Auto-farming                                              |     ✅     |
| Auto-tasks                                                |     ✅     |
| Auto-upgrade                                              |     ✅     |
| Auto-check-in                                             |     ✅     |


## [Settings](https://github.com/vanhbakaa/Seed-App-Mine-Seed-BOT-Telegram/blob/main/.env-example)
| Settings                |                                 Description                                 |
|-------------------------|:---------------------------------------------------------------------------:|
| **API_ID / API_HASH**   | Platform data from which to run the Telegram session (by default - android) |
| **AUTO_UPGRADE_STORAGE**|                   Auto upgrade storage  (by default - True)                 |
| **AUTO_UPGRADE_MINING** |                  Auto upgrade mining speed (by default - True)              |
| **AUTO_UPGRADE_HOLY**   |                    Auto upgrade holy (by default - True)                    |
| **AUTO_TASK**           |                       Auto tasks (default - True)                           |
| **USE_PROXY_FROM_FILE** | Whether to use a proxy from the bot/config/proxies.txt file (True / False)  |

## Quick Start 📚

To fast install libraries and run bot - open run.bat on Windows or run.sh on Linux

## Prerequisites
Before you begin, make sure you have the following installed:
- [Python](https://www.python.org/downloads/) **version 3.10**

## Obtaining API Keys
1. Go to my.telegram.org and log in using your phone number.
2. Select "API development tools" and fill out the form to register a new application.
3. Record the API_ID and API_HASH provided after registering your application in the .env file.


# Linux manual installation
```shell
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
cp .env-example .env
nano .env  # Here you must specify your API_ID and API_HASH, the rest is taken by default
python3 main.py
```

You can also use arguments for quick start, for example:
```shell
~/OkxRacerBot >>> python3 main.py --action (1/2)
# Or
~/OkxRacerBot >>> python3 main.py -a (1/2)

# 1 - Run clicker
# 2 - Creates a session
```

# Windows manual installation
```shell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env-example .env
# Here you must specify your API_ID and API_HASH, the rest is taken by default
python main.py
```

You can also use arguments for quick start, for example:
```shell
~/OkxRacerBot >>> python main.py --action (1/2)
# Or
~/OkxRacerBot >>> python main.py -a (1/2)

# 1 - Run clicker
# 2 - Creates a session
```

### Contacts

For support or questions, you can contact me [![Static Badge](https://img.shields.io/badge/Telegram-Channel-Link?style=for-the-badge&logo=Telegram&logoColor=white&logoSize=auto&color=blue)](https://t.me/Vanhday1)
