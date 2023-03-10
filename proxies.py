import boto3
import requests
from time import sleep
region = 'us-east-1'
def start_proxies(num_proxies, use_proxies):
    """
    This method requests new instances from user's AWS account. Ubuntu 18.04, t1.micro
    It passes userdata to install tinyproxy software, aswell as adding the user's ip to
    the tinyproxy config file. 

    For the boto3 library to work, the AWS-CLI on the machine has to be configured
    with the appropriate access keys

    TO_DO:
    Start instances only if config file doesnt contain instances, if it does, 
    retrieve instances and start. 
    This resolves the need to spin up new instances every time
    saves a little time and a little money

    :param 'num_proxies' int - # of proxy servers started
    :param 'use_proxies' bool - Whether or not the scraper class instance is using proxies
    :return proxy servers
    :rtype List of length 2, 1: list of dicts, 2: list of str
    """

    # Terrible code on my part, but this avoids index-
    # errors and makes main class look better
    if not use_proxies:
        proxies = []
        instance_ids = []
        for i in range(0, num_proxies):
            proxies.append({})
            instance_ids.append('')
        return [proxies, instance_ids]


    # Create an EC2 client
    ec2 = boto3.client('ec2', region_name=region)
    # Make an HTTP GET request to the ipify API to fetch public IP address
    response = requests.get('https://api.ipify.org')
    # Get the IP address from the response content
    my_ip = response.content.decode('utf-8')

    #commands that run upon instance launch
    user_data_script = f"""#!/bin/bash
    # Install Tinyproxy
    sudo apt-get update
    sudo apt-get upgrade
    sudo apt-get install -y tinyproxy

    # Edit the configuration file
    sudo echo 'Allow 127.0.0.1' >> /etc/tinyproxy/tinyproxy.conf
    sudo echo 'Allow {my_ip}' >> /etc/tinyproxy/tinyproxy.conf

    # Restart Tinyproxy
    sudo /etc/init.d/tinyproxy restart
    # sudo touch /tmp/installation_complete
    """


    ami_id = 'ami-0263e4deb427da90e' # Ubuntu AMI
    #key_name = 'proxy-key' #replace with aws key-pair name for troubleshouting
    instance_type = 't1.micro' # Smallest possible ec2 for frugality
    security_group_id = 'sg-0a516230e5c68aad3'#currently not portable, 

    response = ec2.run_instances(ImageId=ami_id,
        InstanceType=instance_type,
        #KeyName=key_name,
        SecurityGroupIds=[security_group_id],
        UserData=user_data_script,
        MinCount=num_proxies,
        MaxCount=num_proxies
        )

    #need to return instance ids for later instance termination
    instance_ids = []
    for instance in response["Instances"]:
        instance_id = instance["InstanceId"]
        instance_ids.append(instance_id)

    wait_instances_running(ec2, instance_ids)
    response_description = ec2.describe_instances(InstanceIds=instance_ids)

    instance_ips = []
    for i in response_description["Reservations"][0]['Instances']:
        instance_ips.append(i["PublicDnsName"])

    # EC2 instance details
    ec2_instance_port = "8888"
    ec2_instance_username = "ubuntu"
    proxies = []
    for ip in instance_ips:
        proxy1 = "http://{}@{}:{}".format(ec2_instance_username, ip, ec2_instance_port)
        proxies.append({'http':proxy1, 'https':proxy1})

    # [ proxies ] - [ {}, {}, {}]
    # [ instance_ids]
    ec2.close()
    return [proxies, instance_ids]
    

def wait_instances_running(ec2, instance_ids):
    """
    Waits for instances to return an 'instanceState' of 'Running'. Then ideally wait
    till a file called installationcomplete to be created but that wasnt working so
    just sleeps for awhile until tiny-proxy servers are downloaded
    
    :param 'ec2' Boto3 client
    :param 'instance_ids' List[str] - ids of instances to check 
    """

    while True:
        # Describe all instances to get their current state
        instance_statuses = ec2.describe_instance_status(InstanceIds=instance_ids)['InstanceStatuses']

        # Check if all instances are in a running state
        all_running = True

        for status in instance_statuses:
            if status['InstanceState']['Name'] != 'running':
                all_running = False
                break
        if not instance_statuses:
            all_running = False

        # If all instances are in a running state, break the loop
        if all_running:
            break

        # Wait for 5 seconds before checking the status again
        sleep(10)
    sleep(110)

def close_proxies(instance_ids, use_proxies):
    if not use_proxies:
        return
    ec2 = boto3.client('ec2', region_name=region)
    response = ec2.terminate_instances(InstanceIds=instance_ids)
    ec2.close()















