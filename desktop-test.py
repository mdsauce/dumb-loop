from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import urllib, urllib.error
import threading
import socket
import queue
from selenium.common.exceptions import WebDriverException
from sauceclient import SauceClient
import random
import logging
import datetime
import time
import os, sys
THREADLIMIT = 5
TESTS = 5
username = os.environ.get('SAUCE_USERNAME')
access_key = os.environ.get('SAUCE_ACCESS_KEY')
sauce_client = SauceClient(username, access_key)
now = datetime.datetime.now()
logfileName = now.strftime('job-runner_%d-%m-%Y_%H-%M.log')
logging.basicConfig(filename=logfileName,level=logging.INFO)

def capsBuilder():
    testName = "Simple Desktop Test"
    platforms = ["Windows 10", "Windows 8.1", "Windows 7"]
    browsers = ["chrome", "firefox"]
    caps = {
        'platform': random.choice(platforms),
        'browserName': random.choice(browsers),
        'version': "latest",
        'seleniumVersion': "3.8.1",
        'name': testName
    }
    return caps

def randomTest(caps):
    try:
        driver = webdriver.Remote(command_executor="http://{}:{}@ondemand.saucelabs.com/wd/hub".format(username, access_key), desired_capabilities=caps)
    except urllib.error.URLError as u:
        logging.exception("Problem creating remote webdriver session. Potential DNS rate limiting.\n{}".format(u))
        return 1
    except socket.gaierror as s:
        logging.info("Problem creating remote webdriver session at the socket level. Potential DNS rate limiting.\n{}".format(s))
        return 1
    try: 
        driver.get("https://saucelabs.com")
        wait = WebDriverWait(driver, 45)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "site-container")))
        if driver.title != "Cross Browser Testing, Selenium Testing, and Mobile Testing | Sauce Labs":
            sauce_client.jobs.update_job(driver.session_id, passed=False)
            logging.info("Session {} failed".format(driver.session_id))
            session = driver.session_id
            driver.quit()
            return session
        driver.get("https://www.google.com/")
        query_input = wait.until(EC.presence_of_element_located((By.NAME, "q")))
        query_input.send_keys("Selenium Testing")
        query_input.send_keys(Keys.RETURN)
        selenium_url = wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Introduction — Selenium Documentation")))
        selenium_url.click()
        textbook_link = wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Test Design Considerations")))
        textbook_link.click()
        
        time.sleep(30)
        driver.get("https://www.google.com/")
        query_input = wait.until(EC.presence_of_element_located((By.NAME, "q")))
        time.sleep(30)
        query_input.send_keys("Selenium Testing")
        query_input.send_keys(Keys.RETURN)
        time.sleep(30)
        selenium_url = wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Introduction — Selenium Documentation")))
        time.sleep(30)
        selenium_url.click()
        time.sleep(30)
        textbook_link = wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Test Design Considerations")))
        textbook_link.click()
        time.sleep(30)

        time.sleep(30)
        driver.get("https://www.google.com/")
        query_input = wait.until(EC.presence_of_element_located((By.NAME, "q")))
        time.sleep(30)
        query_input.send_keys("Selenium Testing")
        query_input.send_keys(Keys.RETURN)
        time.sleep(30)
        selenium_url = wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Introduction — Selenium Documentation")))
        time.sleep(25)
        selenium_url.click()
        textbook_link = wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Test Design Considerations")))
        textbook_link.click()


        driver.get("https://www.google.com/")
        query_input = wait.until(EC.presence_of_element_located((By.NAME, "q")))
        query_input.send_keys("Selenium Testing")
        query_input.send_keys(Keys.RETURN)
        selenium_url = wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Introduction — Selenium Documentation")))
        selenium_url.click()
        textbook_link = wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Test Design Considerations")))
        textbook_link.click()


        driver.get("https://www.google.com/")
        query_input = wait.until(EC.presence_of_element_located((By.NAME, "q")))
        query_input.send_keys("Selenium Testing")
        query_input.send_keys(Keys.RETURN)
        selenium_url = wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Introduction — Selenium Documentation")))
        selenium_url.click()
        textbook_link = wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Test Design Considerations")))
        textbook_link.click()

        # hooray! the test passed
        sauce_client.jobs.update_job(driver.session_id, passed=True)  
        logging.info(f"Session {driver.session_id} passed")
        driver.quit()

    except:
        sauce_client.jobs.update_job(driver.session_id, passed=False)  
        logging.info(f"Session {driver.session_id} failed")
        driver.quit()
        return session
lock = threading.Lock()

def worker(q):
    global jobNumber
    global failedJobs
    while True:
        if q.empty():
            logging.info(f"Thread-{threading.current_thread().name} can't find any more work because the queue is empty.")
        # To get around the upstream DNS rate limit.
        # 12 seconds is OK for ~ 1500 jobs.  Only 1 error
        time.sleep(random.randrange(5,14))
        test = q.get()
        try:
            status = randomTest(test)
        except:
            logging.exception(f"Caught Exception: {sys.exc_info()}")
            with lock:
                if status != 0:
                    failedJobs+=1
                    print(f"Thread-{threading.current_thread().name} says: I might be blocking the .join()")
                    q.task_done()
                    logging.info(f"Thread-{threading.current_thread().name} has a failed job.")
                    if status != 1:
                        logging.info(f"Thread-{threading.current_thread().name} had failed session: {status}.")
        with lock:
            jobNumber+=1
            logging.info(f"Thread-{threading.current_thread().name} finished job number: {jobNumber}")
            print(f"Job {jobNumber} finished")
            q.task_done()

capsToTest = queue.Queue()
for i in range(TESTS):
    capsToTest.put(capsBuilder())

jobNumber = 0
failedJobs = 0

print(f"Logged to {logfileName}")

for i in range(THREADLIMIT):
    w = threading.Thread(name=i, target=worker, args=(capsToTest,))
    w.setDaemon(True)
    w.start()

capsToTest.join()
logging.info(f"Total Jobs Run: {TESTS}\nFailed Job Count: {failedJobs}")
print(f"Failed Jobs: {failedJobs}")
