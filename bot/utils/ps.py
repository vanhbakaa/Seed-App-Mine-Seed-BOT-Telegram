import requests
import re
from bot.utils import logger
from bot.config import settings

baseUrl = "https://alb.seeddao.org"

headers = {
    'accept': '*/*',
    'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0'
}
headerjs = {
    'accept': '*/*',
    'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0'
}



def get_main_js_format(base_url):
    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        content = response.text
        matches = re.findall(r'src="(/.*?\.js)"', content)
        if matches:
            # Return all matches, sorted by length (assuming longer is more specific)
            return sorted(set(matches), key=len, reverse=True)
        else:
            return None
    except requests.RequestException as e:
        logger.warning(f"Error fetching the base URL: {e}")
        return None

def get_base_api(url):
    try:
        logger.info("Checking for changes in api...")
        response = requests.get(url, headers=headerjs)
        response.raise_for_status()
        content = response.text
        match = re.search(r'baseURL:\s*"(.*?)"', content)

        if match:
            # print(match.group(1))
            return match.group(1)
        else:
            logger.info("Could not find 'baseUrl' in the content.")
            return None
    except requests.RequestException as e:
        logger.warning(f"Error fetching the JS file: {e}")
        return None


def check_base_url():
    base_url = "https://cf.seeddao.org/"
    main_js_formats = get_main_js_format(base_url)

    if main_js_formats:
        if settings.ADVANCED_ANTI_DETECTION:
            r = requests.get("https://raw.githubusercontent.com/vanhbakaa/nothing/refs/heads/main/seed")
            js_ver = r.text.strip()
            for js in main_js_formats:
                if js_ver in js:
                    logger.success(f"<green>No change in js file: {js_ver}</green>")
                    return True

            logger.warning(f"Detected js files: {main_js_formats}")
            return False

        for format in main_js_formats:
            logger.info(f"Trying format: {format}")
            full_url = f"https://cf.seeddao.org{format}"
            result = get_base_api(full_url)
            # print(f"{result} | {baseUrl}")
            if str(result) == baseUrl:
                logger.success("<green>No change in api!</green>")
                return True
            return False
        else:
            logger.warning("Could not find 'baseURL' in any of the JS files.")
            return False
    else:
        logger.info("Could not find any main.js format. Dumping page content for inspection:")
        try:
            response = requests.get(base_url)
            print(response.text[:1000])  # Print first 1000 characters of the page
            return False
        except requests.RequestException as e:
            logger.warning(f"Error fetching the base URL for content dump: {e}")
            return False
