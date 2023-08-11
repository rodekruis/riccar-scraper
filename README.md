# riccar-scraper
Scrape climate data from [RICCAR](https://www.riccar.org/), merge it and slice it.

### Setup
```
pip install -r requirements.txt
```

### Usage
```
Usage: scraper.py [OPTIONS]

Options:
  --dest TEXT        output folder
  --variable TEXT    variable (short name), can be comma-separated list
  --experiment TEXT  experiment (short name), can be comma-separated list
  --gcm TEXT         global climate model, can be comma-separated list
  --yearmin TEXT     minimum year
  --yearmax TEXT     maximum year
  --mergeperiods     merge yearly files into user-defined periods
  --periods TEXT     user-defined periods, can be comma-separated list
  --slicebbox        slice files based on bounding box
  --bbox TEXT        bounding box (minx, miny, maxx, maxy)
  --help             show this message and exit
```
