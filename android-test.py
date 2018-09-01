from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import urllib
import threading
import socket
import queue
from selenium.common.exceptions import WebDriverException
from sauceclient import SauceClient
import random
import time
import os
THREADS = 10
TESTS = 14

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

def randomTest(caps):
    driver = webdriver.Remote(command_executor="https://%s:%s@ondemand.saucelabs.com/wd/hub" % (username, access_key), desired_capabilities=caps)
    try:
        driver.get("https://saucelabs.com")
        wait = WebDriverWait(driver, 45)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "site-container")))
        if driver.title == "Cross Browser Testing, Selenium Testing, and Mobile Testing | Sauce Labs":
            sauce_client.jobs.update_job(driver.session_id, passed=True)
            print(f"Session {driver.session_id} passed")
            return 0
        else:
            sauce_client.jobs.update_job(driver.session_id, passed=False)
            print(f"Session {driver.session_id} failed")
            return driver.session_id
    except WebDriverException as m:
        print(f"Session {driver.session_id} failed for a Web Driver Exception! https://saucelabs.com/beta/tests/{driver.session_id}\n{m}")
        sauce_client.jobs.update_job(driver.session_id, passed=False)
        session = driver.session_id
        return session
    except (urllib.error.URLError, urllib.error.HTTPError) as u:
        print(f"Session {driver.session_id} failed due to a Socket Exception! https://saucelabs.com/beta/tests/{driver.session_id}\n{u}")
        sauce_client.jobs.update_job(driver.session_id, passed=False)
        session = driver.session_id
        return session
    except (socket.timeout, socket.gaierror) as s:
        print(f"Session {driver.session_id} failed due to a Socket Exception! https://saucelabs.com/beta/tests/{driver.session_id}\n{s}")
        sauce_client.jobs.update_job(driver.session_id, passed=False)
        session = driver.session_id
        return session
    except TimeoutError as t:
        print(f"Session {driver.session_id} failed due to a Timeout Exception! https://saucelabs.com/beta/tests/{driver.session_id}\n{t}")
        sauce_client.jobs.update_job(driver.session_id, passed=False)
        session = driver.session_id
        return session
    finally:
        driver.quit()

lock = threading.Lock()

def worker(q):
    global jobNumber
    global failedJobs
    while True:
        if q.empty():
            print(f"Thread-{threading.current_thread().name} can't find any more work because the queue is empty.")
        status = randomTest(q.get())
        if status != 0:
            with lock:
                print(f"Thread-{threading.current_thread().name} has a failed job.  {status}")
                failedJobs+=1
        with lock:
            jobNumber+=1
            print(f"Thread-{threading.current_thread().name} finished job number: {jobNumber}")
        q.task_done()

capsToTest = queue.Queue()
for i in range(TESTS):
    capsToTest.put(capsBuilder())

jobNumber = 0
failedJobs = 0

for i in range(THREADS):
    w = threading.Thread(name=i, target=worker, args=(capsToTest,))
    w.setDaemon(True)
    w.start()
capsToTest.join()
print(f"Total Jobs Run: {TESTS}\nFailed Job Count: {failedJobs}")