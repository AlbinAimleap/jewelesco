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
import requests

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
        "digital_coupon_description": "",
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

async def get_coupen():
    df = pd.DataFrame({'offerid':[],'description':[],'upc':[]})

    url = "https://www.jewelosco.com/abs/pub/xapi/p13n/deals"

    payload = json.dumps({
    "modelConfigurationId": "65b7f4d7371fb513f19110d5",
    "assortmentChannel": "instore",
    "banner": "jewelosco",
    "storeId": "81",
    "householdId": "",
    "uiPageSize": 22,
    "zipCode": "60031",
    "host": "https://www.jewelosco.com",
    "platform": "web"
    })
    headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/vnd.safeway.v2+json',
    'cookie': '__pdst=b590c63597ab4e06bf7731188b524753; _tt_enable_cookie=1; OptanonAlertBoxClosed=2024-11-07T04:32:28.616Z; visid_incap_1990338=C+snfIAbTUiSZeGxXTzlcq7XFWcAAAAAQkIPAAAAAACAUTS4AS1zWQpECBCoO4vWR0yBElXyMt7o; akacd_PR-bg-www-prod-jewelosco=3908754549~rv=28~id=64db578bc17919bc30a68d21317ddfc5; ACI_S_ECommBanner=jewelosco; ACI_S_ECommSignInCount=0; nlbi_1990338=2Aq4eDTr/woK+BaZzoaznQAAAADKJqvA43cwwhNd8yAiRLkw; reese84=3:c1eIc1o5znkrM5ayUqjrVw==:A/ZF9tIH8eTIlWz9Cz8pW4sN1e5T6SGMZ/zgjjpCf/a9J7nRfZKjj92d7Bcjo05OK4vtnPhUOSU4bH5oGzAPGZdL5VWYO4PseBeo2BN/D4c7tJqOucIUle5sXjK/tBuSt+bOmPPfu2j9kNnc68CJd5TpS99DeSUoHtIrza6swATpvdFYgHz3fOyLTSsXnwrcme4pLzb0X0g6zyXd3YOJYEJiZRa0JWcAkgPDOEpTZqhg2J/xvjBiRl4jzcZr/jCjLE2WYcbu4h1GRfLxBXUcVCFrQkaO3Nl4lDoP8LqV1oD/MtD0BrqZX7EMbpknFGX0CCzv7EZC4aZ7Bvdb7NSSlMsd0GSCFtefrW1GXT+vHk8RRnmVM96IwneKmJlhkhwLTirkKgeeFw7uDmAWiEmhGiFVR2/FfyQsGIhxCApCKOVxu3wRP+WDPoSndcJqdSYGo9JLbvK4FGInfAtDnnm/UDJkN1QRVMGeb1vj593VauJ4WwMdTQeJVyTIxgt/8xx1rMLw8piG4b5PCilLsX2Z6cmMojBVTL/cVZU1+fyzwoM=:9zpuxQxfjXWd66+goU6CWCjeWQ8uQhnIkQPdY/ljENo=; _fbp=fb.1.1732021062555.433774354662959346; incap_ses_738_1990338=XSbrPWA5oEcndNadRec9CkaLPGcAAAAA9Ts5WOcNFHSM3GYKJf7/eQ==; AMCVS_A7BF3BC75245ADF20A490D4D%40AdobeOrg=1; AMCV_A7BF3BC75245ADF20A490D4D%40AdobeOrg=179643557%7CMCIDTS%7C20047%7CMCMID%7C17672570347864736784304271336750436805%7CMCAAMLH-1732625863%7C12%7CMCAAMB-1732625863%7C6G1ynYcLPuiQxYZrsz_pkqfLG9yMXBpb2zX5dvJdYQJzPXImdj0y%7CMCOPTOUT-1732028263s%7CNONE%7CvVersion%7C5.5.0; at_check=true; SAFEWAY_MODAL_LINK=; s_ivc=true; _gcl_au=1.1.2084205062.1732021068; absVisitorId=0fbc7ef0-7704-4323-8dac-55a35113d7b5; _pin_unauth=dWlkPU5qWTFOV0UwWTJZdFpEQXlZeTAwTVRNMUxUbGlNMll0WVRsaE5EY3dOVFF5TlRRMA; __gads=ID=d244d3fe12a79f26:T=1732021382:RT=1732021382:S=ALNI_MYPhHjRLOtT5zVg-MUI9vyyKqiCRg; __gpi=UID=00000f6e5a2a6616:T=1732021382:RT=1732021382:S=ALNI_MYui6kGx4ZsH2iIg5opjH7UW7Cpyg; __eoi=ID=1200a7c23b17ae3c:T=1729484722:RT=1732021382:S=AA-AfjbuGxBNbyzi9r6fEOtyDPVV; abs_gsession=%7B%22info%22%3A%7B%22COMMON%22%3A%7B%22preference%22%3A%22J4U%22%2C%22Selection%22%3A%22user%22%2C%22zipcode%22%3A%2260657%22%2C%22resolvedBy%22%3A%22zipcode%22%7D%2C%22J4U%22%3A%7B%22storeId%22%3A%223514%22%2C%22zipcode%22%3A%2260657%22%7D%2C%22SHOP%22%3A%7B%22storeId%22%3A%223514%22%2C%22zipcode%22%3A%2260657%22%7D%7D%7D; ACI_S_abs_previouslogin=%7B%22info%22%3A%7B%22COMMON%22%3A%7B%22preference%22%3A%22J4U%22%2C%22Selection%22%3A%22user%22%2C%22zipcode%22%3A%2260657%22%2C%22resolvedBy%22%3A%22zipcode%22%7D%2C%22J4U%22%3A%7B%22storeId%22%3A%223514%22%2C%22zipcode%22%3A%2260657%22%7D%2C%22SHOP%22%3A%7B%22storeId%22%3A%223514%22%2C%22zipcode%22%3A%2260657%22%7D%7D%7D; SWY_SHARED_SESSION_INFO=%7B%22info%22%3A%7B%22COMMON%22%3A%7B%22userType%22%3A%22G%22%2C%22zipcode%22%3A%2260657%22%2C%22banner%22%3A%22jewelosco%22%2C%22preference%22%3A%22J4U%22%2C%22Selection%22%3A%22user%22%2C%22userData%22%3A%7B%7D%2C%22grsSessionId%22%3A%22cbfccdc8-255c-4c84-a295-c57e976072b8%22%2C%22siteType%22%3A%22C%22%2C%22customerType%22%3A%22%22%2C%22resolvedBy%22%3A%22zipcode%22%7D%2C%22J4U%22%3A%7B%22storeId%22%3A%223514%22%2C%22zipcode%22%3A%2260657%22%2C%22userData%22%3A%7B%7D%7D%2C%22SHOP%22%3A%7B%22storeId%22%3A%223514%22%2C%22zipcode%22%3A%2260657%22%2C%22userData%22%3A%7B%7D%7D%7D%7D; SWY_SYND_USER_INFO=%7B%22storeAddress%22%3A%22%22%2C%22storeZip%22%3A%2260657%22%2C%22storeId%22%3A%223514%22%2C%22preference%22%3A%22J4U%22%7D; ACI_S_ECommRedirectURL=https%3A%2F%2Fwww.jewelosco.com%2Fforu%2Fcoupons-deals.html%3Fevent%3DThanksgiving%2520Deals; s_sq=%5B%5BB%5D%5D; OptanonConsent=isGpcEnabled=0&datestamp=Tue+Nov+19+2024+18%3A33%3A57+GMT%2B0530+(India+Standard+Time)&version=202409.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=44753b0d-71fd-4ef8-8da8-6d08ddc798f6&interactionCount=2&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0004%3A1%2CC0003%3A1&intType=1&geolocation=IN%3BGJ&AwaitingReconsent=false; _uetvid=7ceefad08f6411efab29577cfb41e7e1; gpv_Page=jewelosco%3Aloyalty%3Ahome; nlbi_1990338_2147483392=CE0XAzRGhHshuS9vzoaznQAAAABBefCVAAR8DRgjS4sbibSi; _ga_8KFH5XL9VW=GS1.1.1732021437.1.0.1732021452.0.0.0; mbox=session#55cfd5b61cca4c45a130f15e29b916bb#1732023314|PC#55cfd5b61cca4c45a130f15e29b916bb.41_0#1795266254; abc=abc; incap_ses_885_1990338=xmQPDOMLly7B9uPrCSdIDCqmPGcAAAAAXaGZ67EWvsypywthpt85OQ==; nlbi_1990338=zwpNcZxaFlAScstKzoaznQAAAAAkEvZ2TFSgrr1bmpRAUPqG; visid_incap_1990338=C+snfIAbTUiSZeGxXTzlcq7XFWcAAAAAQ0IPAAAAAABrZwgVzaG08GOczLfv4BRm',
    'ocp-apim-subscription-key': '7bad9afbb87043b28519c4443106db06',
    'origin': 'https://www.jewelosco.com',
    'platform': 'web',
    'priority': 'u=1, i',
    'referer': 'https://www.jewelosco.com/',
    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    data = response.json()
    for coupen in data['coupons']:
        url = f"https://www.jewelosco.com/abs/pub/xapi/offers?offerId={coupen}&includeUpc=y"

        payload = {}
        headers = {
        'Cookie': 'abc=abc; incap_ses_885_1990338=ld5dXocp+wsJ+u7rCSdIDIquPGcAAAAA80XEYI5t3QMC5UnPIjaOqA==; nlbi_1990338=QjQRMFhW/CwCNu7czoaznQAAAABa5O3rJjGu46JwMG43u684; visid_incap_1990338=C+snfIAbTUiSZeGxXTzlcq7XFWcAAAAAQ0IPAAAAAABrZwgVzaG08GOczLfv4BRm'
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        data = response.json()
        description = data['offerDetail']['description']
        upcList = data['upcList']
        #datajs = {
        #    "offerid":coupen,
        #    "description":description,
        #    "upc":upcList
        #}
        df = df._append({'offerid':coupen,'description':description,'upc':upcList},ignore_index=True)
    #df.to_csv('coupens.csv')
    return df['upc'],df['description']
