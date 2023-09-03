import requests, json

ckan_instance = "https://data.gov.ro"


# Step 1: Get a list of dataset names
response = requests.get(f"{ckan_instance}/api/3/action/package_list")
datasets = response.json()["result"]

with open('data/package-list.json', 'w') as f:
    json.dump(datasets, f)

# write to file


