import asyncio
from datetime import datetime, timezone
from itertools import cycle

import aiohttp
import pytz
from aiocfscrape import CloudflareScraper
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from bot.core.agents import generate_random_user_agent
from bot.config import settings

from bot.utils import logger
from bot.exceptions import InvalidSession
from .headers import headers

from random import randint, uniform
import traceback
import time

# api endpoint
api_endpoint = "https://elb.seeddao.org/"

# api endpoint
api_claim = f'{api_endpoint}api/v1/seed/claim'
api_balance = f'{api_endpoint}api/v1/profile/balance'
api_checkin = f'{api_endpoint}api/v1/login-bonuses'
api_upgrade_storage = f'{api_endpoint}api/v1/seed/storage-size/upgrade'
api_upgrade_mining = f'{api_endpoint}api/v1/seed/mining-speed/upgrade'
api_upgrade_holy = f'{api_endpoint}api/v1/upgrades/holy-water'
api_profile = f'{api_endpoint}api/v1/profile'
api_hunt_completed = f'{api_endpoint}api/v1/bird-hunt/complete'
api_bird_info = f'{api_endpoint}api/v1/bird/is-leader'
api_make_happy = f'{api_endpoint}api/v1/bird-happiness'
api_get_worm_data = f'{api_endpoint}api/v1/worms/me-all'
api_feed = f'{api_endpoint}api/v1/bird-feed'
api_start_hunt = f'{api_endpoint}api/v1/bird-hunt/start'
api_inv = f'{api_endpoint}api/v1/worms/me'
api_sell = f'{api_endpoint}api/v1/market-item/add'
new_user_api = f'{api_endpoint}api/v1/profile2'


class Tapper:
    def __init__(self, Query: str):
        self.session_name = ''
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
        self.auth = Query
        self.total_earned_from_sale = 0
        self.total_on_sale = 0
        self.worm_in_inv = {"common": 0, "uncommon": 0, "rare": 0, "epic": 0, "legendary": 0}
        self.worm_in_inv_copy = {"common": 0, "uncommon": 0, "rare": 0, "epic": 0, "legendary": 0}

    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy) -> None:
        try:
            response = await http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")

    async def setup_profile(self, http_client: aiohttp.ClientSession) -> None:
        response = await http_client.post(url=api_profile)
        if response.status == 200:
            logger.info(f"{self.session_name} | <green>Set up account successfully!</green>")


        else:
            logger.warning(
                f"Can't get account data for session: {self.session_name}. <red>response status: {response.status}</red>")

    async def hatch_egg(self, http_client: aiohttp.ClientSession, egg_id):
        payload = {
            "egg_id": egg_id
        }
        res = await http_client.post('https://elb.seeddao.org/api/v1/egg-hatch/complete', json=payload)
        if res.status == 200:
            json_data = await res.json()
            logger.success(f"{self.session_name} | <cyan>Sucessfully hatched {json_data['data']['type']}!</cyan>")

    async def get_first_egg_and_hatch(self, http_client: aiohttp.ClientSession):
        res = await http_client.post('https://elb.seeddao.org/api/v1/give-first-egg')
        if res.status == 200:
            logger.success(f"{self.session_name} <green>Successfully get first egg!</green>")
            json_egg = await res.json()
            egg_id = str(json_egg['data']['id'])
            await self.hatch_egg(http_client, egg_id)

    async def fetch_profile(self, http_client: aiohttp.ClientSession) -> None:
        response = await http_client.get(url=api_profile)
        if response.status == 200:
            response_json = await response.json()
            self.user_id = response_json['data']['id']
            self.session_name = response_json['data']['name']
            logger.info(
                f"{self.session_name} | <green>Got into seed app - Username: {response_json['data']['name']}</green>")
            if response_json['data']['give_first_egg'] is False:
                await self.get_first_egg_and_hatch(http_client)
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
                logger.info(f"{self.session_name} | <cyan>{upgrade_type.capitalize()} Level: {level + 1}</cyan>")
        else:
            logger.warning(
                f"Can't get account data for session: {self.session_name}. <red>response status: {response.status}</red>")

    async def upgrade_storage(self, http_client: aiohttp.ClientSession) -> None:
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
                logger.info(
                    f"{self.session_name} | Next Worm in {hours} hours {minutes} minutes - Status: {'Caught' if worm_caught else 'Available'}")
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
        response = await http_client.get(f'{api_endpoint}api/v1/tasks/progresses')
        tasks = await response.json()
        for task in tasks['data']:
            if task['task_user'] is None:
                await self.mark_task_complete(task['id'], task['name'], http_client)
            elif task['task_user']['completed'] is False:
                await self.mark_task_complete(task['id'], task['name'], http_client)

    async def mark_task_complete(self, task_id, task_name, http_client: aiohttp.ClientSession):
        response = await http_client.post(f'{api_endpoint}api/v1/tasks/{task_id}')
        if response.status == 200:
            logger.success(f"{self.session_name} | <green>Task {task_name} marked complete.</green>")
        else:
            logger.error(f"{self.session_name} | Failed to complete task {task_name}, status code: {response.status}")

    async def claim_hunt_reward(self, bird_id, http_client: aiohttp.ClientSession):
        payload = {
            "bird_id": bird_id
        }
        response = await http_client.post(api_hunt_completed, json=payload)
        if response.status == 200:
            response_data = await response.json()
            logger.success(
                f"{self.session_name} | <green>Successfully claimed {response_data['data']['seed_amount'] / (10 ** 9)} seed from hunt reward.</green>")
        else:
            response_data = await response.json()
            print(response_data)
            logger.error(f"{self.session_name} | Failed to claim hunt reward, status code: {response.status}")

    async def get_bird_info(self, http_client: aiohttp.ClientSession):
        response = await http_client.get(api_bird_info)
        if response.status == 200:
            response_data = await response.json()
            return response_data['data']
        else:
            response_data = await response.json()
            logger.info(f"{self.session_name} | Get bird data failed: {response_data}")
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
            # print(response_data)
            return response_data['data']
        else:
            return None

    async def feed_bird(self, bird_id, worm_id, http_client: aiohttp.ClientSession):
        payload = {
            "bird_id": bird_id,
            "worm_ids": worm_id
        }
        response = await http_client.post(api_feed, json=payload)
        if response.status == 200:
            logger.success(f"{self.session_name} | <green>Feed bird successfully</green>")
        else:
            response_data = await response.json()
            print(response_data)
            logger.info(f"{self.session_name} | Failed to feed bird, response code:{response.status}")
            return None

    async def start_hunt(self, bird_id, http_client: aiohttp.ClientSession):
        payload = {
            "bird_id": bird_id,
            "task_level": 0
        }
        response = await http_client.post(api_start_hunt, json=payload)
        if response.status == 200:
            logger.success(f"{self.session_name} | <green>Successfully start hunting</green>")
        else:
            print(await response.json())
            logger.error(f"{self.session_name} | Start hunting failed..., response code: {response.status}")

    async def get_worms(self, http_client: aiohttp.ClientSession):
        worms = []
        first_page = await http_client.get(api_inv + "?page=1")
        json_page = await first_page.json()

        for worm in json_page['data']['items']:
            worms.append(worm)
            if worm['on_market'] is False:
                self.worm_in_inv[worm['type']] += 1
        count = 0
        if json_page['data']['total'] % json_page['data']['page_size'] != 0:
            count = 1
        total_page = int(float(json_page['data']['total'] / json_page['data']['page_size'])) + count
        for page in range(2, total_page + 1):
            api_url = api_inv + f"?page={page}"
            page_data = await http_client.get(api_url)
            json_page = await page_data.json()
            for worm in json_page['data']['items']:
                worms.append(worm)
                if worm['on_market'] is False:
                    self.worm_in_inv[worm['type']] += 1
            time.sleep(uniform(1, 2))
        return worms

    async def sell_worm(self, worm_id, price, worm_type, http_client: aiohttp.ClientSession):
        payload = {
            "price": price,
            "worm_id": worm_id
        }
        response = await http_client.post(api_sell, json=payload)
        if response.status == 200:
            self.total_on_sale += 1
            logger.success(
                f"{self.session_name} | <green>Sell {worm_type} worm successfully, price: {price / 1000000000}</green>")
        else:
            response_data = await response.json()
            print(response_data)
            logger.info(f"{self.session_name} | Failed to sell {worm_type} worm, response code:{response.status}")
            return None

    async def get_price(self, worm_type, http_client: aiohttp.ClientSession):
        api = f'{api_endpoint}v1/market/v2?market_type=worm&worm_type={worm_type}&sort_by_price=ASC&sort_by_updated_at=&page=1'
        response = await http_client.get(api)
        if response.status == 200:
            json_r = await response.json()
            return json_r['data']['items'][0]['price_gross']
        else:
            return 0

    async def get_sale_data(self, http_client: aiohttp.ClientSession):
        api = f'{api_endpoint}api/v1/history-log-market/me?market_type=worm&page=1&history_type=sell'
        response = await http_client.get(api)
        json_data = await response.json()
        worm_on_sale = {"common": 0, "uncommon": 0, "rare": 0, "epic": 0, "legendary": 0}
        for worm in json_data['data']['items']:
            if worm['status'] == "on-sale":
                worm_on_sale[worm['worm_type']] += 1
            elif worm['status'] == "bought":
                self.total_earned_from_sale += worm['price_net'] / 1000000000
        count = 0
        if json_data['data']['total'] % json_data['data']['page_size'] != 0:
            count = 1
        total_page = int(float(json_data['data']['total'] / json_data['data']['page_size'])) + count
        for page in range(2, total_page + 1):
            response = await http_client.get(
                f"{api_endpoint}api/v1/history-log-market/me?market_type=worm&page={page}&history_type=sell",
                headers=headers)
            json_data = await response.json()
            for worm in json_data['data']['items']:
                if worm['status'] == "on-sale":
                    worm_on_sale[worm['worm_type']] += 1
                elif worm['status'] == "bought":
                    self.total_earned_from_sale += worm['price_net'] / 1000000000

        return worm_on_sale

    async def check_new_user(self, http_client: aiohttp.ClientSession):
        response = await http_client.get(new_user_api)
        if response.status == 200:
            data_ = await response.json()
            # print(data_)
            return data_['data']['bonus_claimed']

    def refresh_data(self):
        self.total_earned_from_sale = 0
        self.worm_in_inv = self.worm_in_inv_copy

    async def get_streak_rewards(self, http_client: aiohttp.ClientSession):
        res = await http_client.get(f"{api_endpoint}api/v1/streak-reward")
        if res.status == 200:
            data_ = await res.json()
            return data_['data']
        else:
            logger.warning(f"{self.session_name} | <yellow>Failed to get streak rewards</yellow>")
        return None

    async def claim_streak_rewards(self, http_client: aiohttp.ClientSession):
        rewards = await self.get_streak_rewards(http_client)
        pl_rewards = []
        if rewards is None:
            return
        if len(rewards) == 0:
            logger.info(f"{self.session_name} | No ticket to claim.")
            return
        for reward in rewards:
            pl_rewards.append(reward['id'])

        payload = {
            "streak_reward_ids": pl_rewards
        }
        claim = await http_client.post(f"{api_endpoint}api/v1/streak-reward", json=payload)
        if claim.status == 200:
            logger.success(f"{self.session_name} | <green>Successfully claim tickets!</green>")
        else:
            logger.warning(f"{self.session_name} | <yellow>Failed to claim ticket!</yellow>")

    async def get_tickets(self, http_client: aiohttp.ClientSession):
        res = await http_client.get(f"{api_endpoint}api/v1/spin-ticket")
        if res.status == 200:
            data = await res.json()
            return data['data']
        return None

    async def get_egg_pieces(self, http_client: aiohttp.ClientSession):
        res = await http_client.get(f"{api_endpoint}api/v1/egg-piece")
        if res.status == 200:
            data = await res.json()
            return data['data']
        return None

    async def get_fusion_fee(self, type, http_client: aiohttp.ClientSession):
        res = await http_client.get(f"{api_endpoint}api/v1/fusion-seed-fee?type={type}")
        if res.status == 200:
            data = await res.json()
            return data['data']
        return None

    async def spin(self, ticketId, http_client: aiohttp.ClientSession):
        payload = {
            "ticket_id": ticketId
        }

        res = await http_client.post(f"{api_endpoint}api/v1/spin-reward", json=payload)
        if res.status == 200:
            data = await res.json()
            logger.success(f"{self.session_name} | <green>Spinned successfully - Got <cyan>{data['data']['type']}</cyan> egg pieces!</green>")
        else:
            return

    async def fusion(self, egg_ids, type, http_client: aiohttp.ClientSession):
        payload = {
            "egg_piece_ids": egg_ids
        }

        res = await http_client.post(f"{api_endpoint}api/v1/egg-piece-merge", json=payload)
        if res.status == 200:
            logger.success(f"{self.session_name} | <green>Successfully fusion a <cyan>{type}</cyan> egg!</green>")
        else:
            return
    async def play_game(self, http_client: aiohttp.ClientSession):
        egg_type = {
            "common": 0,
            "uncommon": 0,
            "rare": 0,
            "epic": 0,
            "legendary": 0
        }
        egg_pieces = await self.get_egg_pieces(http_client)
        if egg_pieces is None:
            return
        for piece in egg_pieces:
            egg_type[piece['type']] += 1

        info_ = f"""
        Common pieces: <cyan>{egg_type['common']}</cyan>
        Uncommon pieces: <cyan>{egg_type['uncommon']}</cyan>
        rare pieces: <cyan>{egg_type['rare']}</cyan>
        epic pieces: <cyan>{egg_type['epic']}</cyan>
        legendary pieces: <cyan>{egg_type['legendary']}</cyan>
        """

        logger.info(f"{self.session_name} Egg pieces: \n{info_}")

        tickets = await self.get_tickets(http_client)
        if tickets is None:
            return

        logger.info(f"{self.session_name} | Total ticket: <cyan>{len(tickets)}</cyan>")

        play = randint(settings.SPIN_PER_ROUND[0], settings.SPIN_PER_ROUND[1])

        for ticket in tickets:
            if play == 0:
                break
            play -= 1
            await self.spin(ticket['id'], http_client)
            await self.get_tickets(http_client)
            await self.get_egg_pieces(http_client)
            await asyncio.sleep(randint(2,5))

        if settings.AUTO_FUSION:
            # print("stary")
            egg_type = {
                "common": 0,
                "uncommon": 0,
                "rare": 0,
                "epic": 0,
                "legendary": 0
            }
            egg_pieces = await self.get_egg_pieces(http_client)
            if egg_pieces is None:
                return
            for piece in egg_pieces:
                egg_type[piece['type']] += 1

            if egg_type['common'] >= 5:
                fusion_fee = await self.get_fusion_fee('common', http_client)
                # print(fusion_fee)
                if fusion_fee is None:
                    return
                if fusion_fee/1000000000 <= settings.MAXIMUM_PRICE_TO_FUSION_COMMON:
                    pl_data = []
                    for piece in egg_pieces:
                        if len(pl_data) >= 5:
                            break
                        if piece['type'] == 'common':
                            pl_data.append(piece['id'])

                    await self.fusion(pl_data, 'common', http_client)

            if egg_type['uncommon'] >= 5:
                fusion_fee = await self.get_fusion_fee('uncommon', http_client)
                if fusion_fee is None:
                    return
                if fusion_fee/1000000000 <= settings.MAXIMUM_PRICE_TO_FUSION_UNCOMMON:
                    pl_data = []
                    for piece in egg_pieces:
                        if len(pl_data) >= 5:
                            break
                        if piece['type'] == 'uncommon':
                            pl_data.append(piece['id'])

                    await self.fusion(pl_data, 'uncommon', http_client)

            if egg_type['rare'] >= 5:
                fusion_fee = await self.get_fusion_fee('rare', http_client)
                if fusion_fee is None:
                    return
                if fusion_fee/1000000000 <= settings.MAXIMUM_PRICE_TO_FUSION_RARE:
                    pl_data = []
                    for piece in egg_pieces:
                        if len(pl_data) >= 5:
                            break
                        if piece['type'] == 'rare':
                            pl_data.append(piece['id'])

                    await self.fusion(pl_data, 'rare', http_client)

            if egg_type['epic'] >= 5:
                fusion_fee = await self.get_fusion_fee('epic', http_client)
                if fusion_fee is None:
                    return
                if fusion_fee/1000000000 <= settings.MAXIMUM_PRICE_TO_FUSION_EPIC:
                    pl_data = []
                    for piece in egg_pieces:
                        if len(pl_data) >= 5:
                            break
                        if piece['type'] == 'epic':
                            pl_data.append(piece['id'])

                    await self.fusion(pl_data, 'epic', http_client)

            if egg_type['legendary'] >= 5:
                fusion_fee = await self.get_fusion_fee('legendary', http_client)
                if fusion_fee is None:
                    return
                if fusion_fee/1000000000 <= settings.MAXIMUM_PRICE_TO_FUSION_LEGENDARY:
                    pl_data = []
                    for piece in egg_pieces:
                        if len(pl_data) >= 5:
                            break
                        if piece['type'] == 'legendary':
                            pl_data.append(piece['id'])

                    await self.fusion(pl_data, 'legendary', http_client)

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
                    # logger.info(f"{self.session_name} | Update auth token...")
                    tg_web_data = self.auth
                    headers['telegram-data'] = tg_web_data
                    # print(tg_web_data)
                    http_client.headers["telegram-data"] = tg_web_data
                    access_token_created_time = time.time()
                    token_live_time = randint(3500, 3600)
                    await asyncio.sleep(delay=randint(10, 15))

                not_new_user = await self.check_new_user(http_client)

                if not_new_user is False:
                    logger.info(f"{self.session_name} | Setting up new account...")
                    await self.setup_profile(http_client)

                await self.fetch_profile(http_client)

                if settings.AUTO_START_HUNT:
                    bird_data = await self.get_bird_info(http_client)
                    # print(bird_data)
                    if bird_data is None:
                        logger.info(f"{self.session_name} | Can't get bird data...")
                    elif bird_data['owner_id'] != self.user_id:
                        logger.warning(f"{self.session_name} | <yellow>Bird is not your: {bird_data}</yellow>")
                    elif bird_data['status'] == "hunting":

                        try:
                            given_time = datetime.fromisoformat(bird_data['hunt_end_at'])
                            timestamp_naive = given_time.replace(tzinfo=None)
                        except:
                            import dateutil.parser
                            timestamp_naive = dateutil.parser.isoparse(bird_data['hunt_end_at'])
                        now = datetime.now(timezone.utc)

                        # If the parsed timestamp is naive, make it aware in UTC
                        if timestamp_naive.tzinfo is None:
                            timestamp_naive = timestamp_naive.replace(tzinfo=timezone.utc)

                        if now < timestamp_naive:
                            logger.info(f"{self.session_name} | Bird currently hunting...")
                        else:
                            logger.info(f"{self.session_name} | <white>Hunt completed, claiming reward...</white>")
                            await self.claim_hunt_reward(bird_data['id'], http_client)
                    else:
                        condition = True
                        if bird_data['happiness_level'] == 0:
                            logger.info(f"{self.session_name} | Bird is not happy, attemping to make bird happy...")
                            check = await self.make_bird_happy(bird_data['id'], http_client)
                            if check:
                                logger.success(f"{self.session_name} | <green>Successfully make bird happy!</green>")
                            else:
                                logger.info(f"{self.session_name} |Failed to make bird happy!")
                                condition = False
                        if bird_data['energy_level'] == 0:
                            logger.info(f"{self.session_name} | Bird is hungry, attemping to feed bird...")
                            worms = await self.get_worm_data(http_client)
                            if worms is None:
                                condition = False
                                logger.info(f"{self.session_name} | Failed to fetch worm data")
                            elif len(worms) == 0:
                                logger.warning(f"{self.session_name} | You dont have any worm to feed bird!")
                                condition = False
                            else:
                                try:
                                    energy = (bird_data['energy_max'] - bird_data['energy_level']) / 1000000000
                                except:
                                    print(bird_data)
                                    energy = 2
                                wormss = []
                                for worm in worms:
                                    if worm['type'] == "common" and worm['on_market'] is False:
                                        wormss.append(worm['id'])
                                        energy -= 2
                                        if energy <= 1:
                                            break
                                if energy > 1:
                                    for worm in worms:
                                        if worm['type'] == "uncommon" and worm['on_market'] is False:
                                            wormss.append(worm['id'])
                                            energy -= 4
                                            if energy <= 1:
                                                break
                                await self.feed_bird(bird_data['id'], wormss, http_client)
                                if energy > 1:
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
                        logger.success(f"{self.session_name} | <green> Claim successful </green>")
                    elif response.status == 400:
                        logger.info(f"{self.session_name} | Not yet time to claim")
                    else:
                        logger.error(
                            f"{self.session_name} | <red>An error occurred, status code: {response.status}</red>")

                    await self.perform_daily_checkin(http_client)
                    await self.capture_worm(http_client)
                if settings.AUTO_SELL_WORMS:
                    logger.info(f"{self.session_name} | Fetching worms data to put it on sale...")
                    worms = await self.get_worms(http_client)
                    # print(self.worm_in_inv)
                    worms_on_sell = await self.get_sale_data(http_client)
                    logger.info(f"{self.session_name} | Worms on sale now: ")
                    for worm in worms_on_sell:
                        logger.info(
                            f"{self.session_name} | Total <cyan>{worm}</cyan> on sale: <yellow>{worms_on_sell[worm]}</yellow>")
                    logger.info(
                        f"{self.session_name} | Total earned from sale: <yellow>{self.total_earned_from_sale}</yellow>")
                    for worm in worms:
                        if worm['on_market']:
                            continue
                        elif settings.QUANTITY_TO_KEEP[worm['type']]['quantity_to_keep'] == -1:
                            continue
                        elif settings.QUANTITY_TO_KEEP[worm['type']]['quantity_to_keep'] < self.worm_in_inv[
                            worm['type']]:
                            if settings.QUANTITY_TO_KEEP[worm['type']]['sale_price'] == 0:
                                price_to_sell = await self.get_price(worm['type'], http_client)

                            else:
                                price_to_sell = settings.QUANTITY_TO_KEEP[worm['type']]['sale_price'] * (10 ** 9)
                            # print(f"Sell {worm['type']} , price: {price_to_sell/1000000000}")
                            await self.sell_worm(worm['id'], price_to_sell, worm['type'], http_client)
                            self.worm_in_inv[worm['type']] -= 1

                    self.refresh_data()
                if settings.AUTO_CLEAR_TASKS:
                    await self.fetch_tasks(http_client)

                if settings.AUTO_SPIN:
                    await self.claim_streak_rewards(http_client)
                    await asyncio.sleep(randint(1,4))
                    await self.play_game(http_client)

                delay_time = randint(2800, 3600)
                logger.info(f"{self.session_name} | Completed {self.session_name}, waiting {delay_time} seconds...")
                await asyncio.sleep(delay=delay_time)
            except InvalidSession as error:
                raise error

            except Exception as error:
                traceback.print_exc()
                logger.error(f"{self.session_name} | Unknown error: {error}")
                await asyncio.sleep(delay=randint(60, 120))


async def run_tapper_query(query_list: list[str], proxies: list[str]):
    while 1:
        proxies_cycle = cycle(proxies) if proxies else None
        for query in query_list:
            await Tapper(Query=query).run(proxy=next(proxies_cycle) if proxies_cycle else None)
            await asyncio.sleep(randint(3,5))
        sleep_ = randint(2500, 3600)
        logger.info(f"<red>Sleep {sleep_}s...</red>")
        await asyncio.sleep(sleep_)
