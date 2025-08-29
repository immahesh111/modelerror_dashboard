import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import pandas as pd
import pymongo
from datetime import datetime, timedelta
import glob
import logging
import threading
import signal
import sys
from retry import retry

# Set up logging with file handler for persistence
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

# Placeholder for MongoDB connection string
MONGO_URI = "mongodb+srv://nsneditz111_db_user:gK4RIMYPNjIW8JRV@mqscluster.ahth286.mongodb.net/?retryWrites=true&w=majority&appName=mqscluster"
client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client["error_data"]

# URL and XPaths
URL = "https://mqs.motorola.com/NPI/NTF_Pareto_Split.aspx?enc=DyJ232ifxtkKHA9i91yj9sqQMSLZOSLQurMRneg7xoGrf0gH/lvmjUBPRSLFgEDoimg2ixNrQoaOpqs8QO+/9Um5HOmxTwsJhGgxOQHfjBeBwCLrEJICAES7OPJ1rD2V"
PLANT_COMBOBOX_XPATH = "/html/body/form/div[3]/table[1]/tbody/tr[2]/td/div/table/tbody/tr/td[2]/div/select"
SECTOR_68_OPTION_XPATH = "/html/body/form/div[3]/table[1]/tbody/tr[2]/td/div/table/tbody/tr/td[2]/div/select/option[4]"
START_DATE_INPUT_XPATH = "/html/body/form/div[3]/table[2]/tbody/tr[1]/td[1]/div/div[2]/div/div/table/tbody/tr[2]/td[3]/input"
START_TODAY_XPATH = "/html/body/form/div[3]/table[2]/tbody/tr[1]/td[1]/div/div[2]/div/div/table/tbody/tr[2]/td[2]/div/div/div[3]/div"
END_DATE_INPUT_XPATH = "/html/body/form/div[3]/table[2]/tbody/tr[1]/td[1]/div/div[2]/div/div/table/tbody/tr[3]/td[3]/input"
END_TODAY_XPATH = "/html/body/form/div[3]/table[2]/tbody/tr[1]/td[1]/div/div[2]/div/div/table/tbody/tr[3]/td[2]/div/div/div[3]/div"
START_TIME_INPUT_XPATH = "/html/body/form/div[3]/table[2]/tbody/tr[1]/td[1]/div/div[2]/div/div/table/tbody/tr[2]/td[6]/input"
END_TIME_INPUT_XPATH = "/html/body/form/div[3]/table[2]/tbody/tr[1]/td[1]/div/div[2]/div/div/table/tbody/tr[3]/td[6]/input"
GENERATE_BUTTON_XPATH = "/html/body/form/div[3]/table[1]/tbody/tr[1]/td[6]/input"

# Download directory
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def get_current_shift():
    """Determine current shift based on time"""
    current_hour = datetime.now().hour
    return 1 if 7 <= current_hour < 19 else 2

@retry(tries=3, delay=5, backoff=2, max_delay=30)
def fetch_and_download(shift):
    """Fetch and download Excel file with retry mechanism"""
    driver = None
    try:
        # Clear download directory
        for f in glob.glob(os.path.join(DOWNLOAD_DIR, "*.xls*")):
            os.remove(f)
            logging.info(f"Cleared old file: {f}")

        # Set up Chrome options
        options = Options()
        options.add_argument("--headless")  # Run in headless mode for reliability
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("prefs", {
            "download.default_directory": DOWNLOAD_DIR,
            "download.prompt_for_download": False,
            "safebrowsing.enabled": True
        })

        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        
        logging.info("Navigating to URL")
        driver.get(URL)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, PLANT_COMBOBOX_XPATH))
        )
        
        # Select Sector 68
        plant_combobox = driver.find_element(By.XPATH, PLANT_COMBOBOX_XPATH)
        plant_combobox.click()
        time.sleep(1)
        sector_68 = driver.find_element(By.XPATH, SECTOR_68_OPTION_XPATH)
        sector_68.click()
        time.sleep(1)
        logging.info("Selected Sector 68")
        
        # Set dates
        for date_xpath, today_xpath in [
            (START_DATE_INPUT_XPATH, START_TODAY_XPATH),
            (END_DATE_INPUT_XPATH, END_TODAY_XPATH)
        ]:
            driver.find_element(By.XPATH, date_xpath).click()
            time.sleep(1)
            driver.find_element(By.XPATH, today_xpath).click()
            time.sleep(1)
        logging.info("Set dates to today")
        
        # Set shift times
        shift_times = {
            1: ("07:00:00", "19:00:00"),
            2: ("19:00:00", "07:00:00")
        }
        start_time, end_time = shift_times[shift]
        
        for time_xpath, time_value in [
            (START_TIME_INPUT_XPATH, start_time),
            (END_TIME_INPUT_XPATH, end_time)
        ]:
            time_input = driver.find_element(By.XPATH, time_xpath)
            time_input.clear()
            time_input.send_keys(time_value)
            time.sleep(1)
            logging.info(f"Set time {time_xpath} to {time_value}")
        
        # Generate report
        driver.find_element(By.XPATH, GENERATE_BUTTON_XPATH).click()
        logging.info("Clicked Generate Report")
        
        # Poll for file download
        max_wait = 120
        waited = 0
        while waited < max_wait:
            files = glob.glob(os.path.join(DOWNLOAD_DIR, "*.xls*"))
            if files:
                latest_file = max(files, key=os.path.getctime)
                logging.info(f"Downloaded file: {latest_file}")
                return latest_file
            time.sleep(2)
            waited += 2
        
        raise ValueError("No Excel file downloaded after waiting 120 seconds")
    
    except Exception as e:
        logging.error(f"Error in fetch_and_download: {str(e)}")
        raise
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def process_excel(file_path, shift):
    """Process Excel file and push to MongoDB with duplicate removal"""
    try:
        # Read Excel with fallback engines
        for engine in ["openpyxl", "xlrd"]:
            try:
                df = pd.read_excel(file_path, sheet_name="Total", engine=engine)
                break
            except:
                continue
        else:
            raise ValueError("Failed to read Excel file with any engine")
        
        # Find header row
        required_cols = ["Track Id", "NTF?", "Family", "Process", "Testcode", "Test Val", "LL", "UL", "2nd P/F", "3rd P/F"]
        header_row = None
        header_values = None
        for idx in range(len(df)):
            row = df.iloc[idx]
            try:
                if str(row.iloc[2]).strip() == "NTF?" and str(row.iloc[9]).strip() == "Testcode":
                    header_row = idx
                    header_values = [str(val).strip() for val in row]
                    logging.info(f"Selected header row {idx + 2}: {header_values}")
                    break
            except IndexError:
                continue
        
        if header_row is None:
            raise ValueError("No valid header row found with 'NTF?' in Column C and 'Testcode' in Column J")
        
        # Reload with correct header
        df = pd.read_excel(file_path, sheet_name="Total", skiprows=header_row)
        df.columns = header_values
        
        # Select required columns
        df = df[required_cols]
        
        # Filter NTF? to blanks and remove duplicates based on Track Id
        df = df[df["NTF?"].isna()].drop_duplicates(subset=["Track Id"], keep="first")
        logging.info(f"Filtered {len(df)} unique rows with blank NTF?")
        
        # Process each model
        models = [model for model in df["Family"].unique() if pd.notna(model)]
        logging.info(f"Found models: {models}")
        
        for model in models:
            model_df = df[df["Family"] == model]
            data = model_df[required_cols].to_dict("records")
            
            # Add shift and timestamp
            for doc in data:
                doc["shift"] = shift
                doc["timestamp"] = datetime.now()
            
            # Create/use collection
            coll_name = model.replace("/", "_").replace(" ", "_")
            coll = db[coll_name]
            
            # Delete previous data
            coll.delete_many({})
            logging.info(f"Cleared previous data for model {model}")
            
            # Insert new data
            if data:
                coll.insert_many(data)
                logging.info(f"Pushed {len(data)} unique records for model {model} in shift {shift}")
            else:
                logging.warning(f"No data to push for model {model} in shift {shift}")
    
    except Exception as e:
        logging.error(f"Error in process_excel: {str(e)}")
        raise

def run_cycle():
    """Main execution cycle"""
    try:
        current_time = datetime.now()
        current_hour = current_time.hour
        shift = get_current_shift()
        
        # Check if current time is within shift hours
        if (shift == 1 and 7 <= current_hour < 19) or (shift == 2 and (current_hour >= 19 or current_hour < 7)):
            logging.info(f"Starting cycle for Shift {shift} at {current_time}")
            file_path = fetch_and_download(shift)
            process_excel(file_path, shift)
            
            # Cleanup
            if os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"Cleaned up file: {file_path}")
        else:
            logging.info(f"Skipping cycle: Current time {current_time} is outside Shift {shift} hours")
            
    except Exception as e:
        logging.error(f"Cycle failed: {str(e)}")
        raise

def schedule_runs():
    """Run cycle immediately and schedule subsequent runs every 30 minutes"""
    # Run immediately
    run_cycle()
    
    # Schedule subsequent runs
    while True:
        try:
            time.sleep(1800)  # Wait 30 minutes
            run_cycle()
        except Exception as e:
            logging.error(f"Scheduled run failed: {str(e)}")
            logging.info("Continuing to next cycle in 30 minutes...")
            continue

def signal_handler(sig, frame):
    """Handle graceful shutdown"""
    logging.info("Received shutdown signal, cleaning up...")
    client.close()
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logging.info(f"Starting script at {datetime.now()}")
    
    # Start scheduling in a separate thread to allow immediate execution
    threading.Thread(target=schedule_runs, daemon=True).start()
    
    # Keep main thread alive
    while True:
        try:
            time.sleep(60)  # Sleep to reduce CPU usage
        except KeyboardInterrupt:
            signal_handler(signal.SIGINT, None)