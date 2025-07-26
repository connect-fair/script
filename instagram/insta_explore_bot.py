import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
import pyautogui
from openai import OpenAI
import re

client = OpenAI(
    base_url="https://models.github.ai/inference",
    api_key="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",
)

# print("🖱️ Move your mouse over the Like button in the next 5 seconds...")
#
# time.sleep(5)  # Gives you time to move the mouse
#
# position = pyautogui.position()
# print(f"📍 Mouse is at: {position}")

like_button = {'x': 1070, 'y':602}
see_more_caption_button = {'x': 900, 'y':833}
show_comments_button = {'x': 1070, 'y':666}

USERNAME = "mayank.knytt"
PASSWORD = "Bundilal@123"
MAX_REELS = 100  # how many reels you want to like

# Setup
options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)
actions = ActionChains(driver)

def wait(sec=2):
    time.sleep(sec)

def login():
    driver.get("https://www.instagram.com/accounts/login/")
    wait(3)
    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD + Keys.ENTER)
    wait(5)

    # Skip popups
    for _ in range(2):
        try:
            driver.find_element(By.XPATH, "//button[text()='Not Now']").click()
            wait(2)
        except:
            pass

def extract_top_level_comments(driver):
    try:
        wait(5)
        comments = []

        # Find all "reply" containers (those that contain a 'Reply' span)
        reply_divs = driver.find_elements(By.XPATH,
                                          '//div[.//span[contains(translate(text(), "REPLY", "reply"), "reply")]]')

        print("Reply div length: ", len(reply_divs))
        for i in range(min(20, len(reply_divs))):
            try:
                reply_div = reply_divs[i]
                # Get the immediately preceding sibling div (actual comment block)
                print("Reply Div: ", reply_div)
                comment_div = reply_div.find_element(By.XPATH, './ancestor::div[2]')

                # Collect all <span> texts in that comment block
                spans = comment_div.find_elements(By.XPATH, './/span')
                span_texts = [s.text.strip() for s in spans if s.text.strip()]

                if span_texts:
                    comments.append(span_texts)
            except Exception as inner_e:
                print("⚠️ Skipping one reply block due to error:", inner_e)
        comments_set = set()
        for comment in comments:
            for c in comment:
                comments_set.add(c)
        print("comments_set: ", comments_set)
        return comments_set

    except Exception as e:
        print("❌ Error extracting comments:", e)
        return []

def extract_caption_and_hashtags(driver):
    try:
        # Find any hashtag anchor first
        hashtag_anchor = driver.find_element(By.XPATH, '//a[starts-with(@href, "/explore/tags/")]')

        # Get the parent <span> containing the caption and hashtags
        caption_span = hashtag_anchor.find_element(By.XPATH, './ancestor::span[1]')
        caption = caption_span.text

        # Extract all hashtags (i.e., all <a> inside the same span with /explore/tags/)
        hashtag_anchors = caption_span.find_elements(By.XPATH, './/a[starts-with(@href, "/explore/tags/")]')
        hashtags = [a.text for a in hashtag_anchors]

        print("📝 Caption:", caption)
        print("🏷️ Hashtags:", hashtags)

        return {
            "caption": caption,
            "hashtags": hashtags
        }

    except Exception as e:
        print("❌ Could not extract caption/hashtags:", e)
        return None

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
    print("JSON String: ", json_str)

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
    # return {
    #     "summary": "The scraped content includes public reels from various creators with themes around relationships, friendship, humor, and mindfulness. Captions include tags like #friendship, #lovequotes, #contentcreator, and #reels, indicating interest in emotional and relatable topics. Audience reactions show high engagement and emotional resonance, with several reels surpassing 100K likes. Creators vary in niches, with an undercurrent of relatability and positivity.",
    #     "creator_persona": "Relatable content creating positive and emotionally engaging reels about friendship, love, and life moments.",
    #     "comment_sentiment": "Positive and relational",
    #     "conversion_likelihood": "High",
    #     "target_for_outreach": "both",
    #     "score_out_of_10": 9,
    #     "reel_likes": 126000,
    #     "reel_link": "https://www.instagram.com/reel/126K_likes_example",
    #     "creator_profile_link": "https://www.instagram.com/adit__y.a",
    #     "reasoning": "This creator's content focuses on themes of love, friendship, and emotional relationships, which align with Knytt's goals of fostering personal and engaging interaction. Their reel performance with 126K likes shows substantial reach and engagement, and their audience is highly interactive and emotionally connected.",
    #     "outreach_strategy": "both",
    #     "personalized_pitch_message": "Hi Adit! 😊 Loved your reel about supportive best friends — it’s so heartfelt and relatable. At Knytt, we're building a text and video calling app for meaningful and real connections like the ones you share in your content. Would love to share more and possibly collaborate. Let me know what you think!",
    #     "public_comment": "This is so sweet! 🥺 You nailed the feeling of having a supportive best friend. ❤️ Have you checked out @knyttofficial? They’re all about creating spaces for meaningful connections like this!"
    # }
    try:
        main_div = driver.find_element(By.XPATH, '//main/div[1]')
        spans = main_div.find_elements(By.XPATH, './/span')
        contents = [s.text.strip() for s in spans if s.text.strip()]
        contents = main_div.text
        response = client.chat.completions.create(
            model="deepseek/DeepSeek-V3-0324",
            temperature=1,
            max_tokens=4096,
            top_p=1,
            messages=[
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
                        "content": f"""I will now give you an array of **unstructured textual information** scraped from a public Instagram reel page.
                        **Instructions:**
                        - Parse and distinguish between: caption, comments, views, likes, tags, and any clues about the creator
                        - Analyze the audience’s tone and reaction
                        - Decide whether to send DM, comment, or both
                        - Generate the actual text to send or comment
                        
                        **Here is the unstructured content:**
                        {contents}"""
                },
                {
                    "role": "user",
                    "content": (
                        "I will now give you an array of **unstructured textual information** scraped from a public Instagram reel page.\n\n"
                        "**Instructions:**\n"
                        "- Parse and distinguish between: caption, comments, views, likes, tags, and any clues about the creator\n"
                        "- Analyze the audience’s tone and reaction\n"
                        "- Decide whether to send DM, comment, or both\n"
                        "- Generate the actual text to send or comment\n\n"
                        "**Here is the unstructured content:**\n\n"
                        f"{contents}"  # your variable from scraping
                    )
                }
            ]
        )
        free_text = response.choices[0].message.content
        json_resp = extract_json_from_markdown(free_text)
        print("JSON Response: ", json_resp)
        current_reel_url = driver.current_url
        json_resp['reel_link'] = current_reel_url
        return json_resp
    except Exception as e:
        print("❌ Could not extract caption/hashtags:", e)
        return {}

def mouse_click(x, y):
    time.sleep(2)  # wait for UI to settle
    pyautogui.moveTo(x, y, duration=0.3)
    pyautogui.click()
    time.sleep(2)
    print(f"Clicked Like at ({x}, {y})")


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
    actions.send_keys(Keys.ARROW_RIGHT).perform()
    wait(3)

# Run
login()
driver.get("https://www.instagram.com/gaurgopaldas/reels/")
wait(5)
processed_reel = {}
for i in range(MAX_REELS):
    print(f"\n📽️ Reel {i+1}/{MAX_REELS}")

    # if driver.current_url in processed_reel:
    #     print("Skipping already processed reel.")
    #     wait(2)
    #     continue

    #mouse_click(like_button['x'], like_button['y'])
    mouse_click(see_more_caption_button['x'], see_more_caption_button['y'])
    reel_data = get_reel_sentiment(driver)
    print("Response Reel Data: ", reel_data)
    if reel_data.get("score_out_of_10", 0) >= 8:
        print("Reaching out as score is above 8.")
        persist_in_excel(reel_data)
    else:
        print("Skipping as score is below 8.", reel_data)

    processed_reel[driver.current_url] = True

    # mouse_click(show_comments_button['x'], show_comments_button['y'])
    # extract_top_level_comments(driver)
    scroll_to_next_reel()
driver.quit()
