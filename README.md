
# Jewel-Osco Product Scraper

This Python script scrapes product information from the Jewel-Osco website and saves it to a CSV file.

## Features

- Asynchronous web scraping using `aiohttp` and `asyncio`
- Processes multiple product categories concurrently
- Saves data to CSV file in real-time
- Handles product promotions and digital coupons
- Logs progress and errors

## Requirements

- Python 3.7+
- pandas
- aiohttp
- asyncio
- BeautifulSoup4
- scrapy
- logging

## Usage

1. Ensure you have all required libraries installed:

   ```bash
   pip install -r requirements.txt
   ```

2. Place the `Category_links_new.xlsx` file in the same directory as the script.

3. Run the script:

   ```bash
   python main.py
   ```

4. The script will create a CSV file named `Jewelsco_sample_YYYY-MM-DD.csv` in the same directory, where YYYY-MM-DD is the current date.

## Configuration

- Modify the `Config.HEADERS` in `config.py` to change the request headers if needed.
- Adjust the `zipcode`, `store_name`, and `store_location` in the `process_product` function if you want to scrape data for a different store.
