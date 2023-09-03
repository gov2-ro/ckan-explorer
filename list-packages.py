import requests, json

ckan_instance = "https://data.gov.ro"
data_root='data/'

# ckan_instance = "https://data.gov.md/ckan"
# data_root='data/data.gov.md/'

# ckan_instance = "https://data.humdata.org/"
# data_root='data/data.humdata.org/'

# ckan_instance = "https://catalog.data.gov/"
# data_root='data/catalog.data.gov/'

# ckan_instance = "https://data.gov.sg"
# data_root='data/data.gov.sg/'

# ckan_instance = "https://africaopendata.org/"
# data_root='data/africaopendata.org/'

# ckan_instance = "https://katalog.data.go.id/"
# data_root='data/katalog.data.go.id/'

# Step 1: Get a list of dataset names
response = requests.get(f"{ckan_instance}/api/3/action/package_list")
datasets = response.json()["result"]

with open(data_root + 'package-list.json', 'w') as f:
    json.dump(datasets, f)

# write to file


