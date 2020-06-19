#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from rfeed import *
import datetime
import dateparser

rssLink = 'https://rss.malpiszon.net/trojmiasto.pl/'
url = 'https://www.trojmiasto.pl/wiadomosci/'
skippedCategories = ['sport', 'deluxe']
arts = []

articles= requests.get(url)
articlesSoup = BeautifulSoup(articles.text, 'lxml')

for art in articlesSoup.find_all('li', class_='arch-item'):
    category = art.find('div', class_='category').find('a').text.strip()
    if category.lower() not in skippedCategories:
        url = art.find('a').get('href')
        dateOpinions = art.find('span', class_='op-list')
        opinions = '' if dateOpinions.find('strong') == None else ', ' + dateOpinions.find('strong').text + ' opinii'
        sponsored = '' if art.find('h4').find('img', class_='art-sponsorowany') == None else ', SPONSOROWANY'
        item = Item(
            title = art.find('a', class_='color04').text.strip(),
            link = url,
            description = art.find('div', class_='lead').text.strip(),
            creator = 'Trojmiasto.pl (' + category + opinions + sponsored + ')',
            comments = url + '#opinions-wrap',
            categories = [ category ],
            guid = Guid(art.find('a').get('href')),
            pubDate = dateparser.parse(dateOpinions.text.strip().splitlines()[0].strip(), languages=['pl'])
        )
        arts.append(item)

feed = Feed(
    title = 'Trójmiasto.pl',
    link = rssLink,
    description = 'Kanał RSS dla Trójmiasto.pl',
    language = 'pl-PL',
    lastBuildDate = datetime.datetime.now(),
    items = arts
)

print(feed.rss())

