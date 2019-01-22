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

ASIN_list = ['B07MTZHCKF', 'B07H4KJTC9', 'B01KZB4FF4','B07F85WTS7']

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
    'Action'          : 'GetMatchingProductForId',
    'MarketplaceId'   : 'A1VC38T7YXB528',
    'SellerId'        : AMAZON_CREDENTIAL['SELLER_ID'],
    'SignatureMethod' : 'HmacSHA256',
    'SignatureVersion': '2',
    'Timestamp'       : timestamp,
    'Version'         : '2011-10-01',
    'IdType'          : 'ASIN'
}

for num in range(len(ASIN_list)):
    index = str(num + 1)
    data['IdList.Id.' + index] = ASIN_list[num]

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

for product in root.findall('.//xmlns:Product', ns):

    result = {}



    # ASIN
    asin = product.find('.//xmlns:ASIN', ns).text
    result['ASIN'] = asin

    # 商品名
    title = product.find('.//ns2:Title', ns).text
    result['Title'] = title

    # メーカ名
    manufacturer = product.find('.//ns2:Manufacturer', ns).text
    result['Manufacturer'] = manufacturer

    # メーカ型番
    model = product.find('.//ns2:Model', ns)
    result['Model'] = '' if model is None else model.text

    # ブランド名
    brand = product.find('.//ns2:Brand', ns).text
    result['Brand'] = brand

    # 画像 (サムネ)
    image_url = product.find('.//ns2:URL', ns).text
    result['Image_URL'] = image_url

    # 画像 (メイン)
    if '_SL75_.' in image_url:
        main_url = image_url.replace('_SL75_.', '')
    else:
        main_url = ''
    result['Main_image_url'] = main_url


    # 商品グループ
    product_group = product.find('.//ns2:ProductGroup', ns).text
    result['Product Group'] = product_group

    # 高さ (cm)
    height = product.find('.//ns2:Height', ns).text
    result['Height (inched)'] = height

    # 長さ (cm)
    length = product.find('.//ns2:Length', ns)
    result['Length (inched)'] = '' if length is None else length.text

    # 幅 (cm)
    width = product.find('.//ns2:Width', ns)
    result['Width (inched)'] = '' if width is None else width.text

    # 重量 (kg)
    weight = product.find('.//ns2:Weight', ns)
    result['Weight (pound)'] = '' if weight is None else weight.text

    # 発売日
    release_date = product.find('.//ns2:ReleaseDate', ns)
    result['Release Date'] = '' if release_date is None else release_date.text

    # 最下位セールスランク
    rank_dict = {}
    for category, rank in zip(product.findall('.//xmlns:ProductCategoryId', ns), product.findall('.//xmlns:Rank', ns)):
        rank_dict[category.text] = rank.text

    result.update(rank_dict)

    for header, element in result.items():
        print(header, ' : ', element)
    print('\n')
