import json
import math
from pathlib import PosixPath
import requests

import tkinter
from tkinter import Label, Button, filedialog, Menu

from PIL import Image, ImageTk, ImageFont, ImageDraw, ImageFont

from rich.console import Console
console = Console()

from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import NoSuchElementException

print("""
 ____              _ _             _   _      ____ _               _
|  _ \ _   _ _ __ (_| |_ __   __ _| |_| |__  / ___| |__   ___  ___| | _____ _ __
| |_) | | | | '_ \| | | '_ \ / _` | __| '_ \| |   | '_ \ / _ \/ __| |/ / _ | '__|
|  __/| |_| | |_) | | | |_) | (_| | |_| | | | |___| | | |  __| (__|   |  __| |
|_|    \__,_| .__/|_|_| .__/ \__,_|\__|_| |_ \____|_| |_|\___|\___|_|\_\___|_|
        |_|       |_|
""")

chromeOptions = Options()
chromeOptions.add_argument("--headless")

browser = webdriver.Chrome("./chromedriver.exe", options=chromeOptions)

def waitToBeClickable(byType, path):
    return WebDriverWait(browser, 10).until(expected_conditions.element_to_be_clickable((getattr(By, byType), path)))

with console.status("Working on tasks", spinner="bouncingBar"):
    try:
        browser.get("https://auth.ioeducation.com/users/sign_in")
    except:
        console.log("[red]An unkown error occured while attemping to connect with pupilpath website")
    else:
        console.log("[green]Established connection with pupilpath website")

    userInfoData = json.load(open("Storage/Data/UserInfo.json", encoding="utf-8"))

    data = [
        ("//*[@id='user_username']", userInfoData["PupilPathInfo"]["Username"]),
        ("//*[@id='user_password']", userInfoData["PupilPathInfo"]["Password"])
    ]

    for type, data in data:
        waitToBeClickable("XPATH", type).send_keys(data)

        waitToBeClickable("ID", "sign_in").click()

    browser.get("https://pupilpath.skedula.com/home/dashboard/")

    waitToBeClickable("ID", "sign_in").click()

    try:
        browser.find_element_by_xpath('//*[@id="messages"]/div')
    except NoSuchElementException:
        if browser.current_url == "https://auth.ioeducation.com/users/sign_in":
            console.log("[red]Username/Password is incorrect")

    waitToBeClickable("XPATH", '//*[@id="loginSKD"]/span[2]').click()

    console.log(f"Successfully Logged into {'[REDACTED]' if userInfoData['PupilPathInfo']['PrivateMode'] else userInfoData['PupilPathInfo']['Username']}")

    #Finished logging in now getting data
    gradeElement = browser.find_elements_by_xpath("//*[@id='progress-card']/tbody/tr")
    studentName = "Unknown User" if userInfoData["PupilPathInfo"]["PrivateMode"] else browser.find_element_by_xpath('/html/body/div[1]/div[1]/div/div/a[2]').text.split(": ")[1]

    studentData = {"title": [], "teacher": [], "department": [], "average": []}

    for i in (number + 1 for number in range(len(gradeElement))):
        
        elements = {
            "title": browser.find_element_by_xpath(f'//*[@id="progress-card"]/tbody/tr[{i}]/td[2]').text,

            "teacher": browser.find_element_by_xpath(f'//*[@id="progress-card"]/tbody/tr[{i}]/td[3]').text,

            "department": browser.find_element_by_xpath(f'//*[@id="progress-card"]/tbody/tr[{i}]/td[4]').text,

            "average": browser.find_element_by_xpath(f'//*[@id="progress-card"]/tbody/tr[{i}]/td[5]/span').text if browser.find_elements_by_xpath(f'//*[@id="progress-card"]/tbody/tr[{i}]/td[5]/span') else "-"
        }

        for element in elements:
            studentData[element].append(elements.get(element))

    browser.close()
    
    #Generating scorecard
    scoreTemp = Image.open("Storage/Scorecard/ScorecardTemplate.png")

    draw = ImageDraw.Draw(scoreTemp)

    boldFont = ImageFont.truetype("Storage/Fonts/Roboto-Bold.ttf", 30)

    coreUI = [
        ((115, 17), "Title", (30, 80)),
        ((360, 17), "Teacher", (350, 80)),
        ((605, 17), "Department", (610, 80)),
        ((905, 17), "Average", (930, 80)),
    ]
    
    draw.text((1170, 380), studentName, fill="white", font=boldFont)

    for position, title, valuePosition in coreUI:
        draw.text(position, title, fill="white", font=boldFont)
        
        if studentData[title.lower()]:
            text = "\n".join(studentData[title.lower()])

            draw.text(valuePosition, text=text, fill="white", font=ImageFont.truetype(f"Storage/Fonts/Roboto-{'Bold' if title == 'Average' else 'Light'}.ttf", 23))
    
    scoreCard = [
        ((1150, 450), "Classes: ", "p"),
        ((1300, 450), "Average: ", "p"),
        ((1450, 450), "Overall: ", "None")
    ]

    for position, text, value, valuePosition in scoreCard:
        draw.text(position, text=text, fill="white", font=ImageFont.truetype(f"Storage/Fonts/Roboto-Bold.ttf", 24))
        draw.text(valuePosition, text=value, fill="white", font=ImageFont.truetype(f"Storage/Fonts/Roboto-Light.ttf", 24))
        
    scoreTemp.save("Storage/TemporaryFiles/Scorecard.png")

#Displaying the image with a custom displayer
class ImageDisplay(tkinter.Tk):
    def __init__(self):
        tkinter.Tk.__init__(self)

        self.title(f"Student Name: {studentName} - {len(gradeElement)} Classes")
        self.resizable(False, False)

        scoreCard = ImageTk.PhotoImage(Image.open("Storage/TemporaryFiles/Scorecard.png"))

        label = Label(self, image=scoreCard)
        label.photo = scoreCard
        label.pack()

        console.log("[green]Successfully generated results")

ImageDisplay().mainloop()