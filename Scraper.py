from linkedin_api import Linkedin
from linkedin_api.client import ChallengeException
"""
Tom-quirk Linkedin API wrapper
https://linkedin-api.readthedocs.io/en/latest/api.html
https://github.com/tomquirk/linkedin-api
"""

from data import (
    get_offset,
    profile_data_try,
    jsonSetCombiner,
    update_json,
    get_unchecked_profiles,
    add_search_to_main,
    job_data_search,
    get_unscraped_jobs,
    )
from proxies import (
    start_proxies,
    close_proxies
)
from challenge import login as challenge_login

import logging
import json
from time import sleep, time
import random
import queue
import threading

def default_evade():
    """
    Rather long random sleep method, this is to try and evade Linkedin Bot detection
    This is aswell a method in the base api im using, so there is multiple layers of 
    waiting
    """

    sleep(30 + random.random()*3.5)

    
class Linkedin_scraper(object):
    """
    The following is a Linkedin Scraper
    The software scrapes broadly for a given keyword
    extracts data from related job listings and profiles
    """

    _SEARCH_LIMIT_TOTAL_ = 900
    _PROFILE_LIMIT_TOTAL__ = 80

    _PATH_TO_PROFILE_DATA_ = "profile_data.json"
    _PATH_TO_JOB_DATA_ = "job_data.json"
    _PATH_TO_CONFIG_ = "config.json"
    _PATH_TO_LOGINS_ = "input.txt"

    use_proxies = True

    logger = logging.getLogger(__name__)

    def __init__(
        self,
        *,
        profile_data=None,
        job_data=None,
        config=None,
        use_proxies=True,
        debug=False,
    ):
        """Constructor"""
        
        if not profile_data:
            self.profile_data = self.open_file(self._PATH_TO_PROFILE_DATA_)
        if not job_data:
            self.job_data = self.open_file(self._PATH_TO_JOB_DATA_)
        if not config:
            if not self.checkConfig():
                #if getting error, must populate input.txt file with usernames and passwords
                #print usernames is asterickeed out passwords
                self.construct_config_file()
            self.config = self.checkConfig()

        self.use_proxies=use_proxies

        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
        self.logger = self.logger


    def search_profiles(self, keyword):
        """
        This method searches for profiles regarding the keyword, aggregates
        data from multiple searches efficiently using the offset feature.
        Creates proxy servers at beginning and deletes once one is used, doesn't
        use threading because of offset functionality

        It's worth noting that further functionality can be achieved with this method and others
        paramters such as network distance, company, etc..
        see https://linkedin-api.readthedocs.io/en/latest/api.html#linkedin_api.Linkedin.search_people
        """

        logins = self.get_available_logins()

        proxies, instance_id = start_proxies(len(logins), self.use_proxies)

        for index, email in enumerate(logins):
        
            api = Linkedin(email, '',
                proxies=proxies[index],
                debug=self.debug
                )

            self.logger.info(f"{email} is searching for {keyword}")

            offset = get_offset(self.config, keyword, "profile_keyword")

            search_data = api.search_profiles(keyword, offset=offset)

            self.updateConfig({"profile_keyword": {keyword: (offset+len(search_data))}}, email=email, searches=self._SEARCH_LIMIT_TOTAL_)

            # when offset var offset gets too big, skips too many results
            if len(search_data < 3):
                self.logger.info(f"{keyword}, all results scraped")
                break

            #pulls methods from data.py and uses self.profile_Data, also updates file and self.profile_Data
            self.profile_data = add_search_to_main(self.profile_data, search_data)

        close_proxies(instance_id)
        write_files()


    def scrape_profiles_base(self, login, proxy, unchecked, result_queue):
        """
        This is called from thread_scraping() only, while this scraper is technically setup
        to run without using scrapers, doing so using this method with the current implemention
        would be incredibily stupid, Linkedin would essentially see tons of requests coming from
        the same IP address, and from a bunch of different accounts.

        is served unchecked profiles from thread_scraping method()
        iterates through profile/public_ids - requesting their profile data
        extracts key details from raw search data, stores it locally
        returns its portion of task to result_queue

        profile data needs to be converted to dict,
        ^hardest part probs^
        """

        profile_visits = self.config["logins"][login]["profile_visits"]

        api = Linkedin(login, '',
            proxies=proxy,
            debug=self.debug
            )

        ret = {}
        for profile in unchecked:

            scrape_data = api.get_profile(profile)
            ret.update(profile_data_try(scrape_data, profile))
            profile_visits+=1

            default_evade()

        self.config["logins"][login]["profile_visits"] = profile_visits
        result_queue.put(ret)


    def scrape_profiles(self):
        unchecked = get_unchecked_profiles()
        self.profile_status = jsonSetCombiner(self.profile_data, self.thread_scraping(self.scrape_profiles_base, unchecked))
        write_files()
        

    def search_jobs(self, keyword):
        """
        Basically Identical to search_profiles method. Searches for any and all job listings
        related to the keyword. spins up proxies 

        Again, it's worth noting that the basis of this functions Linkedin.search_jobs() has
        much more functionality that can be implemented. currently only using keyword arg and
        offset arg
        see https://linkedin-api.readthedocs.io/en/latest/api.html#linkedin_api.Linkedin.search_jobs

        :param 'keyword' str
        """

        self.logger.info("Commencing Job Search")

        logins = self.get_available_logins()

        offset = get_offset(self.config, keyword, "job_keyword")

        proxies, instance_ids = start_proxies(len(logins), self.use_proxies)

        for index, email in enumerate(logins):

            api = Linkedin(email, '',
                debug=self.debug,
                proxies=proxies[index]
            )

            self.logger.info(f"{email} searching for {keyword} related jobs")
            
            search_data = api.search_jobs(keyword, offset=offset)

            self.updateConfig({"job_keyword": {keyword: (offset+len(search_data))}}, email=email, searches=self._SEARCH_LIMIT_TOTAL_)

            self.job_data = job_data_search(self.job_data, search_data)

            close_proxies(instance_ids[index])
        write_files()

            
    def scrape_jobs_base(self, login, proxy, unchecked, result_queue):
        """
        Again very similar to the scrape_profiles_base function. wont go into it here.
        
        Occasionally this will throw an error, in the form of 'invalid request', if this
        is the case it could be the usual linkedin blocking the bot account, or it could 
        be the job listing is no longer up. if this is throwing an error try inputing the 
        urn manually into linkedin

        More functionality can be achieved
        see https://linkedin-api.readthedocs.io/en/latest/api.html#linkedin_api.Linkedin.get_job
        """

        profile_visits = self.config["logins"][login]["profile_visits"]

        api = Linkedin(login, '', 
            debug=True,
            proxies=proxy
        )

        ret = {}
        for job in unchecked:

            search_data = api.get_job(job)
            ret.update(search_data)
            profile_visits+=1

            default_evade()

        self.config["logins"][login]["profile_visits"] = profile_visits
        result_queue.put(ret)


    def scrape_jobs(self):
        unchecked = get_unscraped_jobs(self.job_data)
        self.job_data = self.thread_scraping(self.scrape_jobs_base, unchecked)
        write_files()


    def thread_scraping(self, function, unchecked):
        """
        This function uses multi-threading to 'concurrently' run
        different scraper instances. Distributes egress traffic through
        ec2 proxies, threading saves on time and costs for ec2 instances

        Since many instances writing to the same file can be a problem, I 
        had setup a temp file system (legacy). But I haven't tested multiple
        instances writing to the same variable (self.profile_data/self.job_data)
        so the data is stored using queue, and aggregated one level above this at
        the 
        """

        logins = self.get_available_logins(1)
        len_logins = len(logins)

        proxies, instance_ids = start_proxies(len_logins, self.use_proxies)
        divided_list = self.divide_list(unchecked, len_logins)

        threads = []
        result_queue = queue.Queue()
        for index, login in enumerate(logins):
            threads.append(threading.Thread(target=function, args=(login, proxies[index], divided_list[index], result_queue)))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        close_proxies(instance_ids)

        return result_queue.get()
    

    def open_file(self, _path_):
        """
        Catches errors upon first start
        
        :param '__path__' str - path to local file
        :rtype: bool/Json
        :return if error False - else JSON
        """
        try:
            with open(_path_, 'r') as f:
                return json.loads(f.read())
        except FileNotFoundError:
            #initiate file
            with open(_path_, 'w') as f:
                pass
            return False
        except json.JSONDecodeError:
            return False


    def write_files(self):
        """
        This method simply updates the relevent config and 
        data files with the current state of the scraper
        """

        with open(self._PATH_TO_PROFILE_DATA_, 'w') as f:
            f.write(json.dumps(f.read(), indent=4))
        with open(self._PATH_TO_PROFILE_DATA_, 'w') as f:
            f.write(json.dumps(f.read(), indent=4))
        with open(self._PATH_TO_CONFIG_, 'w') as f:
            f.write(json.dumps(f.read(), indent=4))
    

    def new_day(self):
        """
        This method removes overhead when running this scraper multiple times
        through multiple days scraper updates the time in which it was last run,
        then this method compares current time to stored time, if more than a day
        then reset scraper values
        """

        if time.time() - self.config["update_time"] >= 86400:

            self.logger.info("New Day! Resetting Values")

            for email in self.config["logins"]:
                for element in self.config["logins"][email]:
                    if element == "password":
                        pass
                    elif element == "tracking_id":
                        pass
                    else:
                        self.config["logins"][email][element] = 0
        else:
            self.logger.info("Not a new day, not resetting values")


    def get_available_logins(self, int):
        available_logins = []
        for email in self.config["logins"]:
            if self.email_checker(email, int):
                available_logins.append(email)
        if len(available_logins) <= 0:
            self.logger.debug("No Available Logins")
            return False
        return available_logins


    def email_checker(self, email, int):
        """
        Checks if a given email is valid for more scraping/searching. Scraping/searching is denoted by a given int.
        These values reset if the scraper is run a day after the previous invocation.
        
        :param 'email' str - Login info for scraper account
        :param 'int' int - check for searching/scraping
        
        :rtype bool
        :return if the email is under the unoffical api limits
        """
        if int == 1:
            if self.config["logins"][email]["profile_visits"] < self._PROFILE_LIMIT_TOTAL__:
                return True
            return False
        if int == 2:
            if self.config["logins"][email]["searches"] < self._SEARCH_LIMIT_TOTAL_:
                return True
            return False
        

    def updateConfig(self, data_dict=None, email=None, profile_visits=None, searches=None, launches=None):
        if data_dict:
            self.config = update_json(self.config, data_dict)
        if email:
            if searches:
                self.config["logins"][email]["searches"] = searches
            if profile_visits:
                self.config["logins"][email]["profile_visits"] = profile_visits
            if launches:
                self.config["logins"][email]["launches"] = launches
            #impossible to result from user error,
            # will delete these errors after testing
            if not searches and not profile_visits and not launches:
                raise ValueError("updateConfig w/ email but wo/ parameter")
        if not data_dict and not email and not searches:
            raise ValueError("updateConfig Error")


    def construct_config_file(self):
        """
        I've tried to reduce overhead and make the setup as easy as possible
        when using this repo. This method is called upon the first calling of 
        the constructor on a system. 

        This method also attempts to login and gain cached cookies, if it fails 
        the scraper doesnt work.

        - THIS FUNCTION ATTEMPTS TO HANDLE CHALLENGE EXCEPTION -
        the solution barely ever works, but sometimes it does,
        better than nothing

        Extracts user inputed username/login from input file
        Starts proxies to login and store cookies for each username:password
        closes proxies

        --- NOTICE ---
        When linkedin receives a login from a new location it likes to throw challenge error
        Try this method use_proxies=False
        """

        with open(self._PATH_TO_LOGINS_, 'r') as f:
            logins = {}
            for line in f.readlines():
                if line[0] == '#':
                    continue
                try:
                    nline = line.split(":")
                    logins[nline[0]] = nline[1]
                except Exception:
                    raise ValueError("Invalid Login Format")
        
        proxies, instance_ids = start_proxies(len(logins), self.use_proxies)

        self.logger.info(f"{len(proxies)} proxy servers started")

        config = {}
        config['logins'] = {}
        config['update_time'] = 0
        config['profile_keyword'] = {}
        config['job_keyword'] = {}
        for index, username in enumerate(logins):
            config['logins'][username] = {}
            config['logins'][username]['profile_visits'] = 0
            config['logins'][username]['searches'] = 0

            try:
                Linkedin(username, logins[username],
                        #debug=False,
                        proxies=proxies[index]
                    )
                
            except ChallengeException:
                challenge_login(username, logins[username])

            close_proxies(instance_ids[index])

            self.logger.info(f"{instance_ids[index]} server closed")

        with open(self._PATH_TO_CONFIG_, 'w') as f:
            f.write(json.dumps(config, indent=4))
