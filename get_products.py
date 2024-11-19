import json
import random
import time
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from scrapy import Selector
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_utc_time_stamp_random():
    random_part_1 = str(random.randint(100, 999))
    current_time = str(int(time.time() * 1000))
    random_part_2 = str(random.randint(100, 999))
    return random_part_1 + current_time + random_part_2

async def get_product_response(session, cat, start):
    url = f'https://www.jewelosco.com/abs/pub/xapi/pgmsearch/v1/search/products'
    params = {
        'request-id': get_utc_time_stamp_random(),
        'url': 'https://www.jewelosco.com',
        'pageurl': 'https://www.jewelosco.com',
        'pagename': 'search',
        'rows': '30',
        'start': start,
        'search-type': 'keyword',
        'storeid': '81',
        'featured': 'true',
        'q': cat,
        'sort': '',
        'dvid': 'web-4.1search',
        'channel': 'instore',
        'pp': 'true',
        'visitorId': '69523c47-8519-4aee-971d-6c74b9f377b6',
        'uuid': '9c3332bb-f293-475b-91e2-f875757ca50b',
        'pgm': 'intg-search',
        'banner': 'jewelosco',
        'variantSponsored': 'ACIP108365_c'
    }
    async with session.get(url, params=params, headers=Config.HEADERS) as response:
        return await response.json()

def trim_and_pad(number):
    if number:
        number = int(number)
        trimmed_number = str(number)
        zeros_to_add = 13 - len(trimmed_number)
        return '0' * zeros_to_add + trimmed_number
    return None

def process_product(pr, formatted_today):
    upc = trim_and_pad(pr.get("upc", '').strip())
        
    product_data = {
        "zipcode": "60031",
        "store_name": "Jewel-Osco Grand & Hunt Club Rd",
        "store_location": "6509 W Grand Avenue, Gurnee, IL 60031",
        "store_logo": "https://www.jewelosco.com/content/dam/safeway/images/logos/JewelOsco_Vert_Oval_RGB.svg",
        "category": pr.get("departmentName", '').strip(),
        "sub_category": pr.get("aisleName", "").split("|")[0].strip() if pr.get("aisleName", "") else '',
        "product_title": pr.get("name", '').strip(),
        "weight": str(pr.get("averageWeight", [])[0]).strip() if pr.get("averageWeight", []) else 1,
        "regular_price": str(pr.get("basePrice", '')).strip(),
        "sale_price": str(pr.get("price", '')).strip() if str(pr.get("basePrice", '')).strip() != str(pr.get("price", '')).strip() else '',
        "volume_deals_description": pr.get("promoDescription", '').strip() or pr.get("promoText", '').strip(),
        "volume_deals_price": "",
        "digital_coupon_short_description": "",
        "digital_coupon_price": "",
        "unit_price": "",
        "image_url": f"https://images.albertsons-media.com/is/image/ABS/{pr['pid']}?$ng-ecom-pdp-desktop$&defaultImage=Not_Available",
        "url": f"https://www.jewelosco.com/shop/product-details.{pr['pid']}.html",
        "upc": upc,
        "crawl_date": formatted_today
    }
    return product_data
    

async def process_category(session, cat, formatted_today, csv_file):
    start = 0
    processed_items = list()
    while True:
        response_json = await get_product_response(session, cat, start)
        try:
            products = response_json['primaryProducts']['response']['docs']
        except Exception as e:
            logger.error(f"Error processing category {cat}: {e}")
            break
            

        for pr in products:
            try:
                data = process_product(pr, formatted_today)
                if data not in processed_items:
                    
                    pd.DataFrame([data]).to_csv(csv_file, mode='a', header=not csv_file.exists(), index=False)
                    processed_items.append(data)
            except Exception as e:
                logger.error(f"Error processing product in category {cat}: {e}")

        logger.info(f'Category: {cat}, Processed UPCs: {len(processed_items)}')

        start += 30
        if len(products) < 30:
            break

async def get_products(process=True):
    cur_dir = Path(__file__).parent
    df_cat = pd.read_excel(cur_dir / 'Category_links_new.xlsx')
    cat_links = list(df_cat['links'])
    cat_query = list(set([cat.split('/')[-2] for cat in cat_links]))

    today = datetime.today().date()
    formatted_today = today.strftime('%Y-%m-%d')

    csv_file = Path(f'Jewelsco_sample_{formatted_today}.csv')
    
    if process:
        if csv_file.exists():
            csv_file.unlink()

        logger.info("Starting data collection process")

        async with aiohttp.ClientSession() as session:
            tasks = [process_category(session, cat, formatted_today, csv_file) for cat in cat_query]
            await asyncio.gather(*tasks)

        logger.info(f"CSV file saved: {csv_file}")
        logger.info("Data collection process completed")
    return csv_file

