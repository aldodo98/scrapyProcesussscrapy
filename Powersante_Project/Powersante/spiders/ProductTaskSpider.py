import scrapy
import random
# from Powersante.items import Product
# from Powersante.itemloader import ProductItemLoader
from scrapy.http.headers import Headers
from scrapy_redis.spiders import RedisSpider
import json
import re
from Powersante.settings import BOT_NAME
# from datetime import datetime
# import datetime
from datetime import datetime
from Powersante.items import Product, AttributeBasicInfoClass, MappingClass, ProductAttributeClass, VariableClass
from Powersante.itemloader import ProductItemLoader, VariableClassItemLoader


class ProducttaskspiderSpider(RedisSpider):
# class ProducttaskspiderSpider(scrapy.Spider):
    name = 'ProductTaskSpider'
    redis_key = BOT_NAME + ':ProductTaskSpider'
    allowed_domains = ['www.powersante.com']

    # __init__方法必须按规定写，使用时只需要修改super()里的类名参数即可
    def __init__(self, *args, **kwargs):
        # 修改这里的类名为当前类名
        super(ProducttaskspiderSpider, self).__init__(*args, **kwargs)

    def make_request_from_data(self, data):
        receivedDictData = json.loads(str(data, encoding="utf-8"))
        # print(receivedDictData)
        # here you can use and FormRequest
        formRequest = scrapy.FormRequest(url=receivedDictData['ProductUrl'], dont_filter=True,
                                         meta={'TaskId': receivedDictData['Id']})
        return formRequest

    def parse(self, response):
        try:
            return self.parse_res(response=response)
        except Exception as err:
            print(err)

    def parse_res(self, response):
        product = Product()
        product['Success'] = response.status == 200
        if response.status == 200:
            product_itemloader = ProductItemLoader(item=product, response=response)
            product_itemloader.add_value('TaskId', response.meta['TaskId'])
            # product_itemloader.add_value('TaskId', 'XXXXXXXXXX')

            product_itemloader.add_value('Name', self.get_product_name(response))
            product_itemloader.add_value('ShortDescription', '')

            product_itemloader.add_value('FullDescription', self.get_product_desc(response))

            product_itemloader.add_value('Price', self.get_product_price(response))
            product_itemloader.add_value('OldPrice', '')

            product_itemloader.add_value(
                'ImageThumbnailUrl',
                response.css('div#gallery img::attr(data-large-src)').get())

            # product_itemloader.add_value(
            #     'ImageUrls', [])

            product_itemloader.add_value('LastChangeTime', datetime.utcnow().isoformat())
            product_itemloader.add_value('HashCode', '')
            loadItem = product_itemloader.load_item()
            # 暂时没有看到有选项的 size 或者 color 或者等等提供选项的
            product_attributes = self.get_product_attributes(response)
            loadItem['ImageUrls'] = self.get_img_urls(response)
            loadItem['ProductAttributes'] = product_attributes
            yield loadItem

    def get_product_name(self, response):
        result = ''
        title = response.css('div.price_note>h1>span::text').get()
        sub_title = response.css('div.price_note>h1::text').get()
        if title is not None:
            result = title
        if sub_title is not None:
            result += sub_title
        return result

    def get_product_desc(self, response):
        dr = re.compile(r'<[^>]+>', re.S)
        dd = dr.sub('', response.css('div.product_desc .description::text').get())

        return dd

    def get_product_price(self, response):
        regular_big_price = response.css('.price-box>.regular-price>span::text').get()
        regular_small_price = response.css('.price-box>.regular-price>span>small::text').get()
        if regular_small_price is not None:
            regular_small_price = regular_small_price.replace(' ', '')
        regular_price = (regular_big_price or '') + (regular_small_price or '')
        return regular_price

    def get_thumbnail_url(self, response):
        img = response[0]
        img_url = img.css('::attr(src)').get()
        return img_url

    def get_img_urls(self, response):
        urls = response.css('div#gallery_nav .item img')
        if urls is not None and (len(urls)>0):
            return ','.join(urls.css('::attr(src)').extract())
        else:
            return response.css('div#gallery img::attr(data-large-src)').get()

    def get_product_attributes(self, response):
        result = []
        # size_link_list = response.css('#dd_productSize li')
        # if len(size_link_list) > 0:
        #     size_attr = self.get_size_attribute(response, is_perfume=False)
        #     result.append(size_attr)
        #
        # color_list = response.css('#dd_productColour li')
        # if len(color_list) > 0:
        #     breadcrumb = response.css('.m-breadcrumb__items div')
        #     if breadcrumb[2].css('a::text').get() == 'PARFUMS':
        #         size_attr = self.get_size_attribute(response, is_perfume=True)
        #         result.append(size_attr)
        #     else:
        #         color_attr = self.get_color_attribute(response)
        #         result.append(color_attr)

        return result

    def get_size_attribute(self, response, is_perfume):
        # attributeBasicInfo
        attributeBasicInfo = AttributeBasicInfoClass()
        attributeBasicInfo['Name'] = "Size"
        attributeBasicInfo['Description'] = ""

        # mapping
        mapping = MappingClass()
        mapping['TextPrompt'] = "Size"
        mapping['IsRequired'] = True
        mapping['AttributeControlTypeId'] = 2
        mapping['AttributeControlType'] = "RadioList"
        mapping['DisplayOrder'] = 0
        mapping['DefaultValue'] = ""

        productSiteAttribute = ProductAttributeClass()
        productSiteAttribute['AttributeBasicInfo'] = attributeBasicInfo
        productSiteAttribute['Mapping'] = mapping
        productSiteAttribute['Variables'] = self.get_size_variables(response, is_perfume=is_perfume)

        return productSiteAttribute

    def get_color_attribute(self, response):
        # attributeBasicInfo
        attribute_basic_info = AttributeBasicInfoClass()
        attribute_basic_info['Name'] = "Color"
        attribute_basic_info['Description'] = ""

        # mapping
        mapping = MappingClass()
        mapping['TextPrompt'] = "Color"
        mapping['IsRequired'] = True
        mapping['AttributeControlTypeId'] = 2
        mapping['AttributeControlType'] = "RadioList"
        mapping['DisplayOrder'] = 0
        mapping['DefaultValue'] = ""

        product_site_attribute = ProductAttributeClass()
        product_site_attribute['AttributeBasicInfo'] = attribute_basic_info
        product_site_attribute['Mapping'] = mapping
        product_site_attribute['Variables'] = self.get_color_variables(response)

        return product_site_attribute

    def get_size_variables(self, response, is_perfume):
        lists = list()
        if is_perfume:
            lists = response.css('#dd_productColour li')
        else:
            lists = response.css('#dd_productSize li')

        result = []
        for item in lists:
            attribute_variable = VariableClass()
            variable_class_item_ioader = VariableClassItemLoader(item=attribute_variable, response=response)
            variable_class_item_ioader.add_value('DataCode', '')
            if is_perfume:
                global_price = response.css('span.o-product__title-price.prices strong::text').get()
                new_price = self.get_prefume_price(item.css('a::text').get()) or global_price
                variable_class_item_ioader.add_value('NewPrice', new_price)
                variable_class_item_ioader.add_value('Name',
                                                     self.get_prefume_name(''.join(item.css('a::text').getall())))
            else:
                variable_class_item_ioader.add_value('NewPrice', response.css(
                    'span.o-product__title-price.prices strong::text').get())
                variable_class_item_ioader.add_value('Name', item.css('::text').get())

            variable_class_item_ioader.add_value('OldPrice', '')
            variable_class_item_ioader.add_value('ColorSquaresRgb', '')
            variable_class_item_ioader.add_value('DisplayColorSquaresRgb', False)
            variable_class_item_ioader.add_value('PriceAdjustment', 0)
            variable_class_item_ioader.add_value('PriceAdjustmentUsePercentage', False)

            variable_class_item_ioader.add_value('IsPreSelected', len(item.css('::attr(aria-current)')) > 0)
            variable_class_item_ioader.add_value('DisplayOrder', False)
            variable_class_item_ioader.add_value('DisplayImageSquaresPicture', False)
            variable_class_item_ioader.add_value('PictureUrlInStorage', '')
            loadItem = variable_class_item_ioader.load_item()
            result.append(loadItem)
        return result

    def get_color_variables(self, response):
        list = response.css('#dd_productColour li')
        result = []
        for item in list:
            attribute_variable = VariableClass()
            variable_class_item_loader = VariableClassItemLoader(item=attribute_variable, response=response)
            variable_class_item_loader.add_value('DataCode', '')
            variable_class_item_loader.add_value('NewPrice',
                                                 response.css('span.o-product__title-price.prices strong::text').get())
            variable_class_item_loader.add_value('OldPrice', '')

            variable_class_item_loader.add_value('Name', ''.join(item.css('a::text').getall()))
            variable_class_item_loader.add_value('ColorSquaresRgb', self.main_url + item.css('img::attr(src)').get())
            variable_class_item_loader.add_value('DisplayColorSquaresRgb', False)
            variable_class_item_loader.add_value('PriceAdjustment', 0)
            variable_class_item_loader.add_value('PriceAdjustmentUsePercentage', False)

            variable_class_item_loader.add_value('IsPreSelected', len(item.css('::attr(aria-current)')) > 0)
            variable_class_item_loader.add_value('DisplayOrder', False)
            variable_class_item_loader.add_value('DisplayImageSquaresPicture', False)
            variable_class_item_loader.add_value('PictureUrlInStorage', '')
            loadItem = variable_class_item_loader.load_item()
            result.append(loadItem)
        return result

    @staticmethod
    def get_prefume_price(text):
        if text.replace('\n', '').strip() == '':
            return False
        return text.split('-')[1]

    @staticmethod
    def get_prefume_name(text):
        return text.split('-')[0]

