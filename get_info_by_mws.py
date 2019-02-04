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
import pandas
from time import sleep

AMAZON_CREDENTIAL = {
    'SELLER_ID': os.environ['SELLER_ID'],
    'ACCESS_KEY_ID': os.environ['ACCESS_KEY_ID'],
    'ACCESS_SECRET': os.environ['ACCESS_SECRET']
}

asin_list = []
print('Paste ASIN List\nAnd pless "f" key to finish')

while True:
    asin = input()
    if asin == 'f':
        break
    else:
        asin_list.append(asin)

asin_set = list(set(asin_list))

print('list: ', asin_list)
print(len(asin_list))
print('set: ', asin_set)
print(len(asin_set))

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

    def __init__(self, asin_set):
        self.asin_set = asin_set

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
        data1.update(self.enumerate_param('IdList.Id.', self.asin_set))
        return self.make_url_and_get_response(data1)

    def get_lowest_offer_listings_for_asin(self):
        data2 = copy.deepcopy(self.data)
        data2['Action']        = 'GetLowestOfferListingsForASIN'
        data2.update(self.enumerate_param('ASINList.ASIN.', self.asin_set))
        return self.make_url_and_get_response(data2)

    def get_competitive_pricing_for_asin(self):
        data3 = copy.deepcopy(self.data)
        data3['Action']        = 'GetCompetitivePricingForASIN'
        data3.update(self.enumerate_param('ASINList.ASIN.', self.asin_set))
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
        result = {}
        for product in root.findall('.//xmlns:Product', self.ns):
            if 'GetCompetitivePricingForASIN' in root.tag:
                # ASIN
                asin = product.find('.//xmlns:ASIN', self.ns)
                asin = '' if asin is None else asin.text
                result[asin] = {'ASIN': asin}
                # condition=Any
                count_node = product.find('.//xmlns:OfferListingCount[@condition="Any"]', self.ns)
                count = 0 if count_node is None else int(count_node.text)
                result[asin] = {'出品者数': count}

            elif 'GetMatchingProductForId' in root.tag:
                # ASIN
                asin = product.find('.//xmlns:ASIN', self.ns)
                asin = '' if asin is None else asin.text
                result[asin] = {'ASIN': asin}
                # 商品名
                title = product.find('.//ns2:Title', self.ns)
                result[asin].update({'商品名': '' if title is None else product.text})

                # メーカ名
                manufacturer = product.find('.//ns2:Manufacturer', self.ns)
                result[asin].update({'メーカ名': '' if manufacturer is None else manufacturer.text})

                # メーカ型番
                model = product.find('.//ns2:Model', self.ns)
                result[asin].update({'メーカ型番': '' if model is None else model.text})

                # ブランド名
                brand = product.find('.//ns2:Brand', self.ns)
                result[asin].update({'ブランド名': '' if brand is None else brand.text})

                # 画像 (サムネ)
                image_url = product.find('.//ns2:URL', self.ns).text
                result[asin].update({'画像（サムネイル）': image_url})

                # 画像 (メイン)
                if '_SL75_.' in image_url:
                    main_url = image_url.replace('_SL75_.', '')
                else:
                    main_url = ''
                result[asin].update({'画像（メイン）': main_url})

                # 商品グループ
                product_group = product.find('.//ns2:ProductGroup', self.ns)
                result[asin].update({'商品グループ': '' if product_group is None else product_group.text})

                # 高さ (cm)
                height = product.find('.//ns2:Height', self.ns)
                result[asin].update({'高さ（cm）': '' if height is None else round(float(height.text)/0.3937, 2)})

                # 長さ (cm)
                length = product.find('.//ns2:Length', self.ns)
                result[asin].update({'長さ（cm）': '' if length is None else round(float(length.text)/0.3937, 2)})

                # 幅 (cm)
                width = product.find('.//ns2:Width', self.ns)
                result[asin].update({'幅（cm）': '' if width is None else round(float(width.text)/0.3937, 2)})

                # 重量 (kg)
                weight = product.find('.//ns2:Weight', self.ns)
                result[asin].update({'重量（kg）': '' if weight is None else round(float(weight.text)*453.59237, 2)})

                # 発売日
                release_date = product.find('.//ns2:ReleaseDate', self.ns)
                result[asin].update({'発売日': '' if release_date is None else release_date.text})

                # 最下位セールスランク
                rank_dict = {}
                for category, rank in zip(product.findall('.//xmlns:ProductCategoryId', self.ns), product.findall('.//xmlns:Rank', self.ns)):
                    if 'display_on_website' not in category.text:
                        rank_dict[category.text] = rank.text

                result[asin].update({'最下位カテゴリセールスランク': rank_dict})

            else:
                # ASIN
                asin = product.find('.//xmlns:ASIN', self.ns)
                asin = '' if asin is None else asin.text
                result[asin] = {'ASIN': asin}
                # FBAの新品最安値
                price_list = []
                # for price in product.findall('.//xmlns:ListingPrice/xmlns:Amount', self.ns):
                for price in product.findall('.//xmlns:LandedPrice/xmlns:Amount', self.ns):
                    price_list.append(price.text)

                result[asin] = {'最安値': min(price_list) if price_list else ''}
                # FBAではない新品最安値
                # 中古の最安値





        return result


quotient  = len(asin_set) // 5
print('quotient: ', quotient)
remainder = len(asin_set) % 5
print('remainder', remainder)
data = []

start = datetime.datetime.now()
print('start: ', start.strftime("%Y/%m/%d %H:%M:%S"))

counter = 0
product_info = {}
for asin in asin_set:
    product_info[asin] = {}

while counter < quotient:
    print(counter)
    print(quotient)
    print(asin_set[(counter * 5):(counter + 1)*5])

    get_product = Product(asin_set[(counter * 5):(counter + 1)*5])

    return_dic = get_product.get_competitive_pricing_for_asin()

    for id, dic in return_dic.items():
        product_info[id] = dic

    sleep(1)
    return_dic = get_product.get_matching_product_for_id()

    for id, dic in return_dic.items():
        product_info[id].update(dic)

    sleep(1)
    return_dic = get_product.get_lowest_offer_listings_for_asin()

    for id, dic in return_dic.items():
        product_info[id].update(dic)

    counter += 1

if remainder != 0:
    print('last')
    print(asin_set[-remainder:])
    get_product = Product(asin_set[-remainder:])

    return_dic = get_product.get_competitive_pricing_for_asin()

    for id, dic in return_dic.items():
        product_info[id] = dic

    sleep(1)
    return_dic = get_product.get_matching_product_for_id()

    for id, dic in return_dic.items():
        product_info[id].update(dic)

    sleep(1)
    return_dic = get_product.get_lowest_offer_listings_for_asin()

    for id, dic in return_dic.items():
        product_info[id].update(dic)



data = []
headers = ['ASIN','出品者数', '商品名', 'メーカ名', 'メーカ型番', 'ブランド名', '画像（サムネイル）', '画像（メイン）', '商品グループ', '高さ（cm）', '長さ（cm）', '幅（cm）', '重量（kg）', '発売日', '最下位カテゴリセールスランク', '最安値']
dict = {key:[] for key in headers}

for header in headers:
    for asin in asin_list:
        print(asin)
        if asin == '':
            dict[header].append('')
        else:
            dict[header].append(product_info[asin][header])


df = pandas.DataFrame(dict, columns=headers)
print(df)

# CSV ファイル (employee.csv) として出力
df.to_csv("product_info.csv")

print('Finish!')

stop = datetime.datetime.now()
print('stop: ', stop.strftime("%Y/%m/%d %H:%M:%S"))
print(stop - start)
