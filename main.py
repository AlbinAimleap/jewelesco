from get_products import get_products
from promo_processor import PromoProcessor
import pandas as pd
import asyncio
from typing import Dict, Any
import json
from utils import reformat_data
from datetime import datetime



async def main():
    csv_file = await get_products(process=True)
    
    data = pd.read_csv(csv_file).to_dict(orient='records')

    data = pd.DataFrame(data)
    data.fillna('', inplace=True)
    data = data.to_dict(orient='records')
    processed_data = PromoProcessor.process_item(reformat_data(data))
    
    
    new_file_csv = f"jewelesco_{datetime.now().strftime('%Y-%m-%d')}.csv"
    new_file_json = f"jewelesco_processed_{datetime.now().strftime('%Y-%m-%d')}.json"
    
    with open(new_file_json, 'w') as f:
        data = processed_data.results
        
        for item in data:
            item["digital_coupon_description"] = item["digital_coupon_short_description"]
            if not item["weight"] or item["weight"] == 0.0:
                item["weight"] = ""
            del item["digital_coupon_short_description"]
        data = [i for i in data if i.get("volume_deals_description") or i.get("digital_coupon_description")]
        json.dump(data, f, indent=4)
    
    # promo_processor.to_json(new_file_json)
    # promo_processor.to_csv(new_file_csv)
    
    

 
if __name__ == "__main__":
    asyncio.run(main())
    
    