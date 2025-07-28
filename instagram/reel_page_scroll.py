from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import pyperclip
import copy
from utils import *

def get_reel_sentiment(driver):
    try:
        main_div = driver.find_element(By.XPATH, '//main/div[1]')
        # spans = main_div.find_elements(By.XPATH, './/span')
        # contents = [s.text.strip() for s in spans if s.text.strip()]
        contents = main_div.text
        # Get result with automatic fallback
        try:
            reel_message = copy.deepcopy(messages)
            reel_message[1]["content"] = messages[1]["content"].format(reel_data=contents)
            response = router.get_result(reel_message, temperature=0.7)
            print("Chat GPT Responded.")
        except Exception as e:
            print("All models failed:", str(e))
            raise e

        free_text = response
        json_resp = repair_bad_json(free_text)
        current_reel_url = driver.current_url
        json_resp['reel_link'] = current_reel_url
        print("Parsed JSON: ", json_resp['summary'])
        return json_resp
    except Exception as e:
        print("❌ Could not extract caption/hashtags:", e)
        return {}

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

def start_reel_exploring(USERNAME = "sakshi.knytt", PASSWORD = "Bundilal@12345"):
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
