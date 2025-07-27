import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
import pyautogui
import pickle
import pyperclip
from openai import OpenAI
import re
import os
from aimodels import AIModelRouter
import copy
import sys
import signal


# === Function to save cookies ===
def save_cookies_and_exit(*args):
    print("💾 Saving cookies before exit...")
    cookies = driver.get_cookies()
    if len(cookies) != 0:
        with open(COOKIE_FILE, "w") as f:
            json.dump(cookies, f, indent=2)
    try:
        driver.quit()
    except:
        pass
    sys.exit(0)


# === Register cleanup handlers ===
signal.signal(signal.SIGINT, save_cookies_and_exit)  # Ctrl+C
signal.signal(signal.SIGTERM, save_cookies_and_exit)  # kill
# Optional: exit hook
import atexit

atexit.register(save_cookies_and_exit)

# Configure your models (in practice, load from config/environment)
messages = [
    {
        "role": "system",
        "content": """You are a business strategist and outreach specialist tasked with analyzing public Instagram reel content to determine whether a creator is suitable to join our paid texting & video calling app (https://knytt.in), and how best to approach them — via a **personal message**, a **comment**, or **both**.
                    The main goals are:
                    - Grow the Knytt app user base: iOS (https://apps.apple.com/in/app/knytt/id6744828805), Android (https://play.google.com/store/apps/details?id=com.weknytt&hl=en_IN)
                    - Improve reach and curiosity around the Instagram page @knyttofficial
                    - Make all outreach (comments or DMs) feel natural, human, and contextual — not robotic or spammy

                    **Commenting Strategy:**
                    - If the reel is emotionally rich or relatable, commenting may attract more audience engagement
                    - If the creator is highly likely to convert, tailor a personalized DM
                    - If both make sense, recommend both strategies
                    - Comments can be casual, funny, deep, or softly promotional — depending on the context

                    **Also consider:**
                    - 'reel_likes': measure of reach and viral potential
                    - 'reel_link': must be included in output JSON for future reference

                    **Output this exact JSON, the Output MUST only contain below JSON and no other free text:**
                    {
                      "summary": string,
                      "creator_persona": string,
                      "comment_sentiment": string,
                      "conversion_likelihood": "High" | "Medium" | "Low",
                      "target_for_outreach": "creator" | "audience" | "both",
                      "score_out_of_10": number,
                      "reel_likes": number,
                      "reel_link": string,
                      "creator_profile_link": string,
                      "reasoning": string,
                      "outreach_strategy": "message" | "comment" | "both" | "none",
                      "personalized_pitch_message": string | null,
                      "public_comment": string | null
                    }

                    Always prioritize:
                    - Driving curiosity to check out Knytt
                    - Personal connection and contextual relevance
                    - Natural, creative tone"""
    },
    {
        "role": "user",
        "content": """I will now give you an array of **unstructured textual information** scraped from a public Instagram reel page.
                    **Instructions:**
                    - Parse and distinguish between: caption, comments, views, likes, tags, and any clues about the creator
                    - Analyze the audience’s tone and reaction
                    - Decide whether to send DM, comment, or both
                    - Generate the actual text to send or comment

                    **Here is the unstructured content:**
                    {reel_data}"""
    }
]
model_configs = [
    {
        'model_name': 'openai/gpt-4.1',
        'api_key': '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',
        'organization': 'org-your-org',
        'priority': 0
    },
    {
        'model_name': 'openai/gpt-4o',
        'api_key': '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',
        'organization': 'org-your-org',
        'priority': 1
    },
    {
        'model_name': 'deepseek/DeepSeek-V3-0324',
        'api_key': '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',
        'priority': 2
    }
]
COOKIE_FILE = "cookies.json"

mouse_position = {
    "like_button": {'x': 1070, 'y': 602},
    "see_more_caption_button": {'x': 900, 'y': 833},
    "show_comments_button": {'x': 1070, 'y': 666},
    "type_comments": {'x': 1200, 'y': 666},
}
router = AIModelRouter(model_configs)
MAX_REELS = 100  # how many reels you want to like

# Setup
options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)
actions = ActionChains(driver)


def extract_mouse_location():
    print("🖱️ Move your mouse over the Like button in the next 5 seconds...")
    time.sleep(5)  # Gives you time to move the mouse
    position = pyautogui.position()
    print(f"📍 Mouse is at: {position}")
    sys.exit(0)


def wait(sec=2):
    time.sleep(sec)


def login():
    URL = "https://www.instagram.com/"
    driver.get(URL)
    wait(3)
    # Load existing cookies (if any)
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "r") as f:
            cookies = json.load(f)
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"⚠️ Could not add cookie {cookie['name']}: {e}")
    driver.get(URL)
    wait(5)
    # driver.find_element(By.NAME, "username").send_keys(USERNAME)
    # driver.find_element(By.NAME, "password").send_keys(PASSWORD + Keys.ENTER)
    # wait(5)

    # Skip popups
    for _ in range(2):
        try:
            driver.find_element(By.XPATH, "//button[text()='Not Now']").click()
            wait(2)
        except:
            pass


def extract_json_from_markdown(text):
    """
    Extracts JSON between ```json and ```, safely converts single quotes to double quotes,
    and returns a Python dictionary.
    """
    # Step 1: Extract the JSON block
    json_match = re.search(r'```json(.*?)```', text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        json_str = text

    # Step 2: Convert single-quoted JSON to valid JSON
    # --- Phase 1: Convert keys ---
    json_str = re.sub(
        r"'(.*?)'\s*:",  # Matches 'key':
        lambda m: f'"{m.group(1)}":',
        json_str
    )

    # --- Phase 2: Convert string values ---
    json_str = re.sub(
        r":\s*'(.*?)'\s*([,\]}])",  # Matches : 'value', } or ]
        lambda m: f': "{m.group(1)}"{m.group(2)}',
        json_str
    )

    # Step 3: Parse the fixed JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {str(e)}")


def get_reel_sentiment(driver):
    try:
        main_div = driver.find_element(By.XPATH, '//main/div[1]')
        spans = main_div.find_elements(By.XPATH, './/span')
        contents = [s.text.strip() for s in spans if s.text.strip()]
        contents = main_div.text
        # Get result with automatic fallback
        try:
            reel_message = copy.deepcopy(messages)
            reel_message[1]["content"] = messages[1]["content"].format(reel_data=contents)
            response = router.get_result(reel_message, temperature=0.7)
            print("Chat GPT Response:", response)
        except Exception as e:
            print("All models failed:", str(e))
            raise e

        free_text = response
        json_resp = extract_json_from_markdown(free_text)
        current_reel_url = driver.current_url
        json_resp['reel_link'] = current_reel_url
        print("Parsed JSON: ", json_resp)
        return json_resp
    except Exception as e:
        print("❌ Could not extract caption/hashtags:", e)
        return {}


def mouse_click(x, y):
    time.sleep(2)  # wait for UI to settle
    pyautogui.moveTo(x, y, duration=0.3)
    pyautogui.click()
    time.sleep(2)
    print(f"Clicked Mouse at ({x}, {y})")


def persist_in_excel(json_data):
    """
    Saves JSON data to an Excel file, appending if the file already exists.

    Args:
        json_data (dict): Dictionary containing the data to be saved.
    """
    # Convert JSON to DataFrame with proper orientation
    if isinstance(json_data, dict):
        # Handle scalar values (single-row data)
        if all(not isinstance(v, (list, dict)) for v in json_data.values()):
            df = pd.DataFrame([json_data])  # Wrap in list to create single-row DataFrame
        else:
            df = pd.DataFrame.from_dict(json_data, orient='index').T  # Transpose if needed
    else:
        raise ValueError("Input must be a dictionary")

    # Append to existing Excel or create new file
    excel_file = 'data.xlsx'
    try:
        existing_df = pd.read_excel(excel_file)
        updated_df = pd.concat([existing_df, df], ignore_index=True)
    except FileNotFoundError:
        updated_df = df

    # Write back to Excel
    updated_df.to_excel(excel_file, index=False)


def scroll_to_next_reel():
    actions.send_keys(Keys.ARROW_DOWN).perform()
    wait(3)


def comment_or_send_message(reel_data):
    # reel_data
    public_comment = reel_data.get("public_comment")
    personalized_pitch_message = reel_data.get("personalized_pitch_message")
    print(f"Public comment: {public_comment}")
    print(f"Personalised Pitch Message: {personalized_pitch_message}")
    try:
        if public_comment:
            mouse_click(mouse_position['show_comments_button']['x'], mouse_position['show_comments_button']['y'])
            wait(3)
            mouse_click(mouse_position['type_comments']['x'], mouse_position['type_comments']['y'])
            wait(2)

            ## Paste in comment box
            pyperclip.copy(public_comment)
            actions.key_down(Keys.COMMAND).send_keys('v').key_up(Keys.COMMAND).perform()
            print("Public comment copied to clipboard.", public_comment)
            wait(3)
            ## Send
            post_button = driver.find_element(By.XPATH, "//div[@role='button' and text()='Post']")
            post_button.click()
            wait(3)
            mouse_click(mouse_position['type_comments']['x'], mouse_position['type_comments']['y'] + 100)
        if personalized_pitch_message:
            print("Sending personalized pitch message not implemented yet. Skipping for now...")
        else:
            print("No personalized pitch message found.")
    except Exception as e:
        print("Could not send message or comment:", e)


def click_on_caption_more_button():
    try:
        more_button = driver.find_element(By.XPATH, "//span[@aria-hidden='true' and text()='more']")
        more_button.click()
        wait(3)
    except Exception as e:
        print("Could not click on caption more button:", e)


def start_exploring(USERNAME = "sakshi.knytt", PASSWORD = "Bundilal@12345"):
    # Run
    # extract_mouse_location()
    login()
    driver.get("https://www.instagram.com/reels/")
    wait(5)
    processed_reel = {}
    for i in range(MAX_REELS):
        print(f"\n📽️ Reel {i + 1}/{MAX_REELS}")

        if driver.current_url in processed_reel:
            print("Skipping already processed reel.")
            wait(2)
            continue

        # mouse_click(mouse_position['like_button']['x'], mouse_position['like_button']['y'])
        click_on_caption_more_button()
        reel_data = get_reel_sentiment(driver)
        if reel_data.get("score_out_of_10", 0) >= 8:
            print("Reaching out as score is above 8.")
            persist_in_excel(reel_data)
            comment_or_send_message(reel_data)
        else:
            print("Skipping as score is below 8.", reel_data)
        processed_reel[driver.current_url] = True
        # extract_top_level_comments(driver)
        scroll_to_next_reel()
    driver.quit()
