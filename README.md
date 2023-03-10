# Linkedin Scraper

This is a wrapper for Tom-Quirks Linkedin API; "https://github.com/tomquirk/linkedin-api"

### Overview
This is a Linkedin scraper. The scraper works by searching for people and jobs related to a keyword.
The scraper stores data about the scraper accounts aswell as the scraped data to local files for state-storing functionality. 
The scraper object can be configured to use proxy servers with the use_proxies keyword param when initializing. 
The scraper uses multi-threading to concurrently run scrapers through different proxies. I've also attempted to tackle the 
infamous ChallengeError(https://github.com/tomquirk/linkedin-api/issues/109) upon startup. 

When ran for the first time, we attempt to connect to Linkedin witht the credentials given in the input.txt file.
The Linkedin api then requests session cookies. This allows the scraper to delete your password(s) and run purely on cookies.
Please not that one of the cookies expires after ~6 months. And the scraper will no longer work. 

In the case that Linkedin asks for verification or temporarily signs you out of your account you will need to delete the relevent cookies
from the stored cookie jar, find the link here(https://github.com/tomquirk/linkedin-api/blob/master/linkedin_api/settings.py). And re-run the
construct_config_file method.

### Example usage

```python
from Linkedin_Scraper import Scraper

scraper = Scraper()

scraper.search_profiles("software")

scraper.scrape_profiles()
```

## Setup

### Accounts
To setupd your linkedin account with the scraper, your username and password to the input.txt file in the following format
> username:password

#### Proxies

To setup the proxy functionality of the scraper you must configure boto3 with your aws account

> [(https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html]
### Dependencies

- Python 3.7
- A valid Linkedin user account (don't use your personal account, if possible)
- AWS CLI configured (required for proxies, can use without although not advisable)

## TO-DO
 - change local files to s3
 - check if files in config, if not create them (first launch)
 - change open_file() and write_files() for s3 
 - change self.use_proxies to use_aws, only use proxies/s3 if true
