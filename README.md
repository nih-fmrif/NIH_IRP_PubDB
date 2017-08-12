## NIH_IRP_PubDB

An application to catalog and measure NIH IRP publications.

### SCOPUS Search

```
usage: scopus_search.py [-h] --ids idfile --out output --start startdate

Query Scopus Search API and output to csv file.

optional arguments:
  -h, --help         show this help message and exit
  --ids idfile       Scopus search file
  --out output       Output CSV filename
  --start startdate  Start date for query (YYYYMMDD).
```

1. Export your `SCOPUS_API_KEY` environment variable:

```
export SCOPUS_API_KEY=1234567890abcdef1234567890abcdef
```

2. Prepare a list of AU-IDs to query.  These should go in a text file, one
   AU-ID per line.  Comments are optional.  Example `au-ids.txt`:

```
# Alice
0123456789
# Bob
1234567890
```

3. Run **scopus_search.py**.  First argument is the file containing the AU-IDs
   and the second argument is the output csv file:

```
python scopus_search.py --ids au-ids.txt --out output.csv --start 20160807
```
