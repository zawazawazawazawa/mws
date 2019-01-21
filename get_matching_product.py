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

ASIN = input('ASIN?: ')


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
    'Action'          : 'GetMatchingProduct',
    'MarketplaceId'   : 'A1VC38T7YXB528',
    'SellerId'        : AMAZON_CREDENTIAL['SELLER_ID'],
    'SignatureMethod' : 'HmacSHA256',
    'SignatureVersion': '2',
    'Timestamp'       : timestamp,
    'Version'         : '2011-10-01',
    'ASINList.ASIN.1' : ASIN
}

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

# ASIN
result['ASIN'] = ASIN

# 最下位セールスカテゴリランク

# 商品名
title = root.find('.//ns2:Title', ns).text
result['Title'] = title

# メーカ名
manufacturer = root.find('.//ns2:Manufacturer', ns).text
result['Manufacturer'] = manufacturer

# メーカ型番
model = root.find('.//ns2:Model', ns).text
result['Model'] = model

# ブランド名
brand = root.find('.//ns2:Brand', ns).text
result['Brand'] = brand

# 画像 (サムネ)
image_url = root.find('.//ns2:URL', ns).text
result['Image_URL'] = image_url

# 画像 (メイン)
if '_SL75_.' in image_url:
    result['Main_image_url'] = image_url.replace('_SL75_.', '')

# 商品グループ
product_group = root.find('.//ns2:ProductGroup', ns).text
result['Product Group'] = product_group

# 高さ (cm)
height = root.find('.//ns2:Height', ns).text
result['Height (inched)'] = height

# 長さ (cm)
length = root.find('.//ns2:Length', ns).text
result['Length (inched)'] = length

# 重量 (kg)
weight = root.find('.//ns2:Weight', ns).text
result['Weight (pound)'] = weight

for header, element in result.items():
    print(header, ' : ', element)