# -*- coding: utf-8 -*-

import os

# Scrapy settings for catalog_crawlers project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

# BOT_NAME = "Gustelle's Bot"

SPIDER_MODULES = ['estate_agents.spiders']
NEWSPIDER_MODULE = 'estate_agents.spiders'

# do not log to much
LOG_LEVEL = 'INFO'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'catalog_crawlers (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Randomozing the delay to download reduces the risk of being banned
RANDOMIZE_DOWNLOAD_DELAY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = str(max([2, int('0' + os.getenv('CRAWLER_CONC_REQUESTS', default="2"))]))

# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = str(max([4, int('0' + os.getenv('CRAWLER_CONC_REQUESTS_PER_DOMAIN', default="4"))]))
CONCURRENT_REQUESTS_PER_IP = str(max([2, int('0' + os.getenv('CRAWLER_CONC_REQUESTS_PER_IP', default="2"))]))

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# inspired by DeltaFetch
# SPIDER_MIDDLEWARES = {
#     'catalog_crawlers.middlewares.DeltaFetch': None
# }
# DELTAFETCH_CACHE_DIR = '.'

# Activate the proxycrawl middleware
# for IP rotation
PROXYCRAWL_ENABLED = False #os.getenv('PROXYCRAWL_ENABLED')

# The ProxyCrawl API token you wish to use, either normal of javascript token
PROXYCRAWL_TOKEN = os.getenv('PROXYCRAWL_TOKEN')

# thank you https://github.com/alecxe/scrapy-fake-useragent
DOWNLOADER_MIDDLEWARES = {
    'random_useragent.RandomUserAgentMiddleware': 100,
    # 'scrapy_proxycrawl.ProxyCrawlMiddleware': 200
}

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
	'estate_agents.pipelines.JsonSchemaValidatePipeline': 100,
	'estate_agents.pipelines.HttpPipeline': 200,
	'estate_agents.pipelines.OnClosePipeline': 300
}

# send the item to the following URL
# ON_PROCESS_ITEM = 'http://142.93.186.90:1378/products'
ON_PROCESS_ITEM = os.getenv('ON_PROCESS_ITEM', default='http://127.0.0.1:8000/reps')

# if set to True, items crawled and marked as "dirty" will not be sent to the URL 'ON_PROCESS_ITEM'
# default is False
SKIP_DIRTY_ITEMS = True

# this Zone information is used by the backend app receiving items
# it is used to define the index name in which to store the data
ZONE = 'mel'

# Enable and configure HTTP caching (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
HTTPCACHE_ENABLED = False
# HTTPCACHE_DIR = '/app/data/scrapy_cache'

# log scraping exceptions into sentry
SENTRY_DSN = os.getenv('SENTRY_DSN')
EXTENSIONS = {
    "scrapy_sentry.extensions.Errors":10,
}
