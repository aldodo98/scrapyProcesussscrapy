import scrapy
import random
from Jacadi.items import Product
from Jacadi.itemloader import ProductItemLoader
from scrapy.http.headers import Headers
from scrapy_redis.spiders import RedisSpider
import json
from Jacadi.settings import BOT_NAME
from datetime import datetime
# import datetime
from datetime import datetime
from Jacadi.items import Product, AttributeBasicInfoClass, MappingClass, ProductAttributeClass, VariableClass
from Jacadi.itemloader import ProductItemLoader, VariableClassItemLoader


class ProductTaskSpider(RedisSpider):
# class ProductTaskSpider(scrapy.Spider):
    name = 'ProductTaskSpider'
    redis_key = BOT_NAME + ':ProductTaskSpider'
    allowed_domains = ['www.jacadi.fr']
    main_url = "https://www.jacadi.fr"

    # __init__方法必须按规定写，使用时只需要修改super()里的类名参数即可
    def __init__(self, *args, **kwargs):
        # 修改这里的类名为当前类名
        super(ProductTaskSpider, self).__init__(*args, **kwargs)

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

            product_itemloader.add_value('Name', response.css('.j-prd-description .j-title-epsilon::text').get())
            product_itemloader.add_value('ShortDescription', '')
            product_itemloader.add_value('FullDescription', response.css('#prd-tab-01>p::text').get())
            #
            product_itemloader.add_value('Price', response.css('.j-prd-description .j-pg.j-prd-price--after.smash-mb0::text').get())
            product_itemloader.add_value('OldPrice', '')
            #
            img_lis = response.css('div.j-prd-img img')

            product_itemloader.add_value(
                'ImageThumbnailUrl',
                self.get_thumbnail_url(img_lis))
            urls = self.get_img_urls(img_lis.css('::attr(src)').getall())
            # product_itemloader.add_value(
            #     'ImageUrls', list(urls))

            product_itemloader.add_value('LastChangeTime', datetime.utcnow())
            product_itemloader.add_value('HashCode', '')
            loadItem = product_itemloader.load_item()
            #
            product_attributes = self.get_product_attributes(response)
            if len(urls) > 0:
                urls = urls[:-1]
            loadItem['ImageUrls'] = urls
            loadItem['ProductAttributes'] = product_attributes
            yield loadItem

    def get_product_name(self, response):
        result = ''
        title = response.css('span.o-product__title-truncate.f-body--em::text').get()
        sub_title = response.css('span.o-product__title-truncate.f-body--em.s-multilines span')
        if title is not None:
            result = title
        if sub_title is not None:
            for sub in sub_title:
                result += sub.css('::text').get()
        return result

    def get_thumbnail_url(self, response):
        li = response[0]
        # print(li.get(), 888888888888888888)
        img_url = self.main_url + li.css('::attr(src)').get()
        # if img_url is None:
        #     return li.css('video').xpath('@src').get()
        return img_url

    def get_img_urls(self, urls):
        result = ''
        for url in urls:
            if self.main_url in url:
                result += url + ','
            else:
                result += self.main_url + url + ','

        return result

    def get_product_attributes(self, response):
        result = []
        size_link_list = response.css('.smash-reset.j-prd-sizes.js-size>label')
        if len(size_link_list) > 0:
            size_attr = self.get_size_attribute(response)
            result.append(size_attr)

        color_list = response.css('.smash-reset.j-prd-colors>label')
        if len(color_list) > 0:
            color_attr = self.get_color_attribute(response)
            result.append(color_attr)

        return result

    def get_size_attribute(self, response):
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
        productSiteAttribute['Variables'] = self.get_size_variables(response)

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

    def get_size_variables(self, response):
        lists = list()
        lists = response.css('.smash-reset.j-prd-sizes.js-size>label')

        result = []
        for item in lists:
            attribute_variable = VariableClass()
            variable_class_item_ioader = VariableClassItemLoader(item=attribute_variable, response=response)
            variable_class_item_ioader.add_value('DataCode', '')
            global_price = response.css('.j-prd-description .j-pg.j-prd-price--after.smash-mb0::text').get()
            variable_class_item_ioader.add_value('NewPrice', item.css('input::attr(data-price)').get() or global_price)
            variable_class_item_ioader.add_value('Name', item.css('.j-input--sizes').get())

            variable_class_item_ioader.add_value('OldPrice', '')
            variable_class_item_ioader.add_value('ColorSquaresRgb', '')
            variable_class_item_ioader.add_value('DisplayColorSquaresRgb', False)
            variable_class_item_ioader.add_value('PriceAdjustment', 0)
            variable_class_item_ioader.add_value('PriceAdjustmentUsePercentage', False)

            variable_class_item_ioader.add_value('IsPreSelected', len(item.css('.active')) > 0)
            variable_class_item_ioader.add_value('DisplayOrder', False)
            variable_class_item_ioader.add_value('DisplayImageSquaresPicture', False)
            variable_class_item_ioader.add_value('PictureUrlInStorage', '')
            loadItem = variable_class_item_ioader.load_item()
            result.append(loadItem)
        return result

    def get_color_variables(self, response):
        list = response.css('.smash-reset.j-prd-colors>label')
        result = []
        for item in list:
            attribute_variable = VariableClass()
            variable_class_item_loader = VariableClassItemLoader(item=attribute_variable, response=response)
            variable_class_item_loader.add_value('DataCode', '')
            global_price = response.css('.j-prd-description .j-pg.j-prd-price--after.smash-mb0::text').get()
            variable_class_item_loader.add_value('NewPrice', global_price)
            variable_class_item_loader.add_value('OldPrice', '')

            variable_class_item_loader.add_value('Name', item.css('img::attr(title)').get())
            color_squares_RGB = ''
            if item.css('img::attr(src)').get() is not None and item.css('img::attr(src)').get() != '':
                color_squares_RGB = self.main_url + item.css('img::attr(src)').get()
            variable_class_item_loader.add_value('ColorSquaresRgb', color_squares_RGB)
            variable_class_item_loader.add_value('DisplayColorSquaresRgb', False)
            variable_class_item_loader.add_value('PriceAdjustment', 0)
            variable_class_item_loader.add_value('PriceAdjustmentUsePercentage', False)

            variable_class_item_loader.add_value('IsPreSelected', len(item.css('.j-input--colors-active')) > 0)
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


