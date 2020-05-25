# Real estate ads receiver

This app receives Real estate ads from scrapers and registers them into Elasticsearch

The app is supposed to receive real estate properties items crawled on websites. When receiving data, it expects a core information : the geographical **zone** to which the real estate property is attached, all properties of the same geographical zone being in the same Elasticsearch index

## Configuration

configuration is to be done into the `.env` file at the root of this directory. This file expects the following configurations :

| Variable| Meaning | Default
| ---- | --- | ---
| ELASTIC_HOST | Obvious isn't it ? |
| ELASTIC_SHARDS_NUMBER | | 3
| ELASTIC_REPLICAS_NUMBER | | 0
| ELASTIC_PAGE_SIZE | the number of items fetched when searching for Real estate ads | 1000
| FORCE_REFRESH | Valid values are 1 (True) or 0 (False). If set to 1 (True), the Elasticsearch index will be refreshed as soon as a data is indexed. This affects performance, prefer setting to O (False) | 0
| INDEX_PREFIX | the Elasticsearch indices names will be prefixed by this. | catalogs

The configuration for the CI is to be done in a `.env` file, stored at the root of the /backend/ci directory

## Testing

run the following:
```
./ci/compose-tests.sh
```

## Run the app

```
docker-compose up --build

# create the Elasticsearch index (if not existing) for the context
# example below of a new index created for the context 'my_context', the app running on localhost

curl -d '{"zone": "my_zone"}'  -H "Content-Type: application/json" -X POST 'http://localhost:8000/indices'

```
