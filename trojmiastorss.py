#!/usr/bin/env python3

import urllib3
from bs4 import BeautifulSoup
from rfeed import *
import time
import datetime
import dateparser

rssLink = 'https://rss.malpiszon.net/trojmiasto.pl/'
url = 'https://www.trojmiasto.pl/wiadomosci/'
limit = 10
sleepInSeconds = 5
skippedCategories = ['sport', 'deluxe']
arts = []

http = urllib3.PoolManager()
articles= http.request('GET', url)
articlesSoup = BeautifulSoup(articles.data, 'lxml')

for index, art in zip(range(limit), articlesSoup.find_all('li', class_='arch-item')):
    categoryA = art.find('div', class_='category').find('a')
    category = ''
    if categoryA != None:
        category = categoryA.text.strip()
    if category.lower() not in skippedCategories:
        url = art.find('a').get('href')
        dateOpinions = art.find('span', class_='op-list')
        opinionsText = '' if dateOpinions.find('strong') == None else ', ' + dateOpinions.find('strong').text + ' opinii'
        notSponsored = art.find('h4').find('img', class_='art-sponsorowany') == None
        sponsoredText = '' if notSponsored else ', SPONSOROWANY'
        author = '?'
        description = art.find('div', class_='lead').text.strip()
        if notSponsored:
            articleFull = http.request('GET', url)
            articleFullSoup = BeautifulSoup(articleFull.data, 'lxml')
            authorSpan = articleFullSoup.find('span', class_='article-author')
            if authorSpan != None:
                author = authorSpan.find('strong').text
            descriptionP = articleFullSoup.find('p', class_='lead')
            description = ''
            if descriptionP != None:
                description = descriptionP.text
            time.sleep(sleepInSeconds)
        item = Item(
            title = art.find('a', class_='color04').text.strip(),
            link = url,
            description = description,
            creator = author + ' (' + category + opinionsText + sponsoredText + ')',
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

