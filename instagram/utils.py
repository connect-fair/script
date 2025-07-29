import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
import pyautogui
import pickle
from openai import OpenAI
import re
import os
from aimodels import AIModelRouter
import sys
import signal
from aimodelsconfig import model_configs
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from json_repair import repair_json
from selenium.webdriver.common.by import By


# # === Function to save cookies ===
# def save_cookies_and_exit(*args):
#     print("💾 Saving cookies before exit...")
#     cookies = driver.get_cookies()
#     if len(cookies) != 0:
#         with open(COOKIE_FILE, "w") as f:
#             json.dump(cookies, f, indent=2)
#     try:
#         driver.quit()
#     except:
#         pass
#     sys.exit(0)
#
#
# # === Register cleanup handlers ===
# signal.signal(signal.SIGINT, save_cookies_and_exit)  # Ctrl+C
# signal.signal(signal.SIGTERM, save_cookies_and_exit)  # kill
# # Optional: exit hook
# import atexit
#
# atexit.register(save_cookies_and_exit)

# Configure your models (in practice, load from config/environment)
messages = [
    {
        "role": "system",
        "content": """You are a business strategist and outreach specialist tasked with analyzing public Instagram reel content to determine whether a creator is suitable to join our paid texting & video calling app (https://knytt.in), and how best to approach them — via a **personal message**, a **comment**, or **both**.
                    The main goals are:
                    - Grow the Knytt app user base: iOS (https://apps.apple.com/in/app/knytt/id6744828805), Android (https://play.google.com/store/apps/details?id=com.weknytt&hl=en_IN)
                    - Improve reach and curiosity around the Instagram page @knyttofficial
                    - Make all outreach (comments or DMs) feel natural, human, and contextual — not robotic or spammy
                    - Ensure you mainly target indian users as knytt is only supported in india as of now. 

                    **Commenting Strategy:**
                    - If the reel is emotionally rich or relatable, commenting may attract more audience engagement
                    - If the creator is highly likely to convert, tailor a personalized DM
                    - If both make sense, recommend both strategies
                    - Comments can be casual, funny, deep, or softly promotional — depending on the context

                    **Also consider:**
                    - 'reel_likes': measure of reach and viral potential
                    - 'reel_link': must be included in output JSON for future reference

                    **Output this exact JSON, the Output MUST only contain below JSON and no other free text, out put should be parsable by python json parser**
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
COOKIE_FILE = "cookies.json"

usernames = ["sakshi.knytt", "mayank.knytt" ]
current_user_index = -1
mouse_position = {
    "explore_first_post": {'x': 1200, 'y': 300},
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


def switch_user_if_needed(driver, post_login_url, post_login_steps):
    text_to_find = "We limit how often you can do certain things on Instagram"
    try:
        element = driver.find_element(By.XPATH, f"//span[contains(text(), {repr(text_to_find)})]")
        print(f"Switching user as rate limit reached for {usernames[current_user_index]}")
        login(post_login_url, post_login_steps)
    except Exception as e:
        print(f"User {usernames[current_user_index]} is valid to proceed.")
    return

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

def mouse_click(x, y):
    wait(2) # wait for UI to settle
    pyautogui.moveTo(x, y, duration=0.3)
    pyautogui.click()
    wait(2)
    print(f"Clicked Mouse at ({x}, {y})")

def extract_mouse_location():
    print("🖱️ Move your mouse over the Like button in the next 5 seconds...")
    time.sleep(5)  # Gives you time to move the mouse
    position = pyautogui.position()
    print(f"📍 Mouse is at: {position}")
    sys.exit(0)

def wait(sec=2):
    time.sleep(sec)

def next_user_index():
    global current_user_index
    if current_user_index + 1 >= len(usernames):
        current_user_index = 0
    else:
        current_user_index = current_user_index + 1
    return current_user_index

def login(post_login_url, post_login_steps = None):
    URL = "https://www.instagram.com/"
    driver.get(URL)
    wait(3)
    username = usernames[next_user_index()]
    driver.delete_all_cookies()
    print(f"Logging in user {username}.")
    # Load existing cookies (if any)
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "r") as f:
            all_cookies = json.load(f)
            cookies = all_cookies[username]
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"⚠️ Could not add cookie {cookie['name']}: {e}")
    driver.get(post_login_url)
    wait(5)
    if post_login_steps:
        post_login_steps()
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

def repair_bad_json(text):
    good_json_string = repair_json(text)
    try:
        return json.loads(good_json_string)
    except json.JSONDecodeError as e:
        print(f"Error parsing json_str {text}")
        raise ValueError(f"Failed to parse JSON: {str(e)}")
