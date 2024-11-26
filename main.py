from get_products import get_products
from promo_processor import PromoProcessor
import pandas as pd
import asyncio
import json
from utils import reformat_data
from datetime import datetime
from get_coupons import map_coupen

async def main():
    csv_file = await get_products(process=True)
    
    df = pd.read_csv(csv_file)
    dfcoupens = map_coupen(df,'81','60031')

    data = pd.DataFrame(dfcoupens)
    data.fillna('', inplace=True)
    data = data.to_dict(orient='records')
    
    processed_data = PromoProcessor.process_item(reformat_data(data))
    new_file_json = f"jewelesco_processed_{datetime.now().strftime('%Y-%m-%d')}.json"
    
    with open(new_file_json, 'w') as f:
        data = processed_data.results
        for item in data:
            if not item["weight"] or item["weight"] == 0.0:
                item["weight"] = ""
        # data = [i for i in data if i.get("volume_deals_description") or i.get("digital_coupon_description")]
        json.dump(data, f, indent=4)
        
 
if __name__ == "__main__":
    asyncio.run(main())
    
    