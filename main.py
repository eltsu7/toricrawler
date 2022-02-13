import time
import sys
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from telegram import Bot
from telegram.error import TimedOut
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from env import tg_token, tg_chats, tori_link

pagelists = []
pages_to_keep = 3


class Listing():
    def __init__(self, id, link, title, price, image, age, listingtype):
        self.id = id
        self.link = link
        self.title = title
        self.price = price
        self.image = image
        self.age = age
        self.listingtype = listingtype


def print_listing(listing):
    # Console logging
    print(f'{listing.listingtype}, {listing.id}: {listing.price}, {listing.age}, {listing.title}')

def new_pagelist():
    # Read the page and pushes a new (dict)pagelist to (list)pagelists. Deletes old ones if pages_to_keep cap is met.

    print('Gathering new list at ' + str(datetime.now()))

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--log-level=3')
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(tori_link)
    except:
        return

    pagelist = {}

    items = driver.find_elements(By.CSS_SELECTOR, '[id^=item_]')
    for i in items:
        id = i.get_attribute('id')
        link = i.get_attribute('href')
        title = ''
        price = ''
        image = ''
        age = ''
        listingtype = ''

        try:
            title_element = i.find_element_by_class_name('li-title')
            title = title_element.text
        except NoSuchElementException:
            pass

        try:
            price_element = i.find_element(By.CSS_SELECTOR, '[class="list_price ineuros"]')
            price = price_element.text
        except NoSuchElementException:
            pass

        try:
            image_element = i.find_element_by_class_name('item_image')
            image = image_element.get_attribute('src')
        except NoSuchElementException:
            pass

        try:
            age_element = i.find_element_by_class_name('date_image')
            age = age_element.text
        except NoSuchElementException:
            pass

        try:
            listingtype_element = i.find_element_by_xpath(f'//*[@id="{id}"]/div[2]/div[2]/div/div[2]/p[2]')
            listingtype = listingtype_element.text
        except NoSuchElementException:
            pass

        listing = Listing(id, link, title, price, image, age, listingtype)

        pagelist[id] = listing

    global pagelists
    global pages_to_keep
    pagelists.insert(0, pagelist)

    if len(pagelist) > pages_to_keep:
        pagelists = pagelists[:pages_to_keep]

    driver.quit()
    print('Finished at ' + str(datetime.now()))

def announce_new_listings(bot, test, first_run):
    # Go through the latest pagelist and announce listings that aren't in the older ones.

    global pagelists
    for listing in pagelists[0]:
        found = False
        for old_page in pagelists[1:]:
            if listing in old_page:
                found = True
                break
        
        if not found and not first_run:
            send_listing_message(bot, pagelists[0][listing])
        elif test:
            send_listing_message(bot, pagelists[0][listing])
            test = False

def send_listing_message(bot, listing):
    # Sends message to telegram chat

    print_listing(listing)

    if listing.price:
        price = listing.price
    else:
        price = "-- €"

    if not listing.listingtype or not listing.title:
        return

    text = f'{listing.listingtype[0]}: {price}, {listing.title}, <a href="{listing.link}">Retkahda</a>'
    for chat in tg_chats:
        while True:
            try:
                bot.send_message(chat_id=chat, text=text, parse_mode="HTML")
                time.sleep(3)
            except TimedOut:
                time.sleep(5)
                continue
            break   

def main():
    updater = Updater(tg_token, use_context=True)
    bot = Bot(tg_token)

    updater.start_polling()

    # Don't announce anything on the first run
    first_run = True

    if len(sys.argv) == 2 and sys.argv[1] == 'test':
        test = True
    else:
        test = False

    while True:
        new_pagelist()
        announce_new_listings(bot, test, first_run)
        test = False
        first_run = False
        time.sleep(120)

main()
