import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-notifications")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def navigate_to_channel(channel_url):
    driver.get(channel_url)
    print("Navigated to channel. Please log in if prompted.")
    time.sleep(5)  

def scroll_to_load():
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)  

def save_messages_to_json(messages): # saved to messages.json file concurrently, located in same directory as DiscordScraper.py
    with open("messages.json", "w") as f:
        json.dump(messages, f, indent=4)

def track_and_save_messages():
    previous_messages = set()
    all_messages = []

    while True:
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "messageContent_f9f2ca"))
            )

            messages = driver.find_elements(By.CLASS_NAME, "messageContent_f9f2ca")
            for msg in messages:
                msg_text = msg.text.strip()
                if msg_text not in previous_messages:
                    previous_messages.add(msg_text)
                    all_messages.append({"text": msg_text, "timestamp": time.time()}) # time stamp saved in unix form

            save_messages_to_json(all_messages)
            scroll_to_load()
            time.sleep(2)

        except Exception as e:
            print(f"Error tracking messages, retrying: {e}")
            time.sleep(5)


def fetch_cpi_data(): # fetches table data from CPI prints site, stores in json file 
    try:
        driver.get("https://www.bls.gov/cpi/latest-numbers.htm")
        print("Navigated to the main CPI page.")
        time.sleep(3)

        print("Attempting to locate CPI groups on the main page...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "ln-group"))
        )
        print("Successfully located CPI groups on the main page.")

        groups = driver.find_elements(By.CLASS_NAME, "ln-group")
        print(f"Found {len(groups)} CPI groups.")

        cpi_data = {}

        for group_index, group in enumerate(groups, start=1):
            try:
                group_title = group.find_element(By.CLASS_NAME, "title").text
                print(f"[{group_index}/{len(groups)}] Processing group: {group_title}")

                group_data = {}

                items = group.find_elements(By.CLASS_NAME, "cpi")
                print(f"Found {len(items)} items in group '{group_title}'.")

                for item_index, item in enumerate(items, start=1):
                    item_title = item.find_element(By.CLASS_NAME, "title").text
                    item_value = item.find_element(By.CLASS_NAME, "data").text
                    month = item.find_element(By.CLASS_NAME, "period-text").text
                    year = item.find_element(By.CLASS_NAME, "year").text

                    unique_item_title = f"{item_title}_{month}_{year}"
                    print(f"  [{item_index}/{len(items)}] Processing item: {unique_item_title} - {item_value}")

                    graph_icon = item.find_element(By.XPATH, ".//img[@alt='Historical Data']")
                    driver.execute_script("arguments[0].click();", graph_icon)
                    time.sleep(3)

                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.ID, "table0"))
                    )
                    print(f"    Detailed data page loaded for item '{unique_item_title}'.")

                    table_data = []
                    rows = driver.find_elements(By.XPATH, "//table[@id='table0']//tr")

                    headers = [header.text for header in rows[0].find_elements(By.TAG_NAME, "td")]
                    table_data.append(headers)

                    for row in rows[1:]:
                        cols = row.find_elements(By.TAG_NAME, "td")
                        col_data = [col.text for col in cols]
                        if col_data:
                            table_data.append(col_data)

                    print(f"    Data rows extracted for item '{unique_item_title}': {len(table_data) - 1} rows")

                    group_data[unique_item_title] = {
                        "value": item_value,
                        "date": f"{month} {year}",
                        "table_data": table_data
                    }

                    print(f"    Returning to the main CPI page after processing item '{unique_item_title}'.")
                    driver.back()
                    time.sleep(3)

                cpi_data[group_title] = group_data

            except Exception as group_error:
                print(f"Error processing group '{group_title}': {group_error}")

        with open("cpi_data_grouped.json", "w") as f:
            json.dump(cpi_data, f, indent=4)
        print("CPI data with grouped details saved to cpi_data_grouped.json")

    except Exception as e:
        print(f"Error fetching CPI data: {e}")



navigate_to_channel("https://discord.com/channels/1300818649233494116/1300818718947020884") # discord channel link 
track_and_save_messages()
fetch_cpi_data()

