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
import copy

AMAZON_CREDENTIAL = {
    'SELLER_ID': os.environ['SELLER_ID'],
    'ACCESS_KEY_ID': os.environ['ACCESS_KEY_ID'],
    'ACCESS_SECRET': os.environ['ACCESS_SECRET']
}

# max 10
ASIN_list = ['B07MTZHCKF', 'B07H4KJTC9', 'B01KZB4FF4','B07F85WTS7']
print(ASIN_list)

class Product:
    # 全APIで使う変数
    DOMAIN   = 'mws.amazonservices.jp'
    ENDPOINT = '/Products/2011-10-01'

    ns = {
        'xmlns':'http://mws.amazonservices.com/schema/Products/2011-10-01',
        'ns2'  :'http://mws.amazonservices.com/schema/Products/2011-10-01/default.xsd'
    }

    def datetime_encode(dt):
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    timestamp = datetime_encode(datetime.datetime.utcnow())

    data = {
        'AWSAccessKeyId'  : AMAZON_CREDENTIAL['ACCESS_KEY_ID'],
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

    def get_matching_product_for_id(self):
        data1 = copy.deepcopy(self.data)
        data1['Action'] = 'GetMatchingProductForId'
        data1['IdType'] = 'ASIN'
        data1.update(self.enumerate_param('IdList.Id.', self.asin_list))
        print(data1)
        return self.make_url_and_get_response(data1)
    #
    # def get_lowest_offer_listings_for_asin(self):

    def get_competitive_pricing_for_asin(self):
        data3 = copy.deepcopy(self.data)
        data3['Action']        = 'GetCompetitivePricingForASIN'
        data3.update(self.enumerate_param('ASINList.ASIN.', self.asin_list))
        return self.make_url_and_get_response(data3)

    def make_url_and_get_response(self, data):
        query_string = '&'.join('{}={}'.format(
            n, urllib.parse.quote(v, safe='')) for n, v in sorted(data.items()))

        canonical = "{}\n{}\n{}\n{}".format(
            'POST', self.DOMAIN, self.ENDPOINT, query_string
        )

        h = hmac.new(
            six.b(AMAZON_CREDENTIAL['ACCESS_SECRET']),
            six.b(canonical), hashlib.sha256)

        signature = urllib.parse.quote(base64.b64encode(h.digest()), safe='')

        url = 'https://{}{}?{}&Signature={}'.format(
            self.DOMAIN, self.ENDPOINT, query_string, signature)

        response = requests.post(url).content.decode()

        root = ET.fromstring(response)

        return self.get_list(root)

    def get_list(self, root):
        count_list = []
        for product in root.findall('.//xmlns:Product', self.ns):
            if 'GetCompetitivePricingForASIN' in root.tag:
                # condition=Any
                count_node = product.find('.//xmlns:OfferListingCount[@condition="Any"]', self.ns)
                count = 0 if count_node is None else int(count_node.text)
                count_list.append(count)
                return count_list

            elif 'GetMatchingProductForId' in root.tag:
                result = {}
                # 商品名
                title = product.find('.//ns2:Title', self.ns).text
                result['Title'] = title

                # メーカ名
                manufacturer = product.find('.//ns2:Manufacturer', self.ns).text
                result['Manufacturer'] = manufacturer

                # メーカ型番
                model = product.find('.//ns2:Model', self.ns)
                result['Model'] = '' if model is None else model.text

                # ブランド名
                brand = product.find('.//ns2:Brand', self.ns).text
                result['Brand'] = brand

                # 画像 (サムネ)
                image_url = product.find('.//ns2:URL', self.ns).text
                result['Image_URL'] = image_url

                # 画像 (メイン)
                if '_SL75_.' in image_url:
                    main_url = image_url.replace('_SL75_.', '')
                else:
                    main_url = ''
                result['Main_image_url'] = main_url


                # 商品グループ
                product_group = product.find('.//ns2:ProductGroup', self.ns).text
                result['Product Group'] = product_group

                # 高さ (cm)
                height = product.find('.//ns2:Height', self.ns).text
                result['Height (inched)'] = height

                # 長さ (cm)
                length = product.find('.//ns2:Length', self.ns)
                result['Length (inched)'] = '' if length is None else length.text

                # 幅 (cm)
                width = product.find('.//ns2:Width', self.ns)
                result['Width (inched)'] = '' if width is None else width.text

                # 重量 (kg)
                weight = product.find('.//ns2:Weight', self.ns)
                result['Weight (pound)'] = '' if weight is None else weight.text

                # 発売日
                release_date = product.find('.//ns2:ReleaseDate', self.ns)
                result['Release Date'] = '' if release_date is None else release_date.text

                # 最下位セールスランク
                rank_dict = {}
                for category, rank in zip(product.findall('.//xmlns:ProductCategoryId', self.ns), product.findall('.//xmlns:Rank', self.ns)):
                    rank_dict[category.text] = rank.text

                result.update(rank_dict)

                for header, element in result.items():
                    print(header, ' : ', element)
                print('\n')

get_product = Product(ASIN_list)
# print(product.get_competitive_pricing_for_asin())
get_product.get_matching_product_for_id()

"""
product = Product(ASIN_list)
result = [] || {}
product.get_matching_product_for_id()
product.get_lowest_offer_listings_for_asin()
product.get_competitive_pricing_for_asin()
"""
