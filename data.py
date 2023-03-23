def get_offset(config, keyword, str):
    """
    Gets offset from config, if key isnt there generates the key with 0-value

    :param 'config' JSON - config state of scraper
    :param 'keyword' str - keyword of search
    :param 'str' str - "profile_keyword"/"job_keyword" different offsets for same keyword in people/jobs

    """
    if keyword in config[str]:
        return config[str][keyword]
    else:
        config[str][keyword] = 0
        return 0
    
def profile_data_try(profile_data, public_id):
    """
    API response data isn't always populated, and when trying to access a key 
    that will be there 90% of the time will result in a KeyError 10% of the time

    This function makes sure that the stored data is 100% populated, and instead of 
    try-except structure a simple 'if not' statement can catch bad data.

    Also renames variables and does very basic data enriching

    :param 'profile_data' JSON - Raw API response
    :param 'public_id' str 
    :rtype JSON
    :return reformatted/ideally-structured/populated profile data
    """

    ret_data = {}
    ret_data[public_id] = {}

    try:
        ret_data[public_id]["country"] = profile_data["geoCountryName"]
    except KeyError:
        ret_data[public_id]["country"] = False

    try:
        ret_data[public_id]["location"] = profile_data["geoLocationName"]
    except KeyError:
        ret_data[public_id]["location"] = False
    try:
        ret_data[public_id]["firstName"] = profile_data["firstName"]
    except KeyError:
        ret_data[public_id]["firstName"] = False

    try:
        ret_data[public_id]["lastName"] = profile_data["lastName"]
    except KeyError:
        ret_data[public_id]["lastName"] = False

    try:
        ret_data[public_id]["experience"] = get_experience_local(profile_data)
    except IndexError:
        ret_data[public_id]["experience"] = False

    try:
        ret_data[public_id]["jobs"] = profile_data["experience"]
    except KeyError:
        ret_data[public_id]["jobs"] = False

    try:
        ret_data[public_id]["summary"] = profile_data["summary"]
    except KeyError:
        ret_data[public_id]["summary"] = False

    try:
        ret_data[public_id]["headline"] = profile_data["headline"]
    except KeyError:
        ret_data[public_id]["headline"] = False

    try:
        temp = profile_data["member_urn"]
        templist = temp.split(":")
        ret_data[public_id]["member_urn"] = str(templist[len(templist)-1])
    except KeyError:
        ret_data[public_id]["headline"] = False
        
    ret_data[public_id]["sentEmails"] = []
    ret_data[public_id]["checked"] = True
    return ret_data

def jsonSetCombiner(main_data, jsonObjs):
    """
    Combines set of json objs

    :param main_data JSON - structured class data
    :param 'jsonObjs' list[JSON]
    :rtype JSON
    :return combined JSON obj
    """

    for jsonObj in jsonObjs:
        main_data.update(jsonObj)
    return main_data

def company_jsonSetCombiner(job_data, jsonObjs):
    for jsonObj in jsonObjs:
        for company in jsonObj:
            job_data[company]["companyData"]=jsonObj[company]["companyData"]
    return job_data

def update_json(data, update_data):
    """
    Update the values of `data` with the values of `update_data` at the same key path.

    :param 'data' dict JSON
    :param 'update_data' dict

    :return The updated dictionary
    :rtype dict
    """

    for key, value in update_data.items():
        if isinstance(value, dict):
            if key in data:
                update_json(data[key], value)
            else:
                data[key] = value
        else:
            data[key] = value
    return data

def get_unchecked_profiles(central_data):
    """
    Takes main data and finds profiles that haven't been populated

    :param 'central_data' JSON

    :rtype 
    """

    unchecked_profiles = []
    for profile in central_data:
        if not central_data[profile]["checked"]:
            unchecked_profiles.append(profile)
    if len(unchecked_profiles) <= 0:
        return False
    return unchecked_profiles

def add_search_to_main(main_data, search_data, email):
    """
    Makes sure to not add duplicate profiles, adds a key for later scraping "checked"
    Has functionality to account for no 'main_data', (E.g first time running scraper)

    :param 'main_data' dict (JSON)
    :param 'search_data' dict
    :param 'email' str

    :return formatted & aggregated profile data
    :rtype dict
    """

    # new public ids
    search_data_profiles = []
    for item in search_data:
        public_id = item["public_id"]
        if not main_data:
            continue
        if public_id not in main_data:
            search_data_profiles.append(item)

    reformatted_search_data = reformat_json(search_data_profiles if main_data else search_data)

   
    ret_data = add_key_value(reformatted_search_data, "checked", False) #scraped/checked checker
    ret_data = add_key_value(ret_data, "email_used", email)

    if main_data:
        ret_data = main_data.update(ret_data)
    return ret_data

def reformat_json(data):
    """
    Reformats Voyager API's raw-response's JSON data

    :Original
    {
        public_id:public_id_value,
        key:value,
        key:value
    }

    :New
    public_id_value: {
        key:value,
        key:value
    }

    :return reformatted dict ^
    :rtype dict
    """

    # Create an empty dict to store the reformatted data
    reformatted_data = {}
    # Iterate through each element in the JSON data
    for element in data:
        #print(element)
        # Extract the public_id from the element
        public_id = element.pop("public_id")
        # Create a new dictionary with the public_id as the key and the remaining element as the value
        reformatted_element = {public_id: element}
        # Add the reformatted element to the list
        reformatted_data.update(reformatted_element)
    # Return the reformatted data as a JSON string
    return reformatted_data

def add_key_value(data, key, value):
    """
    Adds a key value pair to dict

    :return dict with added key-value pair
    :rtype dict
    """
    # Iterate through each element in the JSON data
    for element in data:
        # Extract the public_id from the element
        # Check if key already exists in the element's data
        if key in data[element]:
            # Check if the value of the key is a list
            if isinstance(data[element][key], list):
                # Extend the list with the given value
                data[element][key].append(value)
            elif isinstance(data[element][key], bool):
                data[element][key] = value
            else:
                # If the key is not a list, raise an exception
                raise ValueError("Key already exists and is not a list or boolean")
        else:
            # Add the key-value pair to the element's data
            data[element][key] = value
    # Return the modified data as a JSON string
    return data

def job_data_search(main_data, raw_data):
    """
    Aggregates new data to old data, supports no old data.
    simple filtering and fomratting

    :param 'main_data' JSON - structured job data
    :param 'raw_data' raw-JSON - raw return data from api
    :rtype JSON
    :return Strucuted/aggregated/filtered data
    """

    if not main_data:
        return format_job_data(raw_data)
    formatted = format_job_data(raw_data)
    ret_data = aggregate_job_data(main_data, formatted)
    return ret_data

class hashabledict(dict):
    def __hash__(self):
        return hash(tuple(sorted(self.items())))


def format_job_data(data):
    """
    Reformats job data to be paired with job urn. 

    Wrote this awhile ago and don't feel like rewriting

    :param 'data' dict
    :return reformatted json data
    :rtype JSON dict 
    """
    listt = []
    for slice in data:
        try:
            urn = slice["companyDetails"]["company"]
            urnsplit = urn.split(":")
            listt.append([urnsplit[len(urnsplit)-1]])
        except Exception:
            listt.append(slice["companyDetails"]["companyName"].strip())

    #return data headers are  unique company urn
    unique_list = unique(listt)
    ret_data = {}
    for num in unique_list:
        if isinstance(num, str):
            ret_data[num] = {}
        else:
            ret_data[str(num[0])] = {}
    for slice in data:
        try:
            temp1 = slice["companyDetails"]["company"]
            urnsplit = temp1.split(":")
            temp2 = [urnsplit[len(urnsplit)-1]]
            urn = str(temp2[0])
        except KeyError:
            urn = slice["companyDetails"]["companyName"].strip()

        #get job number
        jobtemp = slice["dashEntityUrn"].split(":")
        jobnum = str(jobtemp[len(jobtemp)-1])
        ret_data[urn][jobnum] = {}

        if urn in hashabledict(ret_data):

            #refer to other method
            #get title other metadata
            try:
                ret_data[urn][jobnum]["title"] = slice["title"]
            except KeyError:
                ret_data[urn][jobnum]["title"] = False

            try:
                ret_data[urn][jobnum]["compBreakdown"] = slice["salaryInsights"]["compensationBreakdown"]
            except KeyError:
                ret_data[urn][jobnum]["compBreakdown"] = False

            try:
                ret_data[urn][jobnum]["location"] = slice["formattedLocation"]
            except KeyError:
                ret_data[urn][jobnum]["location"] = False

            try:
                ret_data[urn][jobnum]["benefits"] = slice["briefBenefitsDescription"]
            except KeyError:
                ret_data[urn][jobnum]["benefits"] = False
               
            try:
                ret_data[urn][jobnum]["applyUrl"] = slice["applyMethod"]["companyApplyUrl"]
            except KeyError:
                ret_data[urn][jobnum]["applyUrl"] = False

        else:
            print("urn not in data")
            #if else, either its a string or not in data somehow

    for company in ret_data:
        for job in ret_data[company]:
            if job == 'companyData':
                continue
            ret_data[company][job]["scraped"] = False

    return ret_data

def aggregate_job_data(main_data, new_data):
    old_job_urns = get_job_urns(main_data)

    for new_company in new_data:
        # old comapny
        if new_company in main_data:
            for job in new_data[new_company]:
                if job == 'companyData':
                    continue
                #new job
                job_num = job
                if job not in old_job_urns:
                    main_data[new_company][job_num] = {}
                    for element in new_data[new_company][job]:
                        main_data[new_company][job_num][element] = new_data[new_company][job][element]
                #old job do nothing

        #new company
        else:
            main_data[new_company] = {}
            for job in new_data[new_company]:
                if job == 'companyData':
                    continue
                main_data[new_company][job] = {}
                for element in new_data[new_company][job]:
                    main_data[new_company][job][element] = new_data[new_company][job][element]

    return main_data

def get_job_urns(data):
    urns = []
    for companyUrn in hashabledict(data):
        for listingUrn in data[companyUrn]:
            urns.append(listingUrn)
    return urns

def unique(list1):

    # initialize a null list
    unique_list = []

    # traverse for all elements
    for x in list1:
        # check if exists in unique_list or not
        if x not in unique_list:
            unique_list.append(x)
    # print list
    return unique_list

import datetime
def get_experience_local(profile_data):
    """
    Data enriching - takes difference in time from first job latest job

    :param 'profile_data' JSON - Raw API response
    :rtype int
    :return number of years in workforce
    """

    today = datetime.date.today()
    CURRENT_YEAR = today.year
    experience = profile_data["experience"]

    job_dates = []
    for i in experience:
        try:
            job_dates.append(i["timePeriod"])
        except KeyError:
            # $anti_abuse_metadata
            pass

    start = job_dates[len(job_dates)-1]["startDate"]["year"]
    return CURRENT_YEAR-start

def get_unscraped_jobs(job_data):
    """
    Help method for scraper.scrap_jobs_base() - checks stored data for jobs
    whose key 'scraped' is false.

    :param 'job_data' JSON - stored job data
    :rtype list
    :return jobs who have not been visited yet
    """
    ret_data = []
    for company in job_data:
        for job in job_data[company]:
            if job == "companyData":
                continue
            if not job_data[company][job]["scraped"]:
                ret_data.append(job)
    return ret_data

def divide_list(lst, num_parts):
    """
    Divides list into smaller lists, given number of parts

    :param 'lst' list - list to be divided
    :param 'num_parts' int - num of parts list to be divided into
    :rtype list[lists]]
    :return list divided into smaller equal lists
    """

    # Calculate the length of each sublist
    sublist_length = len(lst) // num_parts

    # Calculate the number of sublists that will have one extra element
    num_long_sublists = len(lst) % num_parts

    # Initialize the list of sublists
    sublists = []

    # Create the sublists
    start_idx = 0
    for i in range(num_parts):
        # Determine the length of this sublist
        sublist_len = sublist_length + (1 if i < num_long_sublists else 0)

        # Add the sublist to the list of sublists
        sublists.append(lst[start_idx:start_idx+sublist_len])

        # Update the starting index for the next sublist
        start_idx += sublist_len

    return sublists

def get_unchecked_companies(job_data):
    """
    Fetches companys for scrape_companies_base
    
    :param 'job_data' JSON
    :rtype list
    :return un-scraped companies
    """

    unchecked_company = []
    for company in job_data:
        if "companyData" not in job_data[company]:
            unchecked_company.append(company)
    return unchecked_company

def company_data_agg(company_data, urn, ret):

    ret[urn] = {}
    ret[urn]["companyData"] = {}

    try:
        ret[urn]["companyData"]["companySize"] = company_data["staffCount"]
    except KeyError:
        try:
            ret[urn]["companyData"]["companySize"] = company_data["staffCountRange"]
        except KeyError:
            ret[urn]["companyData"]["companySize"] = False

    try:
        ret[urn]["companyData"]["url"] = company_data["companyPageUrl"]
    except KeyError:
        try:
            ret[urn]["companyData"]["url"] = company_data["callToAction"]["url"]
        except KeyError:
            ret[urn]["companyData"]["url"] = False

    try:
        write_list = []
        for industry in company_data["companyIndustries"]:
            write_list.append(industry["localizedName"])
        ret[urn]["companyData"]["industries"] = write_list
    except KeyError:
        ret[urn]["companyData"]["industries"] = False

    try:
        ret[urn]["companyData"]["followerCount"] = company_data["followingInfo"]["followerCount"]
    except KeyError:
        print("followerCountError")
        ret[urn]["companyData"]["followerCount"]

    return ret