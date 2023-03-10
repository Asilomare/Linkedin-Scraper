 
def get_offset(config, keyword, str):
    """
    when a keyword is searched for the initial results are always the same,
    so we skip the initial results using the offset feature of the API,
    this method coupled with the config file keep track of the offset through
    multiple start stops of the scraper.
    
    :param 'config' JSON - config data of the scraper class
    :param 'keyword' str - searched-for keyword
    :rtype int
    :return stored offset of a given keyword for a given 
    """
  
    if keyword in config[str]:
        return config[str][keyword]
    else:
        config[str][keyword] = 0
        return 0
      
      
def profile_data_try(profile_data, public_id):
    """
    The returned data of the linkedin API is not always 100% populated,
    every now and again there is a missing field from the data. In that case
    you would get a KeyError when trying to access the missing field using dict[key]
    this method makes it so our data is 100% populated in terms of fields,
    and if there is a hole upon later visiting it can be caught with "if not var:"
    instead of having try-excepts everywhere.
    
    :param 'profile_data' JSON - raw data returned by api.get_profile()
    :param 'public_id' str - unique identifier of linkedin profile
    
    :rtype JSON
    :return re-orginized/formatted data to be aggregated to main data
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

   
def jsonSetCombiner(jsonObjs):
    """
    Im leaving this here cause i wrote it in place of simply using .update(),
    and it makes me laugh at my waste of time
    """
    ret_data = jsonObjs[0]
    count = 1
    for jsonObj in jsonObjs:
        if count == len(jsonObjs):
            break
        ret_data = jsonCombine2(ret_data, jsonObjs[count])
        count += 1
    return ret_data

def jsonCombine2(jsonObj, jsonObjAppend):
    for append_profile in jsonObjAppend:
        append_id = list(append_profile.keys())[0]
        for main_profile in jsonObj:
            main_id = list(main_profile.keys())[0]
            if main_id == append_id:
                for metadata in append_profile[append_id]:
                    main_profile[main_id][metadata] = append_profile[append_id][metadata]
                break
    return jsonObj

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

    :rtype List[str]
    :return list of public_ids not yet scraped
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
    new_search_data = []
    for item in search_data:
        public_id = item["public_id"]
        if public_id not in main_data:
            search_data_profiles.append(item)

    reformatted_search_data = reformat_json(new_search_data)

    #scraped/checked checker
    ret_data = add_key_value(reformatted_search_data, "checked", False)
    ret_data = add_key_value(ret_data, "email_used", email)

    if main_data:
        ret_data = main_data.update(ret_data)
    return ret_data

def reformat_json(data):
    """
    Reformats json data

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


    :param 'data' JSON
    :param 'key' str
    :param 'value' any
    
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
    if not main_data:
        return format_job_data(raw_data)
    formatted = format_job_data(raw_data)
    ret_data = aggregate_job_data(main_data, formatted)


class hashabledict(dict):
    def __hash__(self):
        return hash(tuple(sorted(self.items())))


def format_job_data(data):
    """
    Reformats job data to be paired with job urn. Grabs urn from urn string


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
    ret_data = []
    for company in job_data:
        for job in job_data[company]:
            if job == "companyData":
                continue
            if not job_data[company][job]["scraped"]:
                ret_data.append(job)
    return ret_data
