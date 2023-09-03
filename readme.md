# CKAN Stats 

see [CKAN data analyzer](https://docs.google.com/document/d/1Emrco1IWSVUrHCGGPlFBf8qqCEucECJi/) 

## Scripts

- `list-packages.py` - reads `{ckan_instance}/api/3/action/package_list` , saves to `data/package-list.json`
- `get-stats.py` - loops package-list.json and generates `package-stats.csv`

## Roadmap 

- [x] fetch datasets index
- [x] get stats
- [ ] add header columns for stats
- [ ] prepare for gh actions
- [ ] get org stats
- [ ] consolidate yearly data

## UI
- top orgs - show heatmap table timeline (order by versions / last updated / versions last year)
