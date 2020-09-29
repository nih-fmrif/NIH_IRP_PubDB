## NIH_IRP_PubDB

An application to catalog and measure NIH IRP publications.

Assuming that the user is interested in updating these measures in subsequent years, follow these steps:

1. Check the authors in `au_ids.txt` to ensure all PIs are represented. [Note1: we have discovered that some of the EIDs in this file returned data from investigators not in the IRP]

2. Obtain a listing of the previously used publications in this analysis (henceforth: *old publications*).

3. Use the `scopus_search.py` script to obtain all the papers listed in scopus since a given date (henceforth: *new publications*). This script takes as input a list of investigators, and a cutoff date. [Note2: we have found that this function still returns some papers that precede the cutoff date]

4. Clean up the new publications, and distribute to the investigators so they can mark which papers of theirs used the scanners. [here](https://docs.google.com/spreadsheets/d/1w_00-0GV0OHPJxf1FsTi4oVQzbqitz6xmB5-1qMx-vQ/edit#gid=339438628) is a version of this spreadhseet from 2019.

5. Use the `update_citation_counts.py` script to update the number of citations for the *old publications*. This script takes as input the file produced in the previous year, and pulls all the unique EID (paper identifiers), updating the citation counts for those articles. We have experienced EIDs that change a bit year-to-year (on the order of one or two percent). Consequently, this script will print (and write to disk) EIDs that are missed. It is up to the user to go through an manually correct these by, for instance, creating a new csv file with a column labeled `EID` and using this as input for a second run of `update_citation_counts.py`. 

6. Download the completed tabulation of which *new publications* used the scanners.

7. The notebook `nih_irp_pubcount_workbook.ipynb` aggregates the data from the previous steps and generates a paragraph that describes the "productivity" of the reseaerch group as a whole. It also writes out a complete listing of papers for use next year. This notebook will rely on a PI <-> IC linking file (`investigator_ics.csv`)

There have been uneven historical attempts to remove editorials, reviews, errata, and the like. The above does not attempt to describe how that might happen.

### scopus_search.py

Search SCOPUS for publications given a list of AU-IDs.

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

### update_citation_counts.py

Given a CSV file with an EID for each publication, write to a CSV file with
updated citation counts for each publication.

```
usage: update_citation_counts.py [-h] --input csvfile --output outfile

Take CSV file with EID column and output CSV file with updated citation
counts.

optional arguments:
  -h, --help        show this help message and exit
  --input csvfile   Citation count csv filename
  --output outfile  Output CSV filename
```

1. Export your `SCOPUS_API_KEY` environment variable:

```
export SCOPUS_API_KEY=1234567890abcdef1234567890abcdef
```

2. Run the **update_citation_counts.py**: 

```
python update_citation_counts.py --input old_publist.csv --output updated_publist.csv
```
