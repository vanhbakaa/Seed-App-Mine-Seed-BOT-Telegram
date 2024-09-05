import asyncio
from datetime import datetime
from time import time
from urllib.parse import unquote, quote

import aiohttp
import pytz
from aiocfscrape import CloudflareScraper
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw import functions
from pyrogram.raw.functions.messages import RequestWebView
from bot.core.agents import generate_random_user_agent
from bot.config import settings

from bot.utils import logger
from bot.exceptions import InvalidSession
from .headers import headers

from random import randint, uniform
import traceback


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



class Tapper:
    def __init__(self, tg_client: Client):
        self.tg_client = tg_client
        self.session_name = tg_client.name
        self.first_name = ''
        self.last_name = ''
        self.user_id = ''
        self.Total_Point_Earned = 0
        self.Total_Game_Played = 0


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

            web_view = await self.tg_client.invoke(RequestWebView(
                peer=peer,
                bot=peer,
                platform='android',
                from_bot_menu=False,
                url="https://cf.seeddao.org/",
            ))

            auth_url = web_view.url
            tg_web_data = unquote(
                string=unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]))

            self.user_id = tg_web_data.split('"id":')[1].split(',"first_name"')[0]
            self.first_name = tg_web_data.split('"first_name":"')[1].split('","last_name"')[0]
            self.last_name = tg_web_data.split('"last_name":"')[1].split('","username"')[0]

            if self.tg_client.is_connected:
                await self.tg_client.disconnect()

            return unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])

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
            logger.info(f"<green>Got into seed app - Username: {response_json['data']['name']}</green>")
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
                logger.info(f"<cyan>{upgrade_type.capitalize()} Level: {level+1}</cyan>")
        else:
            logger.warning(f"Can't get account data for session: {self.session_name}. <red>response status: {response.status}</red>")

    async def upgrade_storage(self,http_client: aiohttp.ClientSession) -> None:
        response = await http_client.post(url=api_upgrade_storage)
        if response.status == 200:
            logger.success(f"<yellow>Upgrade Storage Successfully</yellow>")
        else:
            logger.info(f"Upgrade Storage Failed: Insufficient balance")

    async def upgrade_mining(self, http_client: aiohttp.ClientSession) -> None:
        response = await http_client.post(url=api_upgrade_mining)
        if response.status == 200:
            logger.success(f"<yellow>Upgrade Mining Successfully</yellow>")
        else:
            logger.info(f"Upgrade Mining Failed: Insufficient balance")

    async def upgrade_holy(self, http_client: aiohttp.ClientSession) -> None:
        response = await http_client.post(url=api_upgrade_holy)
        if response.status == 200:
            logger.success(f"<yellow>Upgrade Holy Successfully</yellow>")
        else:
            logger.info(f"Upgrade Holy Failed: Requirements not met")

    async def verify_balance(self, http_client: aiohttp.ClientSession):
        response = await http_client.get(url=api_balance)
        if response.status == 200:
            balance_info = await response.json()
            logger.info(f"<cyan>Balance: {balance_info['data'] / 1000000000}</cyan>")
            return True
        else:
            logger.error(f"<red>Balance: Error | {response.status}</red>")

    async def perform_daily_checkin(self, http_client: aiohttp.ClientSession):
        response = await http_client.post(api_checkin)
        if response.status == 200:
            checkin_data = await response.json()
            day = checkin_data.get('data', {}).get('no', '')
            logger.success(f"<green>Successfully checked in | Day {day}</green>")
        else:
            checkin_data = await response.json()
            if checkin_data.get('message') == 'already claimed for today':
                logger.info("Already checked in today")
            else:
                logger.info(f"Failed | {checkin_data}")

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
                logger.info(f"Next Worm in {hours} hours {minutes} minutes - Status: {'Caught' if worm_caught else 'Available'}")
            else:
                logger.info("'next_worm' data not available.")
            return worm_info['data']
        else:
            logger.error("Error retrieving worm data.")
            return None

    async def capture_worm(self, http_client: aiohttp.ClientSession):
        worm_info = await self.fetch_worm_status(http_client)
        if worm_info and not worm_info.get('is_caught', True):
            response = await http_client.post('https://elb.seeddao.org/api/v1/worms/catch')
            if response.status == 200:
                logger.success(f"<green>Worm Captured Successfully</green>")
            elif response.status == 400:
                logger.info("Already captured")
            elif response.status == 404:
                logger.info("Worm not found")
            else:
                logger.error(f"<red>Capture failed, status code: {response.status}</red>")
        else:
            logger.info("Worm unavailable or already captured.")


    async def fetch_tasks(self, http_client: aiohttp.ClientSession):
        response = await http_client.get('https://elb.seeddao.org/api/v1/tasks/progresses')
        tasks = await response.json()
        for task in tasks['data']:
            if task['task_user'] is None or not task['task_user']['completed']:
                await self.mark_task_complete(task['id'], task['name'], http_client)

    async def mark_task_complete(self, task_id, task_name, http_client: aiohttp.ClientSession):
        response = await http_client.post(f'https://elb.seeddao.org/api/v1/tasks/{task_id}')
        if response.status == 200:
            logger.success(f"<green>Task {task_name} marked complete.</green>")
        else:
            logger.error(f"Failed to complete task {task_name}, status code: {response.status}")

    async def claim_hunt_reward(self, bird_id,  http_client: aiohttp.ClientSession):
        payload = {
            "bird_id": bird_id
        }
        response = await http_client.post(api_hunt_completed, json=payload)
        if response.status == 200:
            response_data = await response.json()
            logger.success(f"<green>Successfully claimed {response_data['data']['seed_amount']/(10**9)} seed from hunt reward.</green>")
        else:
            logger.error(f"Failed to claim hunt reward, status code: {response.status}")

    async def get_bird_info(self,  http_client: aiohttp.ClientSession):
        response = await http_client.get(api_bird_info)
        if response.status == 200:
            response_data = await response.json()
            return response_data['data']
        else:
            return None

    async def make_bird_happy(self, bird_id, http_client: aiohttp.ClientSession):
        payload = {
            "bird_id": bird_id,
            "happiness_rate": 10000
        }
        response = await http_client.post(api_make_happy, json=payload)
        if response.status == 200:
            return True
        else:
            return False

    async def get_worm_data(self, http_client: aiohttp.ClientSession):
        response = await http_client.get(api_get_worm_data)
        if response.status == 200:
            response_data = await response.json()
            return response_data['data']
        else:
            return None

    async def feed_bird(self,bird_id, worm_id, http_client: aiohttp.ClientSession):
        payload = {
            "bird_id": bird_id,
            "worm_ids": worm_id
        }
        response = await http_client.post(api_feed, json = payload)
        if response.status == 200:
            response_data = await response.json()
            return response_data['energy_max'] - response_data['energy_level']
        else:
            return None

    async def start_hunt(self, bird_id, http_client: aiohttp.ClientSession):
        payload = {
            "bird_id": bird_id,
            "task_level": 0
        }
        response = await http_client.post(api_start_hunt, json=payload)
        if response.status == 200:
            logger.success("Successfully start hunting")
        else:
            logger.error(f"Start hunting failed..., response code: {response.status}")

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
                if time() - access_token_created_time >= token_live_time:
                    logger.info("Update auth token...")
                    tg_web_data = await self.get_tg_web_data(proxy=proxy)
                    # print(tg_web_data)
                    http_client.headers["telegram-data"] = tg_web_data
                    access_token_created_time = time()
                    token_live_time = randint(3500, 3600)
                    await asyncio.sleep(delay=randint(10, 15))
                logger.info(f"Session {self.first_name} {self.last_name} logged in.")
                await self.fetch_profile(http_client)

                if settings.AUTO_START_HUNT:
                    bird_data = await self.get_bird_info(http_client)
                    if bird_data is None:
                        logger.info("Can't get bird data...")
                    elif bird_data['status'] == "hunting":
                        logger.info("Bird currently hunting...")
                    else:
                        condition = True
                        if bird_data['happiness_level'] == 0:
                            logger.info("Bird is not happy, attemping to make bird happy...")
                            check = await self.make_bird_happy(bird_data['id'], http_client)
                            if check:
                                logger.success(f"Successfully make bird happy!")
                            else:
                                logger.info("Failed to make bird happy!")
                                condition = False
                        if bird_data['energy_level'] == 0:
                            logger.info("Bird is hungry, attemping to feed bird...")
                            worms = await self.get_worm_data(http_client)
                            if worms is None:
                                condition = False
                            elif len(worms) == 0:
                                condition = False
                            else:
                                energy = bird_data['energy_max']
                                for worm in worms:
                                    if worm['type'] == "common":
                                        wormss = [worm['id']]
                                        energy = await self.feed_bird(bird_data['id'], wormss, http_client)
                                        if energy <= 1000000000:
                                            break
                                if energy > 1000000000:
                                    for worm in worms:
                                        if worm['type'] == "uncommon":
                                            wormss = [worm['id']]
                                            energy = await self.feed_bird(bird_data['id'], wormss, http_client)
                                            if energy <= 1000000000:
                                                break
                                if energy > 1000000000:
                                    condition = False

                        if condition:
                            await self.start_hunt(bird_data['id'], http_client)

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
                        logger.success(f"<green> Claim successful </green>")
                    elif response.status == 400:
                        logger.info(f"Not yet time to claim")
                    else:
                        logger.error(f"<red>An error occurred, status code: {response.status}</red>")

                    await self.perform_daily_checkin(http_client)
                    await self.capture_worm(http_client)
                    if settings.AUTO_CLEAR_TASKS:
                        await self.fetch_tasks(http_client)

                delay_time = randint(3400, 3600)
                logger.info(f"============ Completed {self.session_name}, waiting {delay_time} seconds... ============")
                await asyncio.sleep(delay=delay_time)
            except InvalidSession as error:
                raise error

            except Exception as error:
                # traceback.print_exc()
                logger.error(f"{self.session_name} | Unknown error: {error}")
                await asyncio.sleep(delay=randint(60, 120))




async def run_tapper(tg_client: Client, proxy: str | None):
    try:
        await Tapper(tg_client=tg_client).run(proxy=proxy)
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")
