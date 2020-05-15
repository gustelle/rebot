# Real estate ads scraping

This app provides scrapers for real estate agencies.
The property ads crawled are sent to a service, which is supposed to receive and handle them

## Installation

Spiders are deployed with scrapyd-client, thus it has to be installed first:

```
pip install scrapyd-client
pip install -r estate_agents/requirements.txt
```

## Configuration

### configuration of `scrapyd.conf`
The params eggs_dir, logs_dir, items_dir, dbs_dir are used by scrapy

### configuration of `estate_agents/scrapy.cfg`
The scrapyd server can be configured in the `url` param (default : http://127.0.0.1:6800/)

### configuration of `estate_agents/estate_agents/settings.py`
There are 2 params to be configured:
* `ON_PROCESS_ITEM` is the service which will receive the scraped items
* `DATA_CONTEXT` is a param is to be used by the app receiving the scraped items, giving additional info to handle the items
For instance, the DATA_CONTEXT may be used by the service receiving the items to define an elasticsearch index where to store data

Each item scraped is sent to the `ON_PROCESS_ITEM` URL with the following body in a POST request :
* `catalog` : the name of the real estate agency that is being scraped. The catalog name corresponds to the spider name attribute
* `item` : the real estate property scraped
* `context` : an additional param to be used (or not) by the service receiving the scraped data. __All the spiders share the same context !__. Thus the context can be considered by the service receiving data as a way to group the real estate agencies 

_The item scraped is compliant with the following schema:
"properties" : {
      "sku": {"type" : "string"},
      "title"     : { "type" : "string"},
      "description": { "type" : "string"},
      "price"     : { "type" : "number", "minimum": 0},
      "city"    : { "type" : "string"},
      "media" : {"type": "array", "items": { "type": "string" }},
      "url" : {"type" : "string"},
  },
  "required": ["sku", "title", "price", "city", "url", "media"]_

## How to scrape data

```
## Deploy the spiders
# configuration of the deployment can be done in catalog_crawlers/scrapy.cfg

./scripts/deploy-spiders.sh

## List the available spiders
./scripts/list-spiders.sh

## Start scraping
# to start the spider 'rh'
./scripts/start-spider.sh rh

# the script will provide back the **JOB ID** of the spider, it will be useful to stop it !!
# so note it before closing the terminal
# if you lost the job id, you can retrieve it as follow:

curl http://127.0.0.1:6800/listjobs.json?project=catalog_crawlers | python -m json.tool

## Stop scraping
# $job_id corresponds to the one provided when you started the spider

./scripts/stop-spider.sh $job_id
```

## Adding a crawler

If you wan to add a crawler, be careful to:

* __the spider name__ (`name` attribute of the spider) : it will be used as the `catalog` param sent to the service receiving the data
* __you must use the EstateProperty loader so that the data are considered__ :

```
from ..items import EstateProperty

class MySpider(scrapy.Spider):

  # remember : name is passed as the catalog attribute
  # to the service receiving data
  name = 'ndi'
  start_urls = ["..."]

  def parse_product(self, resp):

    loader = ItemLoader(item=EstateProperty(), response=resp)
    loader.add_value("url", resp.request.url)

    ....

    yield loader.load_item()

# the data scraped must be compliant with the json schema :
# "properties" : {
#      "sku": {"type" : "string"},
#      "title"     : { "type" : "string"},
#      "description": { "type" : "string"},
#      "price"     : { "type" : "number", "minimum": 0},
#      "city"    : { "type" : "string"},
#      "media" : {"type": "array", "items": { "type": "string" }},
#      "url" : {"type" : "string"},
#  },
#  "required": ["sku", "title", "price", "city", "url", "media"]

# at the end, don't forget to send your data to the pipeline :

```
