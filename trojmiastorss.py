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
    for art in articlesSoup.find_all('li', class_='arch-item'):
        dateOpinions = art.find('span', class_='op-list')
        dateText = dateOpinions.text.strip().split('\xa0')[0].strip()
        dateTime = dateparser.parse(dateText, languages=['pl'])
        artTimestmap = int(dateTime.timestamp())
        if artTimestmap <= lastItemPubDate:
            break
        
        categoryA = art.find('div', class_='category').find('a')
        category = ''
        if categoryA != None:
            category = categoryA.text.strip()
        if category.lower() not in SKIPPED_CATEGORIES:
            url = art.find('a').get('href')
            artId = int(url[-11:-5])
            title = art.find('a', class_='color04').text.strip()
            opinionsText = '' if dateOpinions.find('strong') == None else ', ' + dateOpinions.find('strong').text + ' opinii'
            notSponsored = art.find('h4').find('i', class_='trm-news-art-sponsorowany') == None
            sponsoredText = '' if notSponsored else ', SPONSOROWANY'
            author = '?'
            description = art.find('div', class_='lead').text.strip()
            artTtl = artTimestmap + int(TTL)
            artDateId = artTimestmap*1000000+artId
            if notSponsored:
                articleFull = http.request('GET', url)
                articleFullSoup = BeautifulSoup(articleFull.data, 'lxml')
                authorSpan = articleFullSoup.find('span', class_='article-author')
                if authorSpan != None:
                    author = authorSpan.find('strong').text
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
                    'pubDate': artTimestmap,
                    'ttl': artTtl
                }
            )
            items+=1
    
    return {
        'statusCode': 200,
        'insertedItems': items
    }
