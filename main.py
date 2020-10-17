import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from telegram import Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from env import tg_token, tg_chats, tori_link

class Listing():
    def __init__(self, id, link, title, price, image, age, listingtype):
        self.id = id
        self.link = link
        self.title = title
        self.price = price
        self.image = image
        self.age = age
        self.listingtype = listingtype

listinglist = {}

def print_listing(listing):
    print(f'{listing.listingtype}, {listing.id}: {listing.price}, {listing.age}, {listing.title}')

def update_listinglist(bot, first_time):
    print('Updating at ' + str(datetime.now()))

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--log-level=3')
    driver = webdriver.Chrome(chrome_options=options)

    driver.get(tori_link)

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

        if id not in listinglist and not first_time:
            newlisting(bot, listing)

        listinglist[id] = listing

    driver.quit()

def newlisting(bot, listing):
    print_listing(listing)
    text = f'{listing.listingtype}: {listing.title}, {listing.price}, {listing.age}\n{listing.link}'
    for chat in tg_chats:
        bot.send_message(chat_id=chat, text=text)

def main():
    updater = Updater(tg_token, use_context=True)
    bot = Bot(tg_token)

    updater.start_polling()

    first_time = True

    while True:
        update_listinglist(bot, first_time)
        time.sleep(60)
        first_time = False

main()