import asyncio
import pandas as pd
import logging
from playwright.async_api import async_playwright, Page, TimeoutError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


TARGET_URL = "https://pai.gov.in/PS/Public/TW-GP.aspx?s=2" 
STATE_NAME = "Punjab"
# Based on the AI Pilot problem statement 
TARGET_DISTRICTS = ["Bathinda", "Rupnagar", "Patiala", "Fatehgarh Sahib"] 
TARGET_DOMAINS = ["Health", "Sanitation", "Wellbeing", "Social Development", "Livelihoods"]


SEL_STATE_DROPDOWN = "#ddl_State"
SEL_DISTRICT_DROPDOWN = "#ddl_District"

SEL_BLOCK_DROPDOWN = "#ddl_Block"
SEL_SEARCH_BTN = "#btnSubmit"
SEL_DATA_TABLE = "table#GVdataT"
SEL_TABLE_ROWS = f"{SEL_DATA_TABLE} tbody tr"

async def extract_table_data(page, district_text, block_text) -> list:
    """Extracts data and formats it into an AI-ready Wide Dataset with LGD Codes."""
    records = []
    try:
        await page.wait_for_selector(SEL_DATA_TABLE, state="visible", timeout=15000)
        await page.wait_for_timeout(1000) 
        
        rows = await page.query_selector_all(f"{SEL_DATA_TABLE} tbody tr")
        
        # Regex to extract the name and the [LGD_CODE]
        import re
        def extract_name_and_id(raw_text):
            match = re.search(r'(.*?)(?:-\s*|)\s*\[(\d+)\]', raw_text)
            if match:
                return match.group(1).strip(), match.group(2).strip()
            return raw_text.strip(), None

        dist_name, dist_lgd = extract_name_and_id(district_text)
        block_name, block_lgd = extract_name_and_id(block_text)
        
        for row in rows:
            cols = await row.query_selector_all("td")
            
            if len(cols) >= 11:
                # 1. Extract Village Name and Village LGD Code
                village_cell_html = await cols[0].inner_html()
                v_match = re.search(r'<a[^>]*>(.*?)</a>', village_cell_html)
                raw_village_text = v_match.group(1) if v_match else "Unknown"
                
                village_name, village_lgd = extract_name_and_id(raw_village_text)

                # Helper to safely grab scores
                async def get_score(col_index):
                    text = await cols[col_index].inner_text()
                    val = text.split('\n')[0].strip() if text else None
                    return float(val) if val and val.replace('.','',1).isdigit() else pd.NA

                # 2. Build the "Wide" Record for the AI
                record = {
                    "state": STATE_NAME,
                    "district_name": dist_name,
                    "district_lgd_code": dist_lgd,
                    "block_name": block_name,
                    "block_lgd_code": block_lgd,
                    "village_name": village_name,
                    "village_lgd_code": village_lgd,
                    # Features representing domains
                    "score_livelihoods": await get_score(2),
                    "score_health": await get_score(3),
                    "score_child_friendly": await get_score(4),
                    "score_water_sanitation": await get_score(5),
                    "score_clean_green": await get_score(6),
                    "score_infrastructure": await get_score(7),
                    "score_social_dev": await get_score(8),
                    "score_governance": await get_score(9),
                    "score_women_friendly": await get_score(10)
                }
                records.append(record)
                        
    except TimeoutError:
        logging.warning(f"Timeout: No data table found.")
    except Exception as e:
        logging.error(f"Extraction error: {e}")
        
    return records

async def scrape_pai_portal():
    all_extracted_data = []
    
    async with async_playwright() as p:
        # Launch browser with explicit geolocation permissions and English headers
        browser = await p.chromium.launch(headless=False, slow_mo=800) 
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            locale='en-IN', 
            permissions=['geolocation'], 
            extra_http_headers={
                'Accept-Language': 'en-IN,en;q=0.9,en-US;q=0.8'
            }
        )
        page = await context.new_page()
        
        try:
            logging.info("Initializing session at the main portal...")
            # We use 'domcontentloaded' because Bhashini scripts often hang 'networkidle'
            await page.goto("https://pai.gov.in/", wait_until="domcontentloaded", timeout=60000)
            
            logging.info("Forcing English via Bhashini Plugin...")
            try:
                await page.locator(".bhashini-dropdown-btn").click(timeout=5000)
                await page.locator(".language-option[data-value='en']").click(timeout=5000)
                logging.info("Bhashini translation set to English.")
                await page.wait_for_timeout(2000) 
            except Exception as e:
                logging.warning(f"Bhashini toggle failed, attempting to proceed: {e}")

            logging.info("Navigating via menu to target dashboard...")
            await page.locator("text=5. PAI 2.0 Score").hover()
            await page.wait_for_timeout(1000)
            
            await page.get_by_role("link", name="5.2 Theme wise PAI Scores of").click()
            await page.wait_for_load_state("domcontentloaded")
            logging.info("Successfully reached the target dashboard!")

            await page.wait_for_selector(SEL_STATE_DROPDOWN, state="visible", timeout=15000)
            logging.info(f"Selecting State: Punjab (Value: 3)")
            await page.locator(SEL_STATE_DROPDOWN).select_option(value="3")
            
            await page.wait_for_timeout(3000) 

            for district in TARGET_DISTRICTS:
                logging.info(f"Processing District: {district}")
                
                try:
                    # FIX: Inject JS to find the exact hidden 'value' attribute for the district
                    # This completely bypasses any invisible characters or translation plugin weirdness
                    district_val = await page.evaluate(f'''(dist) => {{
                        const options = Array.from(document.querySelectorAll("{SEL_DISTRICT_DROPDOWN} option"));
                        const match = options.find(o => o.innerText.toLowerCase().includes(dist.toLowerCase()));
                        return match ? match.value : null;
                    }}''', district)
                    
                    if not district_val or district_val == "0":
                        logging.warning(f"Could not find a valid dropdown value for {district}. Skipping.")
                        continue
                        
                    logging.info(f"  -> Selecting District by internal value: {district_val}")
                    # Select by the exact numeric value instead of the messy text label
                    await page.locator(SEL_DISTRICT_DROPDOWN).select_option(value=district_val)
                    
                    await page.wait_for_timeout(3000)
                    
                    
                    block_data = await page.evaluate(f'''() => {{
                        const options = Array.from(document.querySelectorAll("{SEL_BLOCK_DROPDOWN} option"));
                        // Filter out the default "-Select-" option which usually has value "0" or ""
                        return options.map(o => ({{text: o.innerText.trim(), value: o.value}})).filter(o => o.value !== "0" && o.value !== "");
                    }}''')
                    
                    if not block_data:
                        logging.warning(f"No valid blocks found for {district}. Trying Search directly.")
                        await page.locator(SEL_SEARCH_BTN).click()
                        await page.wait_for_load_state("domcontentloaded")
                        data = await extract_table_data(page, district, "All")
                        all_extracted_data.extend(data)
                        continue

                    for block in block_data:
                        b_text = block['text']
                        b_val = block['value']
                        
                        logging.info(f"  -> Selecting Block: {b_text} (Value: {b_val})")
                        await page.locator(SEL_BLOCK_DROPDOWN).select_option(value=b_val)
                        await page.wait_for_timeout(2000) # Buffer for UI
                        
                        await page.locator(SEL_SEARCH_BTN).click()
                        
                        # Wait for the table data to process and render
                        await page.wait_for_load_state("domcontentloaded")
                        await page.wait_for_timeout(2000)
                        
                        # Call the custom wide-format HTML extractor
                        data = await extract_table_data(page, district, b_text) 
                        all_extracted_data.extend(data)
                        logging.info(f"  -> Extracted {len(data)} records from {b_text}")
                        
                except Exception as dist_err:
                    logging.error(f"Failed to process district {district}: {dist_err}")
                    # Recovery: Refresh the dashboard via the menu if a district fails
                    await page.goto("https://pai.gov.in/", wait_until="domcontentloaded")
                    await page.locator("text=5. PAI 2.0 Score").hover()
                    await page.get_by_role("link", name="5.2 Theme wise PAI Scores of").click()
                    await page.wait_for_load_state("domcontentloaded")
                    await page.locator(SEL_STATE_DROPDOWN).select_option(value="3")
                    await page.wait_for_timeout(3000)
                            
        except Exception as e:
            logging.error(f"Critical Pipeline Failure: {e}")
        finally:
            await browser.close()
            
    return all_extracted_data

def format_for_ai_model(raw_data):
    if not raw_data:
        logging.warning("Pipeline finished but no data was collected.")
        return
        
    df = pd.DataFrame(raw_data)
    
    df.replace("", pd.NA, inplace=True)
    df.replace("N/A", pd.NA, inplace=True)
    
    score_columns = [col for col in df.columns if col.startswith('score_')]
    
    df.dropna(subset=score_columns, how='all', inplace=True) 
    
    csv_filename = "punjab_village_status_ai_dataset_wide.csv"
    df.to_csv(csv_filename, index=False)
    
    logging.info(f"SUCCESS: AI-ready dataset saved to {csv_filename} with {len(df)} rows.")
    print("\n--- Dataset Snapshot ---")
    print(df.head())

if __name__ == "__main__":
    extracted_data = asyncio.run(scrape_pai_portal())
    format_for_ai_model(extracted_data)