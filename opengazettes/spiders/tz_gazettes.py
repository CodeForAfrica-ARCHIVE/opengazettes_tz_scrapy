from datetime import datetime
import re
import scrapy
from bs4 import BeautifulSoup
from ..items import OpengazettesItem


class GazettesSpider(scrapy.Spider):
    name = "tz_gazettes_v2"
    allowed_domains = ["tanzania.go.tz"]
    months = [['january', 'januari'], ['february', 'februari'], ['march', 'machi'], ['april', 'aprili'], ['may', 'mei'], ['june', 'juni'],
              ['july', 'julai'], ['august', 'agosti'], ['september', 'septemba'], ['october', 'oktoba'], ['november', 'novemba'], ['december', 'desemba']]

    start_urls = ['https://tanzania.go.tz/home/pages/12']

    def parse(self, response):
        try:
            year = self.year
        except AttributeError:
            year = datetime.now().strftime('%Y')

        urls = ['https://tanzania.go.tz/home/pages/12', 'https://tanzania.go.tz/home/pages/12/20', 'https://tanzania.go.tz/home/pages/12/40', 'https://tanzania.go.tz/home/pages/12/60', 'https://tanzania.go.tz/home/pages/12/80',
                'https://tanzania.go.tz/home/pages/12/100', 'https://tanzania.go.tz/home/pages/12/120', 'https://tanzania.go.tz/home/pages/12/140', 'https://tanzania.go.tz/home/pages/12/160', 'https://tanzania.go.tz/home/pages/12/180', 'https://tanzania.go.tz/home/pages/12/200']
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_page, meta={'year': year})

    def parse_page(self, response):
        x = response.css('table.documents tr').extract()

        for i in x:
            if str(response.meta['year']) in i:
                soup = BeautifulSoup(i, 'html.parser')
                date = soup.find_all('td')[2:][0].string
                link = soup.find_all('td')[2:][1].find('a').get('href')
                gazette_item = OpengazettesItem()
                g_num = re.findall(r'\d+', link)
                if len(g_num) == 3:
                    g_num = g_num[0]
                else:
                    g_num = '(nf)'

                if not date or date == "":
                    date = link.split('/')
                    date = date[len(date) - 1]
                    g_day = re.findall(r'\d+', date)[0]
                    for pair in self.months:
                        for one in pair:
                            if one.lower() in date.lower():
                                g_month = self.get_month_number(one)
                else:
                    if len(re.findall(r'\b[A-Za-z]+\b', date)) < 1:
                        g_month = date.split("-")[1]
                        g_day = date.split("-")[2]
                    else:
                        g_month = self.get_month_number(
                            re.findall(r'\b[A-Za-z]+\b', date)[0])
                        
                        g_day = self.get_day(date)

                if str(g_day) == '29' and (str(g_month) == '2' or str(g_month) == '02'):
                    g_day = '28'

                the_date = datetime.strptime(
                    g_day + ' ' + g_month + ' ' + str(response.meta['year']), "%d %m %Y")

                gazette_item['gazette_link'] = link
                gazette_item['file_urls'] = [link]
                gazette_item['gazette_number'] = g_num
                gazette_item['gazette_year'] = response.meta['year']
                gazette_item['gazette_day'] = g_day
                gazette_item['gazette_month'] = g_month
                gazette_item['publication_date'] = the_date
                gazette_item['filename'] = 'opengazettes-tz-no-{}-dated-{}-{}-{}'.format(
                    g_num, g_day, g_month, str(response.meta['year']))
                gazette_item['gazette_title'] = 'Tanzania Government Gazette No.{} Dated {} {} {}'.format(
                    g_num, datetime.strftime(the_date, '%d'), datetime.strftime(the_date, '%m'), datetime.strftime(the_date, '%Y'))

                yield gazette_item

    def get_month_number(self, month):

        month = month.lower()
        for one_month in self.months:
            if month in one_month:
                return str(self.months.index(one_month) + 1)

    def get_day(self, date):
        return re.findall(r'\d+', date)[0]

    def next_page_link(self, response):
        next_page_links = response.css('#pagination a::text').extract()
        index_of_link = None
        for one in next_page_links:
            if one == '>':
                index_of_link = next_page_links.index(one)
        if not index_of_link:
            return None
        next_page_link = response.css('#pagination a::attr(href)').extract()[
            index_of_link]
        return next_page_link
