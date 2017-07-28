# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class OpengazettesItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    gazette_link = scrapy.Field()
    publication_date = scrapy.Field()
    gazette_number = scrapy.Field()
    file_urls = scrapy.Field()
    filename = scrapy.Field()
    gazette_title = scrapy.Field()
    gazette_day = scrapy.Field()
    gazette_month = scrapy.Field()
    gazette_year = scrapy.Field()
