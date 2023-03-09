# Linkedin Scraper

This is a wrapper for Tom-Quirks Linkedin API; "https://github.com/tomquirk/linkedin-api"

### Example usage

```python
from Linkedin_Scraper import Scraper

scraper = Scraper()

scraper.search_profiles("software")

scraper.scrape_profiles()
```

### Setup

### Accounts
To setupd your linkedin account, your username and password to the input.txt file in the following format
> username:password

#### Proxies

To setup the proxy functionality of the scraper you must configure boto3 with your aws account

> [#link to boto3 setp](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html)
> 
### Dependencies

- Python 3.7
- A valid Linkedin user account (don't use your personal account, if possible)
- AWS CLI configured (required for proxies, can use without althoug not advisable)
