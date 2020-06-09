# Real estate ads viewer

This app provides a view of the real estate properties scraped by the crawler (`../crawler`) and indexed by the backend (`../backend`)
The properties must comply with the following schema :

```
{
    "type": "object",
    "properties" : {
        "_id": {"type" : "string"},
        "sku": {"type" : "string"},
        "catalog": {"type" : "string"},
        "title"     : { "type" : "string", "minLength": 0}, # allow blank strings
        "description": { "type" : "string"},
        "price"     : { "type" : "number", "minimum": 0},
        "city"    : { "type" : "string"},
        "media" : {"type": "array", "items": { "type": "string" }},
        "url" : {"type" : "string"},
    },
    "required": ["_id", "sku", "catalog", "title", "price", "city", "url"],
}
```

The list of properties can be viewed on *http://host:7000/products/list*

The app uses several third part services :
* __Firebase__ : used to store user's preferences and the catalogs of properties that have been crawler
* __Redis__ : used by the queueing system (RQ) to manage background tasks (like cleanup tasks)
* __Elasticsearch__ : used to retrieve the real estate properties
* __Sentry__ : used to report errors occuring in the app

## Configuration

The configuration is to be done in a `.env` file, stored at the root of the /web directory.

_The configuration for the CI is to be done in a `.env` file, stored at the root of the /web/ci directory_

### Settings related to RQ

| Variable| Meaning | Default
| ---- | --- | ---
| REDIS_HOST | | localhost
| REDIS_PORT | | 9200
| REDIS_PASSWORD | |

### Settings related to Firebase

You need a real time database in firebase to use this app :

| Variable| Meaning | Default
| ---- | --- | ---
| FIREBASE_SERVICE_KEY | this is a base64 encoding of the firebase config. To encode your firbase config, proceed as follows :`echo '{"apiKey": "xxx","authDomain": "xxx", "databaseURL": "xxx", "projectId": "xxx", "storageBucket": "xxx", "messagingSenderId": "xxx"}' \| base64` |
| FIREBASE_LOGIN | the login to use the database |
| FIREBASE_PASSWORD | the password to user the database |

### Settings related to Elasticsearch

| Variable| Meaning | Default
| ---- | --- | ---
| ELASTIC_HOST | |
| ELASTIC_PAGE_SIZE | the number of items fetched on a page |

### Settings related to sentry.io

| Variable| Meaning | Default
| ---- | --- | ---
| SENTRY_URL | Your project URL to push messages in sentry |
| ENVIRONMENT | Tag used in sentry to facilitate the triage of the incoming messagesM. For instance 'dev', 'QA' or 'prod'  |

### Settings related to Authentication

Users can authenticate into the app, thus their filters can be saved in Firebase

| Variable| Meaning | Default
| ---- | --- | ---
| GOOGLE_CLIENT_ID | provided by your google console |
| GOOGLE_CLIENT_SECRET | provided by your google console |

In addition, you'll see 2 important settings in `config.py`:

```
OAUTH_REDIRECT_URI = 'http://localhost:7000/login/oauth'  # define it in google api console too
REDIRECT_AFTER_AUTH = 'http://localhost:7000/welcome'  
```

## Required Data

The app requires some data to run, the data are to be stored in Firebase:

### Catalogs

Real Estate properties have a "_catalog_" attribute, it enables to know the website on which it has been crawled.

For instance, the catalog "qaza" relates to the website http://www.qaza.fr

Sample catalogs are installed at startup, corresponding to sample crawlers in  `../crawlers/estate_agents/estate_agents/spiders`

The `short_name` attribute of a catalog must correspond to the corresponding spider name

In a nutshell for a given real property :
* the real estate property indexed in Elasticsearch has a "catalog" attribute (ex: a_catalog)
* The catalog "A Catalog" must have the attribute "short_name" set to "a_catalog" in firebase

**The short_name of each catalog must correspond to the spider name (see `../crawlers/estate_agents/estate_agents/spiders`)**

#### what is a zone ?

Each catalog must have a "zone" attribute, a zone is a geographical grouping of real estate ads. For instance, you may decide to group together the catalogs _a_ and _b_ : to do this both catalogs would have the same zone.

The zone being also the name of the elasticsearch index in which the real estate ads are indexed, be careful to assign catalogs with a zone name which corresponds to a real index !

_Example:_
_Let's consider you have developped a spider named 'new_spider', which crawls the real estate ads of Paris (1st arrondissement)_
_You would have the following data :_

* _your spider name would be 'new_spider'_
* _your crawler `ZONE` setting in `../crawlers/estate_agents/settings.py` would be `ZONE=paris_1`_
* _you would have a catalog 'new_spider' in firebase, with the attribute 'zone' which would be paris_1_

_Thus to display the list of real estate ads, you would call `http://your_ip:7000/products/list?zone=paris_1&user_id=1` (if you are the user 1)_

### Users

Some base users are installed at startup, if you wan to add users, you may use the /users API
```
curl -H 'Content-Type: application/json' -X POST http://localhost:7000/users/1  -d '{
    "firstname": "John",
    "lastname": "Doe"
}'
```

## Testing

```
./ci/compose-tests.sh
```

## Start the service

```
docker-compose up --build
```

## Stop the service

```
docker-compose down
```
