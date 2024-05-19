#!/usr/bin/env python3

import urllib3
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

http = urllib3.PoolManager()
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('rss')

def lambda_handler(event, context):
    articles = http.request('GET', URL)
    articlesSoup = BeautifulSoup(articles.data, 'lxml')
    
    lastItem = table.query(
        KeyConditionExpression=Key('source').eq(SOURCE),
        ScanIndexForward=False,
        Limit=1,
        ProjectionExpression='pubDate'
    )
    
    lastItemPubDate = 0
    if lastItem['Items']:
        lastItemPubDate = int(lastItem['Items'][0]['pubDate'])

    items = 0
    for art in articlesSoup.find_all('article', class_='newsList__article'):
        dateOpinions = art.find('div', class_='newsList__details')
        dateText = dateOpinions.find('span', class_='newsList__date').text.strip()
        dateTime = dateparser.parse(dateText, languages=['pl'])
        artTimestamp = int(dateTime.timestamp())
        if artTimestamp <= lastItemPubDate:
            break
        
        categoryA = art.find('div', class_='newsList__tag').find('a')
        category = ''
        if categoryA != None:
            category = categoryA.text.strip()
        if category.lower() not in SKIPPED_CATEGORIES:
            url = art.find('h4', class_='newsList__title').find('a').get('href')
            artId = int(url[-11:-5])
            title = art.find('h4', class_='newsList__title').find('span', class_='newsList__text').text.strip()
            opinionsText = '' if dateOpinions.find('b') == None else ', ' + dateOpinions.find('b').text + ' opinii'
            notSponsored = art.find('h4', class_='newsList__title').find('i', class_='trm-news-art-sponsorowany') == None
            sponsoredText = '' if notSponsored else ', SPONSOROWANY'
            author = '?'
            description = art.find('div', class_='newsList__content').find('p', class_='newsList__desc').text.strip()
            artTtl = artTimestamp + int(TTL)
            artDateId = artTimestamp*1000000+artId
            if notSponsored:
                articleFull = http.request('GET', url)
                articleFullSoup = BeautifulSoup(articleFull.data, 'lxml')
                authorDiv = articleFullSoup.find('div', class_='newsHeader__author')
                if authorDiv != None:
                    author = authorDiv.text.strip()
                descriptionP = articleFullSoup.find('p', class_='lead')
                if descriptionP != None:
                    description = descriptionP.text
            
            table.put_item(
                Item={
                    'source': SOURCE,
                    'timestamp#id': artDateId,
                    'title': title,
                    'link': url,
                    'description': description,
                    'author': author,
                    'summary': category + opinionsText + sponsoredText,
                    'category': category,
                    'pubDate': artTimestamp,
                    'ttl': artTtl
                }
            )
            items+=1
    
    return {
        'statusCode': 200,
        'insertedItems': items
    }
