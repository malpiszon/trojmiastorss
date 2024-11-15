#!/usr/bin/env python3

import os
from rfeed import *
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key

VALID_SOURCES = os.environ['VALID_SOURCES'].split(',')

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('rss_headers')

def lambda_handler(event, context):
    if event == None or 'resource' not in event or len(event['resource']) < 2:
        return {
            'statusCode': 404
        }

    source = event['resource'][1:]
    if source not in VALID_SOURCES:
        return {
            'statusCode': 404
        }

    arts = table.query(
        KeyConditionExpression=Key('source').eq(source),
        ScanIndexForward=False,
        Limit=10
    )

    itemsToPublish = []
    for art in arts['Items']:
        item = Item(
            title = art['title'],
            link = art['link'],
            description = art['description'],
            creator = art['author'] + ' (' + art['summary'] + ')',
            comments = art['link'] + '#opinie',
            categories = [ art['category'] ],
            guid = Guid(art['link']),
            pubDate = datetime.fromtimestamp(art['artDateTime'])
        )
        itemsToPublish.append(item)

    feed = Feed(
        title = source,
        link = 'https://rss.malpiszon.net',
        description = 'Kanał RSS dla ' + source,
        language = 'pl-PL',
        lastBuildDate = datetime.now(),
        items = itemsToPublish
    )

    return {
        'statusCode': 200,
        'body': feed.rss()
    }
