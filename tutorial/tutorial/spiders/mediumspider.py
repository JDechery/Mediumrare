import scrapy
from tutorial.items import BlogPost
from scrapy.selector import Selector
import requests
from itertools import product
import pudb
from datetime import datetime, timedelta

def set_resolution(img_url, res=800):
    # print('img_url', img_url)
    # pudb.set_trace()
    parts = img_url.split('/')
    try:
        res_idx = parts.index('max')+1
        parts[res_idx] = str(res)
    except ValueError:
        res_idx = parts.index('fit')+2
        parts[res_idx] = str(res)
        parts[res_idx+1] = str(res)

    return '/'.join(parts)

def save_image(img_url, img_path):
    success = False
    with open(img_path,'wb') as f:
        response = requests.get(img_url)
        if response.status_code == 200:
            f.write(requests.get(img_url).content)
            success = True
    return success

def generate_archive_url(channels, years, months):
    base_url = 'https://www.medium.com/{}/archive/{}/{}'
    for (channel, yr, mo) in product(channels, years, months):
        yield base_url.format(channel, yr, mo)

class MediumSpider(scrapy.Spider):
    name = "mediumspider"

    def start_requests(self):
        # copy/pasted from https://toppub.xyz/
        # channel scrape
        # channels = ['backchannel', 'matter', 'the-mission', 'thewashingtonpost', 'swlh',
        #             'personal-growth', 'startup-grind', 'due', 'startupsco', 'google-design',
        #             'the-nib', 'human-parts', 'vantage', 'dailyjs', 'mother-jones',
        #             'thought-pills', 'slackjaw', 'facebook-design', 'synapse', 'cuepoint',
        #             'la-times', 'adventures-in-consumer-technology', 'hi-my-name-is-jon',
        #             'iotforall', 'the-happy-startup-school']
        # years = ['2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017']
        # months = ['%02d'%x for x in range(1,13)]
        # for url in generate_archive_url(channels, years, months):
        #     yield scrapy.Request(url=url,
        #                          meta = {},
        #                          callback=self.parse)
        start_url = 'https://www.medium.com/browse/top/'
        start_date = (2018, 1, 19)
        current_dt = datetime(*start_date)
        try:
            while True:
                medium_url = start_url + datetime(*start_date).strftime('%B-%d-%Y')
                current_dt = current_dt - timedelta(days=1)
                yield scrapy.Request(url=medium_url, callback=self.parse)
        except KeyboardInterrupt:
            print(current_date)

    def parse(self, response):
        post_urls = response.xpath("//div[contains(@class, 'postArticle-readMore')]/a/@href").extract()
        for url in post_urls:
            raw_url = url.split('?')[0]
            yield scrapy.Request(url=url, callback=self.parse_blog_data)

    def parse_blog_data(self, response):
        blogdata = BlogPost()

        blogdata['blog_url'] = response.url.split('?')[0]

        textcontent = response.xpath("//p/text()").extract()
        textcontent = '\n'.join(textcontent)
        blogdata['textcontent'] = textcontent

        # blogdata['title'] = response.xpath("//h1[contains(@class, 'title')]/text()").extract_first()
        title = response.xpath('//title/text()').extract_first()
        blogdata['title'] = title.split('–')[0]
        if len(title.split('-'))>1:
            blogdata['channel'] = title.split('-')[1]
        else:
            blogdata['channel'] = ''

        pub_date = response.xpath("//time[contains(@datetime,'')]/text()").extract_first()
        blogdata['pub_date'] = pub_date

        tags = r = response.xpath("//ul[contains(@class, 'tags')]/li/a/text()").extract()
        blogdata['tags'] = tags

        author = response.xpath("//div[contains(@class, 'u-lineHeightTightest')]/a/text()").extract_first()
        blogdata['author'] = author

        claps = response.xpath("//button[contains(@data-action, 'show-recommends')]/text()").extract_first()
        blogdata['claps'] = int(claps.replace('.','').replace('K','000'))

        img_url = response.xpath('//div/img/@src').extract_first()
        if not img_url:
            blogdata['img_url'] = ''
            blogdata['img_path'] = ''
        else:
            img_url = set_resolution(img_url)
            blogdata['img_url'] = img_url
            img_path = '/home/jdechery/Pictures/medium/' + blogdata['title'] + '.jpg'
            img_save_success = save_image(img_url, img_path)
            blogdata['img_path'] = img_path

        self.log(f'collected blog post {response.url}')
        return blogdata

# class BenButtonSpider(scrapy.Spider):
#     name = 'benjaminbutton'
#
#     def start_requests(self):
#         start_url = 'https://www.medium.com/top'
#         yield scrapy.Request(url=url,
#                              meta = {},
#                              callback=self.parse)
#
#
#     def parse(self, response):
#         post_urls = response.xpath("//div[contains(@class, 'postArticle-readMore')]/a/@href").extract()
#         for url in post_urls:
#             raw_url = url.split('?')[0]
#             yield scrapy.Request(url=url, callback=self.parse_blog_data)
