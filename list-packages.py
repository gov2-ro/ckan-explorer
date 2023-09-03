import requests, json

# ckan_instance = "https://data.gov.ro"
# data_root='data/'
ckan_instance = "https://data.gov.md/ckan"
data_root='data/data.gov.md/'

# Step 1: Get a list of dataset names
response = requests.get(f"{ckan_instance}/api/3/action/package_list")
datasets = response.json()["result"]

with open(data_root + 'package-list.json', 'w') as f:
    json.dump(datasets, f)

# write to file


