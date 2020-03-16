# ScoutSpyder
ScoutSpyder is a web crawler I wrote for fun (and mostly out of curiosity). It was also rather interesting to see what data I could obtain with the crawler.

The crawler uses Selenium to manipulate a headless browser to conduct its crawls. This allows it to crawl JavaScript rendered pages as well!

Currently, the crawler supports crawling Medium, New York Times, Pastebin, Washington Post and Polyswarm's blog out-of-the-box.

# Using it Out-of-the-Box
### Pre-requisites
1. An existing `MongoDB` database setup to store crawled data.
2. `Docker` and `Docker Compose` on the host you want to run the crawler on.
3. Google Chrome and the Chrome WebDriver (For local runs only)

### Installing Docker
These links will probably help you:
1. [Docker Setup](https://docs.docker.com/install/)
2. [Docker Compose Setup](https://docs.docker.com/compose/install/)

### Configuring the Crawler
In the `config.ini` file are some settings you should consider.

They are pretty self-explanatory. Though it must be said that the `Path` property under the `SELENIUM` section can be ignored if you're using a Docker as the deployment means.

### Running the Crawler Directly
By default, ScoutSpyder is written to use a remote Selenium standalone Chrome instance to conduct its crawls.

Some modifications are required to allow it to be run with a local Chrome executable.
1. Open `Backend/ScoutSpyder/core.py`
2. Find the `start_crawler` function.
3. Make the following modifications.

**Original**
```python
def start_crawler(master_browser=initialise_remote_browser,
    child_browser=initialise_remote_browser)
```

**Updated**
```python
def start_crawler(master_browser=initialise_master_browser,
    child_browser=initialise_child_browser)
```
4. Ensure your `Path` property under the `SELENIUM` section in `config.ini` points to a valid WebDriver executable for your version of the chrome browser.
5. `python main.py -h` should be helpful enough for the rest!

**IMPORTANT**  
Reverse the changes to the `start_crawler` if your wish to use the Docker deployment later!

### Building and Running the Crawler with Docker
1. Run the command `docker-compose up -d` at the root directory of this repository.

### Starting a Crawl with Docker Deployment
The crawler operates with a HTTP API to initiate crawls.

To start a crawl, send a HTTP `POST` request with [Postman](https://www.postman.com/downloads/) or any tool you like to the endpoint at `${host_ip}/api/v1/crawler/manage`, replacing `host_ip` with the IP address of your host machine.

The payload for the `POST` request is as follows:  
```json
{
    "duration": 90,
    "activatedCrawlers": ["com.medium"],
    "environments": [
        {
            "name": "ENVIRONMENT_VAR_1",
            "value": "env_value_1"
        },
        {
            "name": "ENVIRONMENT_VAR_2",
            "value": "env_value_2"
        }
    ]
}
```

**Payload Breakdown**
1. `duration`  
   This property is *mandatory* and specifies the crawl duration of the crawl session in minutes.

2. `activatedCrawlers`  
   This property is *optional* and specifies the list of crawlers to activate in the crawl session. If not specified, all crawlers listed in `ENABLED_CRAWLERS` under `ScoutSpyder/crawlers/__init__.py` are used.

3. `environments`  
   This property is *optional* and specifies a list of environment variables to set for the crawl session. If not specified, no additional environment variables will be added to the context of the crawl process.

# Implementing Additional Crawlers
In order to use the crawler to crawl additional sites other than the ones it crawls out of the box, you'd need to implement the crawlers yourself.

The following is the simplest reference code that you can refer to when implementing a new crawler. Refer to `ScoutSpyder/crawlers` for more examples.

```python
from ScoutSpyder.crawlers.base_crawler import *
from ScoutSpyder.utils.helper import *
from time import sleep

class MediumCrawler(BaseCrawler):
    crawler_id = 'com.medium'
    requests_per_sec = 1
    start_url = [
        'https://medium.com/topic/cybersecurity'
    ]
    cookies_url = ['https://medium.com']
    fqdns_in_scope = [
        'onezero.medium.com'
    ]

    def __init__(self, downloaded_doc=None):
        super().__init__(downloaded_doc)
        self.blacklist_suffix += [
            '&quot;);',
            ')'
        ]
        self.blacklist_regex = [
            'http[s]?://medium.com/m/signout/(.*)'
        ]

    def signin(self, browser):
        """
        Returns `True` on successful login, otherwise returns `False`
        """
        # Medium authenticates with a link sent
        # to the user requesting authentication.
        # In here, we obtain the authentication
        # link from the environment variable and
        # use it to authenticate.
        auth_link = get_env('COM_MEDIUM_AUTH_LINK')
        if not auth_link:
            return False
        browser.get(auth_link)
        # A (useless) little check for
        # successful authentication :3
        if not browser.get_cookies(): 
            return False
        return True
    
    def extract_content(self):
        article = self.parsed_lxml.find('.//article')
        if article is not None and self.valid_body:
            self.has_content = True
```

### Mandatory (IMPORTANT)
The most basic form of the crawler requires certain **class variables** and **instance methods** to be implemented, some files such as the `ScoutSpyder/crawlers/__init__.py` must also be modified.

To start implementing the class, drop a new class in the `Backend/ScoutSpyder/crawlers` directory and create a new class, inheriting `BaseCrawler` from `ScoutSpyder/crawlers/base_crawler.py`.

The list of required class variables and instance methods are available below.

**Class Variables**  
The following are important class variables that should be considered during implementation.
1. `crawler_id`  
   A `str` used as a unique identifier for the crawler, ensure it does not conflict with the `crawler_id`s of existing crawlers. **MUST** be set, any arbitrary non-conflicting value is fine.  
   Example: `'com.example'`

2. `requests_per_sec`  
   An `int` value indicated the maximum number of request per seconds that can be sent for a website, rate-limiting is implemented per FQDN, not per crawler.  
   Default: `1`

3. `robots_url`  
   A `str` pointing to the URL containing robots.txt file which the crawler must abide by when crawling.  
   Default: `None`  
   Example: `'https://example.com/robots.txt'`

4. `start_url`  
   A `list` of `str` URLs to begin crawling from.  
   Default: `[]`  
   Example: `['https://example.com']`

5. `cookies_url`  
  A `list` of `str` URLs which the crawler must visit to extract cookies from in the case of an authenticated crawl.  
  Default: `[]`  
  Example: `['htts://api.example.com/', 'https://graphql.example.com/']`

6. `fqdns_in_scope`  
   A `list` of `str` containing additional FQDNs to crawl with the same crawler behaviour (use same content extraction method) if not included in the `start_url` list.
   Default: `[]`  
   Example: `['example2.com', 'blog.example2.com']`

**Instance Methods**  
The following are mandatory instance methods that should be implemented.
1. `__init__(self, downloaded_doc=None)`  
   The initializer/constructor method of the class must be implemented. The constructor must accept 1 argument and call the superclass's `__init__` method, passing the accepted argument to the superclass's `__init__` method.

2. `extract_content(self)`  
   This method must be implemented. The crawler, by default, attempts to automatically extract content from a given page that was crawled. In this method, refinements can be made to the extracted content.

   By default, the content extracted is not automatically inserted into the database.
   
   In the case where refinements are not required, this method must minimally conduct the heuristics to determine if the content extracted should be saved to the database.
   
   If the content extracted should be inserted into the database, the instance's `has_content` property should be set to `True` as observed in the example code provided above.

### Optional
The list of optional instance variables and instance methods to implement or modified is listed below. They are not explicitly required and can be skipped if you so wish.

**Instance Variables**  
The following are optional instance variables that may be considered during implementation.
1. `depth_limit`  
   An `int` indicated the depth to crawl links to before stopping the crawler from crawling further download the chain.  
   Default: `5`

2. `blacklist_suffix`  
   A `list` of `str` containing URL suffixes that should not be included in the crawl.
   Default: Common file endings such as `.js`, `.css`, `.png` and so on.  

3. `blacklist_regex`  
   A `list` of `str` containing regex entries of URLs that should not be included in the crawl in the event of a match.  
   Default: `['http[s]?://(.*)signout(.*)']`

**Instance Methods**  
The following are optional instance methods that may be considered during implementation
1. `signin(self, browser)`
   This method defines the flow or the actions that must be taken to conduct a signin. This method works in conjunction with the class variable `cookies_url`.

   The method needs to take in a single argument, `browser`, which is a `selenium.webdrive.Chrome` object.
   
   This allows the method to conduct any activities such it needs using the selenium `WebDriver` API to manipulate the headless browser.

   The method must return `True` in the case of successful authentication and `False` or `None` in the case of a failure.

   By default, this method returns `None` indicating that authentication does not need to be considered for the said crawler.

2. `post_scrap(self)`  
   This method defines the actions or hooks to be run after scrapping is completed and the crawler objects are populated with content.
   
   By default, it runs the default `prepare_db_entries` and `insert_db_entries` instance methods. Both of the aforementioned methods may be overriden.

**Credits**  
The automated content extraction relies on the following Python libraries.
1. Newspaper3k
2. trafilatura

# How it Works
**TBD**