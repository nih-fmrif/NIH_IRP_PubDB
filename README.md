# NIH_IRP_PubDB
An application to catalog and measure NIH IRP publications.

# Usage

The list of AU-IDs should go in a text file, one AU-ID per line.  Comments are
optional.  Example `au-ids.txt`:

```
# Alice
0123456789
# Bob
1234567890
```

Then run **scopus_search.py**.  First argument is the file containing the
AU-IDs and the second argument is the output csv file:

```
python scopus_search.py au-ids.txt output.csv
```
