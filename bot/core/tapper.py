import asyncio
from datetime import datetime
from urllib.parse import unquote, quote

import aiohttp
import pytz
import requests
from aiocfscrape import CloudflareScraper
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.types import InputBotAppShortName
from pyrogram.raw.functions.messages import RequestAppWebView
from bot.core.agents import generate_random_user_agent
from bot.config import settings

from bot.utils import logger
from bot.exceptions import InvalidSession
from .headers import headers

from random import randint, uniform
import traceback
import time


#api endpoint
api_claim = 'https://elb.seeddao.org/api/v1/seed/claim'
api_balance = 'https://elb.seeddao.org/api/v1/profile/balance'
api_checkin = 'https://elb.seeddao.org/api/v1/login-bonuses'
api_upgrade_storage = 'https://elb.seeddao.org/api/v1/seed/storage-size/upgrade'
api_upgrade_mining = 'https://elb.seeddao.org/api/v1/seed/mining-speed/upgrade'
api_upgrade_holy = 'https://elb.seeddao.org/api/v1/upgrades/holy-water'
api_profile = 'https://elb.seeddao.org/api/v1/profile'
api_hunt_completed = 'https://elb.seeddao.org/api/v1/bird-hunt/complete'
api_bird_info = "https://elb.seeddao.org/api/v1/bird/is-leader"
api_make_happy = 'https://elb.seeddao.org/api/v1/bird-happiness'
api_get_worm_data = "https://elb.seeddao.org/api/v1/worms/me-all"
api_feed = "https://elb.seeddao.org/api/v1/bird-feed"
api_start_hunt = "https://elb.seeddao.org/api/v1/bird-hunt/start"
api_inv = "https://elb.seeddao.org/api/v1/worms/me"
api_sell = "https://elb.seeddao.org/api/v1/market-item/add"



class Tapper:
    def __init__(self, tg_client: Client):
        self.tg_client = tg_client
        self.session_name = tg_client.name
        self.first_name = ''
        self.last_name = ''
        self.user_id = ''
        self.Total_Point_Earned = 0
        self.Total_Game_Played = 0
        self.worm_lvl = {"common": 1,
                         "uncommon": 2,
                         "rare": 3,
                         "epic": 4,
                         "legendary": 5}
        self.total_earned_from_sale = 0
        self.total_on_sale = 0
        self.worm_in_inv = {"common": 0, "uncommon": 0, "rare": 0, "epic": 0, "legendary": 0}
        self.worm_in_inv_copy = {"common": 0, "uncommon": 0, "rare": 0, "epic": 0, "legendary": 0}

    async def get_tg_web_data(self, proxy: str | None) -> str:
        logger.info(f"Getting data for {self.session_name}")
        if proxy:
            proxy = Proxy.from_str(proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict

        try:
            if not self.tg_client.is_connected:
                try:
                    await self.tg_client.connect()

                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            while True:
                try:
                    peer = await self.tg_client.resolve_peer('seed_coin_bot')
                    break
                except FloodWait as fl:
                    fls = fl.value

                    logger.warning(f"<light-yellow>{self.session_name}</light-yellow> | FloodWait {fl}")
                    logger.info(f"<light-yellow>{self.session_name}</light-yellow> | Sleep {fls}s")

                    await asyncio.sleep(fls + 3)

            web_view = await self.tg_client.invoke(RequestAppWebView(
                peer=peer,
                app=InputBotAppShortName(bot_id=peer, short_name="app"),
                platform='android',
                write_allowed=True,
            ))

            auth_url = web_view.url
            tg_web_data = unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])

            if self.tg_client.is_connected:
                await self.tg_client.disconnect()

            return tg_web_data

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(f"<light-yellow>{self.session_name}</light-yellow> | Unknown error during Authorization: "
                         f"{error}")
            await asyncio.sleep(delay=3)

    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy) -> None:
        try:
            response = await http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")

    async def fetch_profile(self, http_client: aiohttp.ClientSession) -> None:
        response = await http_client.get(url=api_profile)
        if response.status == 200:
            response_json = await response.json()
            logger.info(f"{self.session_name} | <green>Got into seed app - Username: {response_json['data']['name']}</green>")
            upgrade_levels = {}
            for upgrade in response_json['data']['upgrades']:
                upgrade_type = upgrade['upgrade_type']
                upgrade_level = upgrade['upgrade_level']
                if upgrade_type in upgrade_levels:
                    if upgrade_level > upgrade_levels[upgrade_type]:
                        upgrade_levels[upgrade_type] = upgrade_level
                else:
                    upgrade_levels[upgrade_type] = upgrade_level
            for upgrade_type, level in upgrade_levels.items():
                logger.info(f"{self.session_name} | <cyan>{upgrade_type.capitalize()} Level: {level+1}</cyan>")
        else:
            logger.warning(f"Can't get account data for session: {self.session_name}. <red>response status: {response.status}</red>")

    async def upgrade_storage(self,http_client: aiohttp.ClientSession) -> None:
        response = await http_client.post(url=api_upgrade_storage)
        if response.status == 200:
            logger.success(f"{self.session_name} | <yellow>Upgrade Storage Successfully</yellow>")

    async def upgrade_mining(self, http_client: aiohttp.ClientSession) -> None:
        response = await http_client.post(url=api_upgrade_mining)
        if response.status == 200:
            logger.success(f"{self.session_name} | <yellow>Upgrade Mining Successfully</yellow>")

    async def upgrade_holy(self, http_client: aiohttp.ClientSession) -> None:
        response = await http_client.post(url=api_upgrade_holy)
        if response.status == 200:
            logger.success(f"{self.session_name} | <yellow>Upgrade Holy Successfully</yellow>")

    async def verify_balance(self, http_client: aiohttp.ClientSession):
        response = await http_client.get(url=api_balance)
        if response.status == 200:
            balance_info = await response.json()
            logger.info(f"{self.session_name} | <cyan>Balance: {balance_info['data'] / 1000000000}</cyan>")
            return True
        else:
            logger.error(f"{self.session_name} | <red>Balance: Error | {response.status}</red>")

    async def perform_daily_checkin(self, http_client: aiohttp.ClientSession):
        response = await http_client.post(api_checkin)
        if response.status == 200:
            checkin_data = await response.json()
            day = checkin_data.get('data', {}).get('no', '')
            logger.success(f"{self.session_name} | <green>Successfully checked in | Day {day}</green>")
        else:
            checkin_data = await response.json()
            if checkin_data.get('message') == 'already claimed for today':
                logger.info(f"{self.session_name} | Already checked in today")
            else:
                logger.info(f"{self.session_name} | Failed | {checkin_data}")

    async def fetch_worm_status(self, http_client: aiohttp.ClientSession):
        response = await http_client.get('https://elb.seeddao.org/api/v1/worms')
        if response.status == 200:
            worm_info = await response.json()
            next_refresh = worm_info['data'].get('next_worm')
            worm_caught = worm_info['data'].get('is_caught', False)
            if next_refresh:
                next_refresh_dt = datetime.fromisoformat(next_refresh[:-1] + '+00:00')
                now_utc = datetime.now(pytz.utc)
                time_difference_seconds = (next_refresh_dt - now_utc).total_seconds()
                hours = int(time_difference_seconds // 3600)
                minutes = int((time_difference_seconds % 3600) // 60)
                logger.info(f"{self.session_name} | Next Worm in {hours} hours {minutes} minutes - Status: {'Caught' if worm_caught else 'Available'}")
            else:
                logger.info(f"{self.session_name} | 'next_worm' data not available.")
            return worm_info['data']
        else:
            logger.error(f"{self.session_name} | Error retrieving worm data.")
            return None

    async def capture_worm(self, http_client: aiohttp.ClientSession):
        worm_info = await self.fetch_worm_status(http_client)
        if worm_info and not worm_info.get('is_caught', True):
            response = await http_client.post('https://elb.seeddao.org/api/v1/worms/catch')
            if response.status == 200:
                logger.success(f"{self.session_name} | <green>Worm Captured Successfully</green>")
            elif response.status == 400:
                logger.info(f"{self.session_name} | Already captured")
            elif response.status == 404:
                logger.info(f"{self.session_name} | Worm not found")
            else:
                logger.error(f"{self.session_name} | <red>Capture failed, status code: {response.status}</red>")
        else:
            logger.info(f"{self.session_name} | Worm unavailable or already captured.")


    async def fetch_tasks(self, http_client: aiohttp.ClientSession):
        response = await http_client.get('https://elb.seeddao.org/api/v1/tasks/progresses')
        tasks = await response.json()
        for task in tasks['data']:
            if task['task_user'] is None or not task['task_user']['completed']:
                await self.mark_task_complete(task['id'], task['name'], http_client)

    async def mark_task_complete(self, task_id, task_name, http_client: aiohttp.ClientSession):
        response = await http_client.post(f'https://elb.seeddao.org/api/v1/tasks/{task_id}')
        if response.status == 200:
            logger.success(f"{self.session_name} | <green>Task {task_name} marked complete.</green>")
        else:
            logger.error(f"{self.session_name} | Failed to complete task {task_name}, status code: {response.status}")

    def claim_hunt_reward(self, bird_id):
        payload = {
            "bird_id": bird_id
        }
        response = requests.post(api_hunt_completed, json=payload, headers=headers)
        if response.status_code == 200:
            response_data = response.json()
            logger.success(f"{self.session_name} | <green>Successfully claimed {response_data['data']['seed_amount']/(10**9)} seed from hunt reward.</green>")
        else:
            response_data = response.json()
            print(response_data)
            logger.error(f"{self.session_name} | Failed to claim hunt reward, status code: {response.status_code}")

    async def get_bird_info(self,  http_client: aiohttp.ClientSession):
        response = await http_client.get(api_bird_info)
        if response.status == 200:
            response_data = await response.json()
            return response_data['data']
        else:
            return None

    def make_bird_happy(self, bird_id):
        payload = {
            "bird_id": bird_id,
            "happiness_rate": 10000
        }
        response = requests.post(api_make_happy, json=payload, headers=headers)
        if response.status_code == 200:
            return True
        else:
            return False

    def get_worm_data(self):
        response = requests.get(api_get_worm_data, headers=headers)
        if response.status_code == 200:
            response_data = response.json()
            return response_data['data']
        else:
            return None

    def feed_bird(self,bird_id, worm_id):
        payload = {
            "bird_id": bird_id,
            "worm_ids": worm_id
        }
        response = requests.post(api_feed, json = payload, headers=headers)
        if response.status_code == 200:
            response_data = response.json()
            logger.success(f"{self.session_name} | <green>Feed bird successfully</green>")
            try:
                return response_data['energy_max'] - response_data['energy_level']
            except:
                return response_data['energy_level']
        else:
            response_data = response.json()
            print(response_data)
            logger.info(f"{self.session_name} | Failed to feed bird, response code:{response.status_code}")
            return None

    def start_hunt(self, bird_id):
        payload = {
            "bird_id": bird_id,
            "task_level": 0
        }
        response = requests.post(api_start_hunt, json=payload, headers=headers)
        if response.status_code == 200:
            logger.success(f"{self.session_name} | <green>Successfully start hunting</green>")
        else:
            print(response.json())
            logger.error(f"{self.session_name} | Start hunting failed..., response code: {response.status_code}")

    def get_worms(self):
        worms = []
        first_page = requests.get(api_inv+"?page=1", headers=headers)
        json_page = first_page.json()

        for worm in json_page['data']['items']:
            worms.append(worm)
            if worm['on_market'] is False:
                self.worm_in_inv[worm['type']] += 1
        count = 0
        if json_page['data']['total'] % json_page['data']['page_size'] != 0:
            count = 1
        total_page = int(float(json_page['data']['total'] / json_page['data']['page_size'])) + count
        for page in range(2, total_page+1):
            api_url = api_inv + f"?page={page}"
            page_data = requests.get(api_url, headers=headers)
            json_page = page_data.json()
            for worm in json_page['data']['items']:
                worms.append(worm)
                if worm['on_market'] is False:
                    self.worm_in_inv[worm['type']] += 1
            time.sleep(uniform(1,2))
        return worms

    def sell_worm(self, worm_id, price, worm_type):
        payload = {
            "price": price,
            "worm_id": worm_id
        }
        response = requests.post(api_sell, json=payload, headers=headers)
        if response.status_code == 200:
            self.total_on_sale += 1
            logger.success(f"{self.session_name} | <green>Sell {worm_type} worm successfully, price: {price/1000000000}</green>")
        else:
            response_data = response.json()
            print(response_data)
            logger.info(f"{self.session_name} | Failed to sell {worm_type} worm, response code:{response.status_code}")
            return None

    def get_price(self, worm_type):
        api = f"https://elb.seeddao.org/api/v1/market/v2?market_type=worm&worm_type={worm_type}&sort_by_price=ASC&sort_by_updated_at=&page=1"
        response = requests.get(api, headers=headers)
        if response.status_code == 200:
            json_r = response.json()
            return json_r['data']['items'][0]['price_gross']
        else:
            return 0

    def get_sale_data(self):
        api = "https://elb.seeddao.org/api/v1/history-log-market/me?market_type=worm&page=1&history_type=sell"
        response = requests.get(api, headers=headers)
        json_data = response.json()
        worm_on_sale = {"common": 0, "uncommon": 0, "rare": 0, "epic": 0, "legendary": 0}
        for worm in json_data['data']['items']:
            if worm['status'] == "on-sale":
                worm_on_sale[worm['worm_type']] += 1
            elif worm['status'] == "bought":
                self.total_earned_from_sale += worm['price_net']/1000000000
        count = 0
        if json_data['data']['total'] % json_data['data']['page_size'] != 0:
            count = 1
        total_page = int(float(json_data['data']['total'] / json_data['data']['page_size'])) + count
        for page in range(2, total_page + 1):
            response = requests.get(f"https://elb.seeddao.org/api/v1/history-log-market/me?market_type=worm&page={page}&history_type=sell", headers=headers)
            json_data = response.json()
            for worm in json_data['data']['items']:
                if worm['status'] == "on-sale":
                    worm_on_sale[worm['worm_type']] += 1
                elif worm['status'] == "bought":
                    self.total_earned_from_sale += worm['price_net'] / 1000000000

        return worm_on_sale

    def refresh_data(self):
        self.total_earned_from_sale = 0
        self.worm_in_inv = self.worm_in_inv_copy

    async def run(self, proxy: str | None) -> None:
        access_token_created_time = 0
        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None

        headers["user-agent"] = generate_random_user_agent(device_type='android', browser_type='chrome')
        http_client = CloudflareScraper(headers=headers, connector=proxy_conn)

        if proxy:
            await self.check_proxy(http_client=http_client, proxy=proxy)

        token_live_time = randint(3500, 3600)
        while True:
            try:
                if time.time() - access_token_created_time >= token_live_time:
                    logger.info(f"{self.session_name} | Update auth token...")
                    tg_web_data = await self.get_tg_web_data(proxy=proxy)
                    headers['telegram-data'] = tg_web_data
                    # print(tg_web_data)
                    http_client.headers["telegram-data"] = tg_web_data
                    access_token_created_time = time.time()
                    token_live_time = randint(3500, 3600)
                    await asyncio.sleep(delay=randint(10, 15))

                await self.fetch_profile(http_client)

                if settings.AUTO_START_HUNT:
                    bird_data = await self.get_bird_info(http_client)
                    if bird_data is None:
                        logger.info(f"{self.session_name} | Can't get bird data...")
                    elif bird_data['status'] == "hunting":

                        try:
                            given_time = datetime.fromisoformat(bird_data['hunt_end_at'])
                            timestamp_naive = given_time.replace(tzinfo=None)
                        except:
                            import dateutil.parser
                            timestamp_naive = dateutil.parser.isoparse(bird_data['hunt_end_at'])
                        now = datetime.utcnow()
                        if now < timestamp_naive:
                            logger.info(f"{self.session_name} | Bird currently hunting...")
                        else:
                            logger.info(f"{self.session_name} | Hunt completed, claiming reward...")
                            self.claim_hunt_reward(bird_data['id'])
                    else:
                        condition = True
                        if bird_data['happiness_level'] == 0:
                            logger.info(f"{self.session_name} | Bird is not happy, attemping to make bird happy...")
                            check = self.make_bird_happy(bird_data['id'])
                            if check:
                                logger.success(f"{self.session_name} | <green>Successfully make bird happy!</green>")
                            else:
                                logger.info(f"{self.session_name} |Failed to make bird happy!")
                                condition = False
                        if bird_data['energy_level'] == 0:
                            logger.info(f"{self.session_name} | Bird is hungry, attemping to feed bird...")
                            worms = self.get_worm_data()
                            if worms is None:
                                condition = False
                                logger.info(f"{self.session_name} | Failed to fetch worm data")
                            elif len(worms) == 0:
                                logger.warning(f"{self.session_name} | You dont have any worm to feed bird!")
                                condition = False
                            else:
                                try:
                                    energy = bird_data['energy_max']
                                except:
                                    energy = 1000000000
                                for worm in worms:
                                    if worm['type'] == "common":
                                        wormss = [worm['id']]
                                        energy -= self.feed_bird(bird_data['id'], wormss)
                                        if energy <= 1000000000:
                                            break
                                if energy > 1000000000:
                                    for worm in worms:
                                        if worm['type'] == "uncommon":
                                            wormss = [worm['id']]
                                            energy -= self.feed_bird(bird_data['id'], wormss)
                                            if energy <= 1000000000:
                                                break
                                if energy > 1000000000:
                                    condition = False

                        if condition:
                            self.start_hunt(bird_data['id'])

                if settings.AUTO_UPGRADE_STORAGE:
                    await self.upgrade_storage(http_client)
                    await asyncio.sleep(1)
                if settings.AUTO_UPGRADE_MINING:
                    await self.upgrade_mining(http_client)
                    await asyncio.sleep(1)
                if settings.AUTO_UPGRADE_HOLY:
                    await self.upgrade_holy(http_client)
                    await asyncio.sleep(1)

                check_balance = await self.verify_balance(http_client)
                if check_balance:
                    response = await http_client.post(api_claim)
                    if response.status == 200:
                        logger.success(f"{self.session_name} | <green> Claim successful </green>")
                    elif response.status == 400:
                        logger.info(f"{self.session_name} | Not yet time to claim")
                    else:
                        logger.error(f"{self.session_name} | <red>An error occurred, status code: {response.status}</red>")

                    await self.perform_daily_checkin(http_client)
                    await self.capture_worm(http_client)
                if settings.AUTO_SELL_WORMS:
                    logger.info(f"{self.session_name} | Fetching worms data to put it on sale...")
                    worms = self.get_worms()
                    # print(self.worm_in_inv)
                    worms_on_sell = self.get_sale_data()
                    logger.info(f"{self.session_name} | Worms on sale now: ")
                    for worm in worms_on_sell:
                        logger.info(f"{self.session_name} | Total <cyan>{worm}</cyan> on sale: <yellow>{worms_on_sell[worm]}</yellow>")
                    logger.info(f"{self.session_name} | Total earned from sale: <yellow>{self.total_earned_from_sale}</yellow>")
                    for worm in worms:
                        if worm['on_market']:
                            continue
                        elif settings.QUANTITY_TO_KEEP[worm['type']]['quantity_to_keep'] == -1:
                            continue
                        elif settings.QUANTITY_TO_KEEP[worm['type']]['quantity_to_keep'] < self.worm_in_inv[worm['type']]:
                            if settings.QUANTITY_TO_KEEP[worm['type']]['sale_price'] == 0:
                                price_to_sell = self.get_price(worm['type'])

                            else:
                                price_to_sell = settings.QUANTITY_TO_KEEP[worm['type']]['sale_price']*(10**9)
                            # print(f"Sell {worm['type']} , price: {price_to_sell/1000000000}")
                            self.sell_worm(worm['id'], price_to_sell, worm['type'])
                            self.worm_in_inv[worm['type']] -= 1

                    self.refresh_data()
                if settings.AUTO_CLEAR_TASKS:
                    await self.fetch_tasks(http_client)

                delay_time = randint(3400, 3600)
                logger.info(f"{self.session_name} | Completed {self.session_name}, waiting {delay_time} seconds...")
                await asyncio.sleep(delay=delay_time)
            except InvalidSession as error:
                raise error

            except Exception as error:
                traceback.print_exc()
                logger.error(f"{self.session_name} | Unknown error: {error}")
                await asyncio.sleep(delay=randint(60, 120))




async def run_tapper(tg_client: Client, proxy: str | None):
    try:
        await Tapper(tg_client=tg_client).run(proxy=proxy)
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")
