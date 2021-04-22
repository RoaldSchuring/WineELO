import pandas as pd
import numpy as np

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

from bs4 import BeautifulSoup

import json
import time
import random

import pickle


options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--incognito')

driver = webdriver.Chrome(options=options)

driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source":
        "const newProto = navigator.__proto__;"
        "delete newProto.webdriver;"
        "navigator.__proto__ = newProto;"
})


# click the 'show more' button


def expand_show_more():
    show_more_button_visible = True
    while show_more_button_visible:
        show_more_button = driver.find_elements_by_class_name(
            'show-more')[-1].find_element_by_class_name('btn')
        if 'hidden' not in show_more_button.get_attribute('class'):
            driver.execute_script("arguments[0].click();", show_more_button)
            time.sleep(random.uniform(0, 5))
        else:
            show_more_button_visible = False

# use the number of stars per wine to calculate the rating


def calculate_rating(element):

    # a 100-pct icon means a full star in the rating
    full_stars = element.find_all('i', class_='icon-100-pct')
    nr_full_stars = len(full_stars)

    # a 50-pct icon means a half star in the rating
    half_stars = element.find_all('i', class_='icon-50-pct')
    nr_half_stars = len(half_stars)

    rating = nr_full_stars + 0.5*nr_half_stars

    return rating


# extract all the relevant information from each wine review
def grab_review_data(review):

    date_info = review.find('a', class_='link-muted bold inflate')
    review_date = date_info['title']
    review_time_ago = ' '.join(l for l in str(
        date_info.text).splitlines() if l)

    rating_element = review.find(
        'span', class_='rating rating-xs text-inline-block')
    rating = calculate_rating(rating_element)

    wine_id = review.find(
        'div', class_='activity-wine-card')['data-vintage-id']
    vintage = review.find(
        'div', class_='activity-wine-card')['data-year']

    wine_info = review.find('div', class_='wine-info')

    try:
        producer = wine_info.find(
            'span', class_='text-small').find('a', class_='link-muted').text
    except AttributeError:
        producer = np.nan
        pass

    wine_name = wine_info.find('a', class_='link-muted bold').text

    try:
        region_info = wine_info.find(
            'div', 'text-mini link-muted semi').find_all('a')
        region_name = region_info[0].text
        country_name = region_info[1].text
    except AttributeError:
        region_name = np.nan
        country_name = np.nan
        pass

    average_rating = review.find(
        'span', class_='header-large text-block').text.strip()
    nr_ratings = review.find(
        'span', class_='text-micro text-block').find('div', class_='row-no-gutter').text
    nr_ratings = [l for l in nr_ratings.splitlines() if l][0]

    review_info = {'wine_id': wine_id,
                   'review_date': review_date,
                   'review_time_ago': review_time_ago,
                   'vintage': vintage,
                   'rating': rating,
                   'wine_name': wine_name,
                   'producer': producer,
                   'region_name': region_name,
                   'country_name': country_name,
                   'average_rating': average_rating,
                   'nr_ratings': nr_ratings
                   }

    return review_info


def grab_user_id(soup):
    # grab the user name and ID
    user_info = soup.find(
        'div', class_='user-header__image-container__wrapper').find('div')['data-react-props']
    user_info_json = json.loads(user_info)
    user_id = user_info_json['user']['id']
    return user_id


def mine_review_data(user_link):
    user_link = 'https://www.vivino.com/' + user_link
    driver.get(user_link)
    expand_show_more()

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'lxml')

    reviews_selector = soup.find_all('div', class_='user-activity-item')
    if len(reviews_selector) >= 1:
        all_review_info = []
        for r in reviews_selector:
            review_info = grab_review_data(r)
            all_review_info.append(review_info)

        user_id = grab_user_id(soup)

        # write the scraped data to a json file
        filename = 'raw_data/' + str(user_id) + '.json'
        with open(filename, 'w') as outfile:
            json.dump(all_review_info, outfile)


def main():

    # driver.get('https://www.vivino.com/users/martijn-kra/rankings')

    # time.sleep(30)

    # for _ in range(100):
    #     show_more_button = driver.find_elements_by_class_name(
    #         'text-block.text-center.country-rankings-show-more.semi')[-1]
    #     driver.execute_script("arguments[0].click();", show_more_button)
    #     time.sleep(random.uniform(0, 5))

    # page_source = driver.page_source
    # soup = BeautifulSoup(page_source, 'lxml')

    # user_links = soup.find_all('span', class_='user-name header-smaller bold')
    # user_links = [u.find('a', class_='link-muted')['href'] for u in user_links]

    # with open("user_links.json", "w") as f:
    #     json.dump(user_links, f, indent=2)

    with open("user_links.json", 'r') as f:
        user_links = json.load(f)

    for u in user_links[41:500]:
        mine_review_data(u)
        time.sleep(random.uniform(10, 30))

    driver.close()


main()
