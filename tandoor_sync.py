### Save this file under <HA Config folder>/pyscript/apps/

import json
import requests

def tandoor_shop_list():
    # get data from tandoor API as a JSON Object
    data = task.executor(requests.get, f'{tandoor_url}/shopping-list-entry/', headers=tandoor_read_headers, data={}).json()

    # Return shopping list of tandoor items in tuple with ID and concatenated amount + name
    shopping_list = []
    for item in data:
        if item["checked"] == False:
            shopping_list.append((item["id"], f'{item["amount"]} {" " if item["unit"] == None else item["unit"]["name"]} {item["food"]["name"]}'))
    return shopping_list

@service
def tandoor_update_item(item_id, item_details):
    data = task.executor(requests.patch, f'{tandoor_url}/shopping-list-entry/{item_id}/', headers=tandoor_write_headers, json=item_details)

def ha_shop_list():
    # get data from HA shopping list API as JSON object
    data = task.executor(requests.get, f'{ha_url}/shopping_list', headers=ha_headers).json()
    
    # Return incomplete shopping list of HA items in array
    return [item["name"] for item in data if item["complete"] == False]

@service
@time_trigger("period(now, 30m)")
def sync_tandoor_ha():
    # Check if all required fields have been loaded otherwise log error
    if None in {tandoor_url, tandoor_write_token, ha_url, ha_token}:
        log.error("Tandoor Sync: Please insert URLs and tokens for tandoor and home assistant")
    else:
        # get shopping list from tandoor
        tandoor_list = tandoor_shop_list()

        # get shopping list from HA
        ha_list = ha_shop_list()

        if tandoor_list == []:
            log.info("Tandoor Sync: No items to add from Tandoor")
        else:
            # get list of items to add from tandoor but not in HA
            items_to_add = list({item[1] for item in tandoor_list} - set(ha_list))

            # Add each item from Tandoor to HA and check off item in Tandoor
            for item in items_to_add:
                log.info(f'Tandoor Sync: Adding {item}')
                shopping_list.add_item(name=item)

                log.info(f'Tandoor Sync: Checking off {item} in Tandoor')
                # get item id from tuple list
                for ingredient in tandoor_list:
                    if item == ingredient[1]:
                        item_id = ingredient[0]
                tandoor_update_item(item_id, {'checked': 'true'})

            
# Load variables for pyscript app
config = pyscript.app_config

# Load required user-inputs and secrets
tandoor_url = config['tandoor_url']
tandoor_read_token = config['tandoor_read_token']
tandoor_write_token = config['tandoor_write_token']
ha_url = config['ha_url']
ha_token = config['ha_token']

# Set the bearer token based on input
tandoor_read_headers = {'Authorization': f'Bearer {tandoor_read_token}','Content-Type':'application/json'}
tandoor_write_headers = {'Authorization': f'Bearer {tandoor_write_token}','Content-Type':'application/json'}
# Set the bearer token based on input
ha_headers = {
    'Authorization': f'Bearer {ha_token}',
    'content-type': 'application/json'
}
