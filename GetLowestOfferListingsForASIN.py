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

ASIN_list = ['B07MTZHCKF', 'B01KZB4FF4','B07F85WTS7', 'B06Y3YLKP9']

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
    asin = product.find('.//xmlns:ASIN', ns).text
    price_list_new_amazon = []
    price_list_new_other  = []
    price_list_used       = []
    for LowestOfferListing in product.findall('.//xmlns:LowestOfferListing', ns):
        if LowestOfferListing.find('.//xmlns:ItemCondition', ns).text == 'New':
            if LowestOfferListing.find('.//xmlns:FulfillmentChannel', ns).text == 'Amazon':
                # FBS新品最安値
                price_list_new_amazon.append(LowestOfferListing.find('.//xmlns:LandedPrice/xmlns:Amount', ns).text)
            else:
                # FBAではない新品最安値
                price_list_new_other.append(LowestOfferListing.find('.//xmlns:LandedPrice/xmlns:Amount', ns).text)
        elif LowestOfferListing.find('.//xmlns:ItemCondition', ns).text == 'Used':
            # 中古の最安値
            price_list_used.append(LowestOfferListing.find('.//xmlns:LandedPrice/xmlns:Amount', ns).text)
    result[asin] = {'new_amazon': '' if not price_list_new_amazon else min(price_list_new_amazon),
                    'new_other' : '' if not price_list_new_other  else min(price_list_new_other),
                    'used'      : '' if not price_list_used       else min(price_list_used)
                    }

print(result)

    # result[asin] = {'最安値': min(price_list) if price_list else ''}
