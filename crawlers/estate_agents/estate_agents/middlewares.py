# sorry but I'm fed up with dependencies, so I imported some nice middlewares here
import os
import sys
import errno
import os

import logging
from fake_useragent import UserAgent

import time

from scrapy.http import Request
from scrapy.item import BaseItem
from scrapy.utils.request import request_fingerprint
from scrapy.utils.python import to_bytes
from scrapy.exceptions import NotConfigured
from scrapy import signals

import pickle

logger = logging.getLogger(__name__)


# Here is the awesome RandomUserAgent middleware found here
# https://github.com/alecxe/scrapy-fake-useragent/blob/master/scrapy_fake_useragent/middleware.py

class RandomUserAgentMiddleware(object):
    def __init__(self, crawler):
        super(RandomUserAgentMiddleware, self).__init__()

        self.ua = UserAgent()
        self.per_proxy = crawler.settings.get('RANDOM_UA_PER_PROXY', False)
        self.proxy2ua = {}

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        logger.debug('RandomUserAgentMiddleware process_request : {}'.format(request))
        if self.per_proxy:
            proxy = request.meta.get('proxy')
            if proxy not in self.proxy2ua:
                self.proxy2ua[proxy] = self.ua.random
                logger.debug('Assign User-Agent %s to Proxy %s'
                             % (self.proxy2ua[proxy], proxy))
            request.headers.setdefault('User-Agent', self.proxy2ua[proxy])
        else:
            rand = self.ua.random
            logger.debug('User-Agent : {}'.format(rand))
            request.headers.setdefault('User-Agent', rand)


# This is the nice DeltaFetch middleware provided by
# https://github.com/scrapy-plugins/scrapy-deltafetch/blob/master/scrapy_deltafetch/middleware.py
# I adapted it to use a standard file instead of the bsddb3,
# because I wanted to limitate deps
# indeed, DeltaFetch depends on bsddb3 which depends on Java for example

class DeltaFetch(object):
    """
    This is a spider middleware to ignore requests to pages containing items
    seen in previous crawls of the same spider, thus producing a "delta crawl"
    containing only new items.
    This also speeds up the crawl, by reducing the number of requests that need
    to be crawled, and processed (typically, item requests are the most cpu
    intensive).
    """
    def __init__(self, reset, cache_dir, stats=None, spider_name='crawler'):
        """
        the init method is called with additional params through the 
        from_crawler classmethod
        """
        self.reset = reset
        self.cache_dir = cache_dir
        self.stats = stats
        # the spider_name will be used as cache name
        # in order to have a cache per spider for perf issues
        # and also because sometimes we want to reset the cache
        # for one spider, not for all the spiders
        self.spider_name = spider_name

    @classmethod
    def from_crawler(cls, crawler):
        s = crawler.settings
        reset = s.getbool('DELTAFETCH_RESET', False)

        # default cache dir
        default_cache_dir = os.path.abspath(
                                os.path.join(
                                    os.path.dirname(os.path.realpath(__file__)), 'cache'))

        cache_dir = s.get('DELTAFETCH_CACHE_DIR', default_cache_dir)
        logger.info('Using DELTAFETCH_CACHE_DIR: {}'.format(cache_dir))
        
        # pass the spider name and other params here
        o = cls(reset, cache_dir, crawler.stats, crawler.spider.__class__.__name__)
        crawler.signals.connect(o.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(o.spider_closed, signal=signals.spider_closed)
        return o

    def spider_closed(self, spider):
        try:
            with open(self.shelve_path, 'wb') as f:
                pickle.dump(self.shelve, f, protocol=2)
        except:
            logger.error('Error persisting the cache {}'.format(sys.exc_info()[0]))


    def spider_opened(self, spider):
        reset = self.reset or getattr(spider, 'deltafetch_reset', False)

        self.shelve_path = os.path.abspath(os.path.join(self.cache_dir, self.spider_name))

        if reset:  
            try:
                os.remove(self.shelve_path)
            except OSError as e:
                logger.error('Error removing deltafetch file {}'.format(e))
        
        try:
            with open(self.shelve_path, 'rb') as f:
                self.shelve = pickle.load(f)
        except IOError as e:
            logger.info("No cache existing, creating a brand new cache on {}".format(self.shelve_path))
            self.shelve = {}



    def process_spider_output(self, response, result, spider):
        """
        See https://doc.scrapy.org/en/latest/topics/spider-middleware.html
        """
        for r in result:
            if isinstance(r, Request):
                key = self._get_key(r)
                if key in self.shelve:
                    logger.info("Ignoring already visited: %s" % r)
                    if self.stats:
                        self.stats.inc_value('deltafetch/skipped', spider=spider)
                    continue
            elif isinstance(r, (BaseItem, dict)):
                key = self._get_key(response.request)
                self.shelve[key] = str(time.time())
                if self.stats:
                    self.stats.inc_value('deltafetch/stored', spider=spider)
            yield r

    def _get_key(self, request):
        key = request.meta.get('deltafetch_key') or request_fingerprint(request)
        return to_bytes(key)
