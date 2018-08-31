from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from sauceclient import SauceClient
import random
import time
import os

username = os.environ.get('SAUCE_USERNAME')
access_key = os.environ.get('SAUCE_ACCESS_KEY')
sauce_client = SauceClient(username, access_key)


def capsBuilder():
    testName = "Simple Bulk Test"
    androidEmulatorVersions = ["4.4", "5.0", "5.1", "6.0"]
    caps = {
        'deviceName': "Android Emulator",
        'browserName': "Browser",
        'version': "latest",
        'platformName': "Android",
        'platformVersion': random.choice(androidEmulatorVersions),
        'name': testName
    }
    return caps
desired_caps = capsBuilder()

try: 
    driver = webdriver.Remote(command_executor="https://%s:%s@ondemand.saucelabs.com/wd/hub" % (username, access_key), desired_capabilities=desired_caps)
    driver.get("https://saucelabs.com")
    if driver.title == "Cross Browser Testing, Selenium Testing, and Mobile Testing | Sauce Labs":
        sauce_client.jobs.update_job(driver.session_id, passed=True)
        print(f"Session {driver.session_id} passed")
    else:
        sauce_client.jobs.update_job(driver.session_id, passed=False)
        print(f"Session {driver.session_id} failed")
except WebDriverException as m:
        print(f"Session {driver.session_id} failed for some reason!")
        sauce_client.jobs.update_job(driver.session_id, passed=False)
        print(m)
        driver.quit()

driver.quit()
