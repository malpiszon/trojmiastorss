#!/usr/bin/env python3

import httpx
import asyncio
from bs4 import BeautifulSoup
import time
import os
import datetime
import dateparser
import boto3
from boto3.dynamodb.conditions import Key

URL = os.environ['URL']
SOURCE = os.environ['SOURCE']
SKIPPED_CATEGORIES = os.environ['SKIPPED_CATEGORIES'].split(',')
TTL = os.environ['TTL']

dynamodb = boto3.resource('dynamodb')
articlesTable = dynamodb.Table('rss_headers')


class Article:
    def __init__(self, url):
        self.url = url
        self.artId = int(self.url[-11:-5])
        self.timestamp = int(datetime.datetime.now().timestamp())
        self.artTtl = self.timestamp + int(TTL)
        self.author = '?'
        self.artDateTime = self.timestamp
        self.title = '?'
        self.description = '?'
        self.category = '?'
        self.opinionsText = ''
        self.notSponsored = True

    def get_summary(self):
        sponsoredText = '' if self.notSponsored else ', SPONSOROWANY'
        return self.category + self.opinionsText + sponsoredText


async def get_url_content(client, url):
    response = await client.get(url)
    if response.status_code == 103:
        print(f"103 Early Hint response for {url}, skipping...")
    elif not response.is_success:
        print(f'Error while reading {url}, status {articleFull.status_code}')
    else:
        return response.text

    return None


async def update_from_full_article(client, item):
    articleFull = await get_url_content(client, item.url)
    if articleFull != None:
        articleFullSoup = BeautifulSoup(articleFull, 'lxml')

        contentDiv = articleFullSoup.find('div', class_='newsContent')

        headerDiv = contentDiv.find('div', class_='component newsHeader')
        authorDiv = headerDiv.find('div', class_='newsHeader__author')

        if authorDiv != None:
            item.author = authorDiv.text.strip()

        dateDiv = headerDiv.find('div', class_='newsHeader__date')
        if dateDiv != None:
            dateTime = dateparser.parse(dateDiv.text, languages=['pl'])
            if dateTime != None:
                item.artDateTime = int(dateTime.timestamp())
        titleH = headerDiv.find('h1', class_='newsHeader__title')
        if titleH != None:
            item.title = titleH.text

        textDiv = contentDiv.find('div', class_='newsContent__text')

        descriptionP = textDiv.find('p', class_='lead')
        if descriptionP != None:
            item.description = descriptionP.text


async def update_items_from_articles(event, items):
    async with httpx.AsyncClient() as client:
        tasks = []
        for item in items:
            if item.notSponsored:
                tasks.append(asyncio.create_task(update_from_full_article(client, item)))
        await asyncio.gather(*tasks)


def lambda_handler(event, context):
    with httpx.Client() as client:
        articles = client.get(URL)

        if not articles.is_success:
            return {
                'statusCode': articles.status_code,
                'body': 'Error when reading the source URL',
                'errorUrl': URL
            }

    articlesSoup = BeautifulSoup(articles.text, 'lxml')
    processedArticles = {}
    for art in articlesSoup.find_all('article', class_='newsList__article'):
        url = art.find('h4', class_='newsList__title').find('a').get('href')
        item = Article(url)

        if len(processedArticles) == 0:
            firstItemId = item.artId

        if len(processedArticles) >= 8:  # TODO define variable
            break

        if item.artId in processedArticles:
            continue
        else:
            processedArticles[item.artId] = item

        try:
            dateOpinions = art.find('div', class_='newsList__details')
            dateText = dateOpinions.find('span', class_='newsList__date').text.strip()
            dateTime = dateparser.parse(dateText, languages=['pl'])
            item.artDateTime = int(dateTime.timestamp())

            categoryD = art.find('div', class_='newsList__tag')
            if categoryD != None and categoryD.find('a') != None:
                item.category = categoryD.find('a').text.strip()
            if item.category.lower() not in SKIPPED_CATEGORIES:
                item.title = art.find('h4', class_='newsList__title').find('span', class_='newsList__text').text.strip()
                item.opinionsText = '' if dateOpinions.find('b') == None else ', ' + dateOpinions.find(
                    'b').text + ' opinii'
                item.notSponsored = art.find('h4', class_='newsList__title').find('i',
                                                                                  class_='trm-news-art-sponsorowany') == None
                item.description = art.find('p', class_='newsList__desc').text.strip()
            else:
                del processedArticles[item.artId]

        except Exception as e:
            print(f'error while reading {url} due to {repr(e)}')
            return {
                'statusCode': 503,
                'body': repr(e),
                'errorUrl': url
            }

    asyncio.run(update_items_from_articles(event, processedArticles.values()))

    with articlesTable.batch_writer() as batch:
        for art in processedArticles.values():
            batch.put_item(Item={
                'source': SOURCE,
                'artId': art.artId,
                'timestamp': art.timestamp,
                'title': art.title,
                'link': art.url,
                'description': art.description,
                'author': art.author,
                'summary': art.get_summary(),
                'category': art.category,
                'artDateTime': art.artDateTime,
                'ttl': art.artTtl
            })

    return {
        'statusCode': 200,
        'insertedItems': len(processedArticles),
        'lastArticleId': firstItemId
    }
