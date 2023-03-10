from Scraper import Linkedin_scraper

scraper = Linkedin_scraper(debug=True, use_proxies=True)

scraper.search_profiles("software")

scraper.scrape_profiles()
