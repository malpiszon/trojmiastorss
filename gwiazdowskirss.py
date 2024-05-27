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
FULL_TEXT_URL_DOMAIN = os.environ['FULL_TEXT_URL_DOMAIN']
AUTHOR = os.environ['AUTHOR']
SOURCE = os.environ['SOURCE']
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
    for art in articlesSoup.find_all('li', class_='is-1z3'):
        artData = art.find('a', class_='tile-magazine-title-url')
        url = artData.get('href')
        title = artData.text.strip()
        categoryA = art.find('a', class_='tile-magazine-category')
        category = '?'
        if categoryA != None:
            category = categoryA.text.strip()
        author = AUTHOR
        
        # fetch more info from the article itself
        fullUrl = FULL_TEXT_URL_DOMAIN + url
        articleFull = http.request('GET', fullUrl)
        articleFullSoup = BeautifulSoup(articleFull.data, 'lxml')
        descriptionM = articleFullSoup.find('meta', attrs={'name': 'Description'})
        description = descriptionM['content']
        artInfoBox = articleFullSoup.find('div', class_='article-info-box')
        artDateD = artInfoBox.find('div', class_='article-date')
        dateTime = dateparser.parse(artDateD.meta['content'])
        artTimestmap = int(dateTime.timestamp())

        if artTimestmap <= lastItemPubDate:
            break
        
        artId = int(url[-7])
        artTtl = artTimestmap + int(TTL)
        artDateId = artTimestmap*1000000+artId
        
        table.put_item(
            Item={
                'source': SOURCE,
                'timestamp#id': artDateId,
                'title': title,
                'link': fullUrl,
                'description': description,
                'author': author,
                'summary': category.capitalize(),
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
