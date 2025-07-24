from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
import pyautogui


# print("🖱️ Move your mouse over the Like button in the next 5 seconds...")
#
# time.sleep(5)  # Gives you time to move the mouse
#
# position = pyautogui.position()
# print(f"📍 Mouse is at: {position}")

like_button = {'x': 1070, 'y':602}
see_more_caption_button = {'x': 760, 'y':833}
show_comments_button = {'x': 1070, 'y':666}

USERNAME = "mayank.knytt"
PASSWORD = "Bundilal@123"
MAX_REELS = 10  # how many reels you want to like

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


def extract_parent_spans_only(comment_div):
    parent_spans = []

    # Get all spans under comment_div
    all_spans = comment_div.find_elements(By.XPATH, './/span')

    for span in all_spans:
        try:
            # If the span has no ancestor span other than itself inside comment_div, it's a parent
            ancestor_spans = span.find_elements(By.XPATH, './ancestor::span')
            if len(ancestor_spans) == 1:  # Only itself is an ancestor
                text = span.text.strip()
                if text:
                    parent_spans.append(text)
        except Exception as e:
            print(f"⚠️ Error reading span: {e}")

    return parent_spans

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

def mouse_click(x, y):
    time.sleep(2)  # wait for UI to settle
    pyautogui.moveTo(x, y, duration=0.3)
    pyautogui.click()
    print(f"Clicked Like at ({x}, {y})")


def scroll_to_next_reel():
    actions.send_keys(Keys.ARROW_DOWN).perform()
    wait(3)

# Run
login()
driver.get("https://www.instagram.com/reels/")
wait(5)

for i in range(MAX_REELS):
    print(f"\n📽️ Reel {i+1}/{MAX_REELS}")
    mouse_click(like_button['x'], like_button['y'])
    mouse_click(see_more_caption_button['x'], see_more_caption_button['y'])
    extract_caption_and_hashtags(driver)
    mouse_click(show_comments_button['x'], show_comments_button['y'])
    extract_top_level_comments(driver)
    scroll_to_next_reel()
driver.quit()
