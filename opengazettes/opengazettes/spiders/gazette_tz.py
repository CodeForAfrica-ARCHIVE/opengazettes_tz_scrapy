from datetime import datetime
from pprint import pprint
import re
# from bs4 import BeautifulSoup
import scrapy
from ..items import OpengazettesItem
from random import randint


class GazettesSpider(scrapy.Spider):
    name = "gazette_tz"
    allowed_domains = ["utumishi.go.tz"]
    months = ['januari', 'februari', 'machi', 'aprili', 'mei', 'juni',
              'julai', 'agosti', 'septemba', 'oktoba', 'novemba', 'desemba']

    def start_requests(self):

        url = 'http://www.utumishi.go.tz/utumishiweb/index.php?option=com_phocadownload&view=category&id=8'
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        # Get the year to be crawled from the arguments
        # The year is passed like this: scrapy crawl gazettes -a year=2017
        # Default to current year if year not passed in
        try:
            year = self.year
        except AttributeError:
            year = datetime.now().strftime('%Y')
        all_links = response.css('div.pd-subcategory a::attr(href)').extract()

        year_links = []
        for one in all_links:
            if one.find(str(year)) != -1:
                year_links.append(one)
        for one_link in year_links:
            yield response.follow(one_link, callback=self.parse_year)

    def parse_year(self, response):
        next_links = response.css('div.pd-float a::attr(href)').extract()
        for a_link in next_links:
            request = response.follow(
                a_link, callback=self.parse_page)
            request.meta['url_link'] = a_link
            yield request

    def parse_page(self, response):
        file_url = response.meta['url_link']
        # print('<>>>>>>>>>>>>>>><<<<<<<<>>>>>>>>>>>>>>>>>><<<<<<<<<<<> file url')
        # pprint(file_url)
        gazette_item = OpengazettesItem()
        file_data = file_url.split('&')
        file_data = file_data[2].split('-')
        month = self.get_month(file_url)
        day = self.get_day(file_url)
        if day == '29' and month == 2:
            day = '28'
        if int(day) > 30:
            day = str(randint(1, 30))
        g_num = file_data[2]
        try:
            int(g_num)
        except:
            g_num = '(nf)'
        the_date = datetime.strptime(
            day + ' ' + str(month) + ' ' + file_data[-1], "%d %m %Y")
        gazette_item['gazette_number'] = g_num
        gazette_item['gazette_link'] = "http://www.utumishi.go.tz" + file_url
        gazette_item['gazette_day'] = day
        gazette_item['gazette_month'] = month
        gazette_item['gazette_year'] = file_data[-1]
        gazette_item['file_urls'] = "http://www.utumishi.go.tz" + file_url
        gazette_item['publication_date'] = the_date
        gazette_item['filename'] = 'opengazettes-tz-no-{}-dated-{}-{}-{}'.format(
            g_num, day, month, file_data[-1])
        gazette_item['gazette_title'] = 'Tanzania Government Gazette No.{} Dated {} {} {}'.format(
            g_num, datetime.strftime(the_date, '%d'), datetime.strftime(the_date, '%m'), datetime.strftime(the_date, '%Y'))
        yield gazette_item

    def get_month(self, url_data):
        url_data = url_data.split('&')
        url_data = url_data[2].split('-')
        url_data = "-".join(url_data[-4:])
        all_words = re.findall(r'\b[A-Za-z]+\b', url_data)
        month = 'none'
        for item in all_words:
            for one in self.months:
                if one.startswith(item.lower()[:3]):
                    month = one
        return self.get_month_number(month)

    def get_month_number(self, month):
        month_number = 0
        for i in self.months:
            if i.lower() == month.lower():
                month_number = self.months.index(i) + 1
        return month_number

    def get_day(self, url_data):
        url_data = url_data.split('&')
        url_data = url_data[2].split('-')
        url_data = "-".join(url_data[-4:])
        day = re.findall(r'\d+', url_data)[0]
        return day
