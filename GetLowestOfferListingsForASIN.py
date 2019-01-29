#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import datetime
import hashlib
import hmac
import urllib
import requests
import six
import xml.etree.ElementTree as ET
import os

B07H4KJTC9
B07MTZHCKF
B01KZB4FF4

B07F85WTS7



ASIN_list = ['B07MTZHCKF', 'B07MTZHCKF', 'B01KZB4FF4','B07F85WTS7']

AMAZON_CREDENTIAL = {
    'SELLER_ID': os.environ['SELLER_ID'],
    'ACCESS_KEY_ID': os.environ['ACCESS_KEY_ID'],
    'ACCESS_SECRET': os.environ['ACCESS_SECRET']
}

DOMAIN = 'mws.amazonservices.jp'
ENDPOINT = '/Products/2011-10-01'

def datetime_encode(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

timestamp = datetime_encode(datetime.datetime.utcnow())


data = {
    'AWSAccessKeyId': AMAZON_CREDENTIAL['ACCESS_KEY_ID'],
    'Action'          : 'GetLowestOfferListingsForASIN',
    'MarketplaceId'   : 'A1VC38T7YXB528',
    'SellerId'        : AMAZON_CREDENTIAL['SELLER_ID'],
    'SignatureMethod' : 'HmacSHA256',
    'SignatureVersion': '2',
    'Timestamp'       : timestamp,
    'Version'         : '2011-10-01',
}

for num in range(len(ASIN_list)):
    index = str(num + 1)
    data['ASINList.ASIN.' + index] = ASIN_list[num]

query_string = '&'.join('{}={}'.format(
    n, urllib.parse.quote(v, safe='')) for n, v in sorted(data.items()))

canonical = "{}\n{}\n{}\n{}".format(
    'POST', DOMAIN, ENDPOINT, query_string
)

h = hmac.new(
    six.b(AMAZON_CREDENTIAL['ACCESS_SECRET']),
    six.b(canonical), hashlib.sha256)

signature = urllib.parse.quote(base64.b64encode(h.digest()), safe='')

url = 'https://{}{}?{}&Signature={}'.format(
    DOMAIN, ENDPOINT, query_string, signature)

response = requests.post(url).content.decode()

root = ET.fromstring(response)

ns = {
        'xmlns':'http://mws.amazonservices.com/schema/Products/2011-10-01',
        'ns2'  :'http://mws.amazonservices.com/schema/Products/2011-10-01/default.xsd'
}

result = {}
for product in root.findall('.//xmlns:Product', ns):

    # 最安値
    price_list = []
    for price in product.findall('.//xmlns:ListingPrice/xmlns:Amount', ns):
        price_list.append(price.text)

    print(min(price_list) if price_list else '')
