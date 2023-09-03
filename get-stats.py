""" 
## Roadmap

- [x] save csv
- [ ] parametrize instance, dataFolder - prepare for gh actions
- [ ] add header columns for stats

 """


import json, requests, csv
import pandas as pd
from random import randint
from time import sleep
import sys, os 
from tqdm import tqdm

ckan_instance = 'https://data.gov.ro'
data_root = 'data/'
# ckan_instance = 'https://data.gov.md/ckan'
# data_root = 'data/data.gov.md/'

# f = open('data/data.gov.ro-package_list-sample.json')
f = open(data_root + 'package-list.json')

columns = [
     "id",
     "metadata_created",
     "metadata_modified",
     "num_resources",
    #  "organization.title",
    #  "organization.name",
     "name",
     "title"
]

data = json.load(f)

batch_size = 50
current_batch = []
clean_json = []
row_count = 0
# print (len(data['result']))
allcount = len(data)
tqdm.write(' > ' + str(allcount) + ' items in the list, reading in batches of ' + str(batch_size))
pbar=tqdm(total=allcount)

for dataset_id in data:
    response = requests.get(f"{ckan_instance}/api/3/action/package_show?id={dataset_id}")
    dataset_info = response.json()["result"]
    filtered_row = {}
    for column in columns:
        if column in dataset_info:
            filtered_row[column] = dataset_info[column]
    if 'organization' in dataset_info and dataset_info['organization']:
        filtered_row['org'] = str(dataset_info['organization'])
        if 'name' in dataset_info['organization'] and len(dataset_info['organization']['name']) :
            filtered_row['org_name'] = dataset_info['organization']['name']
        if 'title' in dataset_info['organization'] and  len(dataset_info['organization']['title']):
            filtered_row['org_title'] = dataset_info['organization']['title']
        
    current_batch.append(filtered_row)
    row_count += 1

    # Check if the current batch is complete or if all rows have been processed
    
    # if len(current_batch) == batch_size or row_count == len(data['result']):
    if len(current_batch) == batch_size or row_count == len(data):
        clean_json.extend(current_batch)

        # Write the data to a CSV file
        with open(data_root + 'package-stats.csv', 'a', newline='') as csvfile:
            fieldnames = columns + ['org','org_name', 'org_title']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # If it's the first batch, write the header row
            if row_count - len(current_batch) == 1:
                writer.writeheader()

            # Write the data in the current batch
            writer.writerows(current_batch)
            # print(str(row_count) + ' / ' + str(allcount))

        # Reset the current batch and wait for 1 second
        current_batch = []
        pbar.update(batch_size/2)
        sleep(randint(3,110)/100)
        pbar.update(batch_size/2)
pbar.close
print('done')
tqdm.write('done')
os.system('say -v ioana "în sfârșit, am gătat ' +  str(row_count) + ' înregistrări " -r 250')