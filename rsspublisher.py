#!/usr/bin/env python3

from rfeed import *
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('rss')

def lambda_handler(event, context):
    arts = table.query(
        KeyConditionExpression=Key('source').eq('trojmiastopl'),
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
            pubDate = datetime.fromtimestamp(art['pubDate'])
        )
        itemsToPublish.append(item)
        
    feed = Feed(
        title = 'Trójmiasto.pl',
        link = 'https://rss.malpiszon.net',
        description = 'Kanał RSS dla Trójmiasto.pl',
        language = 'pl-PL',
        lastBuildDate = datetime.now(),
        items = itemsToPublish
    )


    return {
        'statusCode': 200,
        'body': feed.rss()
    }
