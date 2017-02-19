# coding=utf-8

import os
import sys
import urllib2
import boto3
import json
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

S3_DATA_BUCKET = os.environ["S3_DATA_BUCKET"]
RSS_FEED_URL = os.environ["FEED_URL"]

s3 = boto3.resource("s3")
bucket = s3.Bucket(S3_DATA_BUCKET)


def raw_text(text):
    t = BeautifulSoup(text, "html.parser").get_text()
    return t.replace(u"\xa0", " ").replace(u"\u2019", "\'")

def load_feed():
    rss_feed = urllib2.urlopen(RSS_FEED_URL)
    rss_feed = BeautifulSoup(rss_feed, "html.parser")

    published_after = datetime.now() + timedelta(days=-5)
    news = []
    print(published_after)
    for item in rss_feed.find_all("item"):
        pub_date = datetime.strptime(item.find("pubdate").string, "%a, %d %b %Y %H:%M:%S +0000")
        print(pub_date)
        if pub_date < published_after:
            continue

        item = {
            "uid": item.find("guid").string,
            "updateDate": "{}.0Z".format(pub_date.strftime("%Y-%m-%dT%H:%M:%S")),
            "titleText": raw_text(item.find("title").get_text()),
            "mainText": raw_text(item.find("description").get_text()),
            "redirectionUrl": item.find("link").string
        }
        news.append(item)

    return news

def export_news_data(items):
    obj = bucket.Object("flash_briefing.json")
    response = obj.put(
        ACL="public-read",
        Body=json.dumps(items, ensure_ascii=False),
        ContentEncoding="utf-8",
        ContentType="application/json"
    )
    print(response)

def lambda_handler(event, context):
    news = load_feed()
    export_news_data(news)

if __name__ == '__main__':
    sys.exit(lambda_handler(None, None))
