import scrapy

class GazettesSpider(scrapy.Spider):
    name = "gazette_tz"
    allowed_domains = ["utumishi.go.tz"]
