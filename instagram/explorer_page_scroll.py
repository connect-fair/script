from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import pyperclip
import copy
from utils import *

def get_explorer_post_sentiment(driver):
    try:
        # Find the article with role="presentation"
        article = driver.find_element(
            By.CSS_SELECTOR,
            "article[role='presentation']"
        )

        # Find the <ul> inside this article
        main_div = article.find_element(By.TAG_NAME, "ul")  # if only one <ul>
        contents = main_div.text
        # Get result with automatic fallback
        try:
            reel_message = copy.deepcopy(messages)
            reel_message[1]["content"] = messages[1]["content"].format(reel_data=contents)
            response = router.get_result(reel_message, temperature=0.7)
            print("Chat GPT Responded.", response)
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
        print("❌Could not find article:", e)
        return {}

def swipe_to_next_post():
    actions.send_keys(Keys.ARROW_RIGHT).perform()
    wait(3)

def comment_or_send_message_in_explorer_post(driver, post_data):
    # reel_data
    public_comment = post_data.get("public_comment")
    personalized_pitch_message = post_data.get("personalized_pitch_message")
    print(f"Public comment: {public_comment}")
    print(f"Personalised Pitch Message: {personalized_pitch_message}")
    try:
        if public_comment:
            ## Paste in comment box
            comment_box = driver.find_element(
                By.XPATH,
                "//textarea[@aria-label='Add a comment…' and @placeholder='Add a comment…']"
            )
            comment_box.click()
            pyperclip.copy(public_comment)
            actions.key_down(Keys.COMMAND).send_keys('v').key_up(Keys.COMMAND).perform()
            wait(3)
            ## Send
            post_button = driver.find_element(By.XPATH, "//div[@role='button' and text()='Post']")
            post_button.click()
            wait(3)
        if personalized_pitch_message:
            print("Sending personalized pitch message not implemented yet. Skipping for now...")
    except Exception as e:
        print("Could not send message or comment:", e)

def post_login_steps():
    mouse_click(mouse_position['explore_first_post']['x'], mouse_position['explore_first_post']['y'])

def start_explore_exploring():
    # Run
    # extract_mouse_location()
    explorer_page_link = "https://www.instagram.com/explore/"
    login(explorer_page_link, post_login_steps)
    processed_reel = {}
    for i in range(MAX_REELS):
        print(f"\n📽️ Explorer  {i + 1}/{MAX_REELS}")
        switch_user_if_needed(driver, explorer_page_link, post_login_steps)
        post_data = get_explorer_post_sentiment(driver)
        if post_data.get("score_out_of_10", 0) >= 7:
            print("Reaching out as score is above 7.")
            persist_in_excel(post_data)
            comment_or_send_message_in_explorer_post(driver, post_data)
        else:
            print("Skipping as score is below 8.", post_data)
        processed_reel[driver.current_url] = True
        # extract_top_level_comments(driver)
        swipe_to_next_post()
    driver.quit()
