#!/usr/bin/env python3
#
import requests
from requests.auth import HTTPBasicAuth
import json
import os
import yaml
import random
from random import randint
from time import sleep
import argparse

endpoint = "http://localhost"

currentDirectory = os.getcwd()
homedir = os.getenv('HOME')
#cfg_yaml = yaml.load(open(homedir+"/test_params.yaml"), Loader=yaml.Loader)
dictionary = open("english-dict.txt", "r").read()
words=dictionary.split()
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
headers = {'content-type': 'application/json'}

def check_active(endpoint):
    if os.system("ping -c 3 " + host.strip(";") + ">/dev/null 2>&1" ) == 0:
        logger.info(CGRN +"SUCCESS - Can ping {}. ".format(host) + CEND)
        #return 0
    else:
        logger.error(CRED +"ERROR - Cant ping {}. ".format(host) + CEND)
        #return 1

def get_owners(endpoint):
    response = requests.get(endpoint+'/api/customer/owners')
    if response.ok:
        if len(json.loads(response.text)) == 0:
            print("ERROR - No owners returned from get owners")
        else:
            # If we Found clusters that are not compatible with WCP
            length_of_owners = len(json.loads(response.text))
            print("response text is {}".format(response.text))
            return length_of_owners
    else:
        print(response.status_code)
        print(response.text)

def get_owner_details(endpoint):
    last_owner_id = get_owners(endpoint)
    random_user_id = random.randrange(1, last_owner_id, 1)
    print("Getting details for randomly chosen User ID " + str(random_user_id))
    response = requests.get(endpoint + '/api/gateway/owners/' + str(random_user_id), headers=headers)
    if response.ok:
        if len(json.loads(response.text)) == 0:
            print("ERROR - No owners returned from get owners")
        else:
            # If we Found clusters that are not compatible with WCP
            length_of_owners = len(json.loads(response.text))
            print("response text is {}".format(response.text))
            return length_of_owners
    else:
        print(response.status_code)
        print(response.text)

def get_vets(endpoint):
    response = requests.get(endpoint+'/api/vet/vets')
    if response.ok:
        if len(json.loads(response.text)) == 0:
            print("ERROR - No owners returned from get owners")
        else:
            # If we Found clusters that are not compatible with WCP
            print("response text is {}".format(response.text))
            reasons = None
    else:
        print(response.status_code)
        print(response.text)

def get_new_user():
    first_name_rnd = random.choice(words)
    last_name_rnd = random.choice(words)
    address_rnd = random.choice(words)
    city_rnd = random.choice(words)

    user = {
        "firstName": first_name_rnd,
        "lastName": last_name_rnd,
        "address": address_rnd,
        "city": city_rnd,
        "telephone": "1234567898"
    }
    return user

def post_owners(endpoint, user_to_add):
    print(user_to_add)
    response = requests.post(endpoint+'/api/customer/owners', json=user_to_add, headers=headers)
    if response.ok:
        if len(json.loads(response.text)) == 0:
            print("ERROR - No owners returned from get owners")
        else:
            # If we Found clusters that are not compatible with WCP
            print("response text is {}".format(response.text))
            reasons = None
    else:
        print(response.status_code)
        print(response.text)

def get_new_pet():
    pet = {
        "birthDate": "2222-12-22T05:00:00.000Z",
        "id": 0,
        "name": random.choice(words),
        "typeId": str(random.randrange(1,6,1))
    }
    return pet

def post_pets(endpoint, pet_to_add):
    print(pet_to_add)
    last_owner_id = get_owners(endpoint)
    random_user_id = random.randrange(1,last_owner_id,1)
    print("Adding a pet to randomly chosen User ID " + str(random_user_id))
    response = requests.post(endpoint + '/api/customer/owners/'+ str(random_user_id)+'/pets', json=pet_to_add, headers=headers)
    if response.ok:
        if len(json.loads(response.text)) == 0:
            print("ERROR - No pets returned from get pets")
        else:
            # If we Found clusters that are not compatible with WCP
            print("response text is {}".format(response.text))
            reasons = None
    else:
        print(response.status_code)
        print(response.text)


################################
################################
#################################   MAIN   ################################
def main():

    actions_list = ["get_owners", "get_owner_details", "get_vets", "add_owner", "add_pet"]

    while True:
        weighted_random_actions = random.choices(actions_list, weights=(70, 70, 60, 20, 30), k=1)
        print(weighted_random_actions)

        if weighted_random_actions[0] == 'get_owners':
            # Check for
            print("Getting owners ")
            print("Current number of pet owners is " + str(get_owners(endpoint)))
        elif weighted_random_actions[0] =="get_owner_details":
            print("Getting owner details ")
            get_owner_details(endpoint)
        elif weighted_random_actions[0] =="get_vets":
            print("Getting vets ")
            get_vets(endpoint)
        elif weighted_random_actions[0] == "add_owner":
            print("Adding an owner ")
            user_to_add = get_new_user()
            post_owners(endpoint, user_to_add)
        elif weighted_random_actions[0] == "add_pet":
            pet_to_add = get_new_pet()
            print(pet_to_add)
            post_pets(endpoint, pet_to_add)

        delay= randint(4, 10)
        print("Sleeping for "+str(delay)+"s")
        sleep(delay)


# Start program
if __name__ == '__main__':
    main()
