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

AMAZON_CREDENTIAL = {
    'SELLER_ID': os.environ['SELLER_ID'],
    'ACCESS_KEY_ID': os.environ['ACCESS_KEY_ID'],
    'ACCESS_SECRET': os.environ['ACCESS_SECRET']
}

ASIN_list = ['B07MTZHCKF', 'B07H4KJTC9', 'B01KZB4FF4','B07F85WTS7']

class Product:
    # 全APIで使う変数
    DOMAIN   = 'mws.amazonservices.jp'
    ENDPOINT = '/Products/2011-10-01'

    def datetime_encode(dt):
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    timestamp = datetime_encode(datetime.datetime.utcnow())

    data = {
        'AWSAccessKeyId'  : AMAZON_CREDENTIAL['ACCESS_KEY_ID'],
        # 'Action'          : 'GetCompetitivePricingForASIN',
        'MarketplaceId'   : 'A1VC38T7YXB528',
        'SellerId'        : AMAZON_CREDENTIAL['SELLER_ID'],
        'SignatureMethod' : 'HmacSHA256',
        'SignatureVersion': '2',
        'Timestamp'       : timestamp,
        'Version'         : '2011-10-01'
    }

    def __init__(self, asin_list):
        self.asin_list = asin_list

    def enumerate_param(self, param, values):
        """
            Builds a dictionary of an enumerated parameter.
            Takes any iterable and returns a dictionary.
            ie.
            enumerate_param('MarketplaceIdList.Id', (123, 345, 4343))
            returns
            {
                MarketplaceIdList.Id.1: 123,
                MarketplaceIdList.Id.2: 345,
                MarketplaceIdList.Id.3: 4343
            }
        """
        params = {}
        if values is not None:
            if not param.endswith('.'):
                param = "%s." % param
            for num, value in enumerate(values):
                params['%s%d' % (param, (num + 1))] = value
        return params

    def get_competitive_pricing_for_asin(self):
        self.data['Action'] = 'GetCompetitivePricingForASIN'
        self.data.update(self.enumerate_param('ASINList.ASIN.', self.asin_list))
        return self.data

product = Product(ASIN_list)
print(product.get_competitive_pricing_for_asin())

"""
product = Product(ASIN_list)
result = [] || {}
product.get_matching_product_for_id()
product.get_lowest_offer_listings_for_asin()
product.get_competitive_pricing_for_asin()
"""





#
# for num in range(len(ASIN_list)):
#     index = str(num + 1)
#     data['ASINList.ASIN.' + index] = ASIN_list[num]
#
# query_string = '&'.join('{}={}'.format(
#     n, urllib.parse.quote(v, safe='')) for n, v in sorted(data.items()))
#
# canonical = "{}\n{}\n{}\n{}".format(
#     'POST', DOMAIN, ENDPOINT, query_string
# )
#
# h = hmac.new(
#     six.b(AMAZON_CREDENTIAL['ACCESS_SECRET']),
#     six.b(canonical), hashlib.sha256)
#
# signature = urllib.parse.quote(base64.b64encode(h.digest()), safe='')
#
# url = 'https://{}{}?{}&Signature={}'.format(
#     DOMAIN, ENDPOINT, query_string, signature)
#
# response = requests.post(url).content.decode()
#
# root = ET.fromstring(response)
#
# ns = {
#         'xmlns':'http://mws.amazonservices.com/schema/Products/2011-10-01',
#         'ns2'  :'http://mws.amazonservices.com/schema/Products/2011-10-01/default.xsd'
# }
#
# for product in root.findall('.//xmlns:Product', ns):
#
#     count = product.find('.//xmlns:OfferListingCount', ns)
#     print('' if count is None else count.text)
#
#
# def get_matching_product_for_id(asin_list:)
