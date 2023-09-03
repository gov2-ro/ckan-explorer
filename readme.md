## Scripts

- `list-packages.py` - reads `{ckan_instance}/api/3/action/package_list` , saves to `data/package-list.json`
- `get-stats.py` - loops package-list.json and generates `package-stats.csv`

## Roadmap 

- [x] fetch datasets index
- [x] get stats
- [ ] get org stats
- [ ] consolidate yearly data

## UI
- top orgs - show heatmap table timeline (order by versions / last updated / versions last year)
