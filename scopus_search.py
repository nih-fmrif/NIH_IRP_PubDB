from __future__ import print_function, unicode_literals

import argparse
import csv
import os
import requests
import sys

SCOPUS_SEARCH_API_URL = "http://api.elsevier.com/content/search/scopus"
CSV_COLUMN_HEADERS = (
    "Title", "PI", "Authors", "Date", "Cited-By Count", "Source Title", "Page Range",
    "DOI", "PubMed ID", "Scopus ID", "EID", "Type", "Funding Agency",
    "Abstract Link", "Scopus Link", "Cited-By Link"
)

# fields determined from this table:
# http://api.elsevier.com/documentation/search/SCOPUSSearchViews.htm
FIELDS = "dc:title,authid,given-name,surname,prism:coverDate,citedby-count," + \
         "prism:publicationName,prism:pageRange,prism:doi,pubmed-id," + \
         "dc:identifier,eid,subtypeDescription,fund-acr,link-self,link-scopus," + \
         "link-scopus-citedby"

def query_scopus(query_id, query_str, outfile):

    headers = {"X-ELS-APIKey": SCOPUS_API_KEY}
    params = {
        "field": FIELDS,
        "query": query_str,
        "count": 100,
        "start": 0
    }

    with open(outfile, "w") as output:
        writer = csv.writer(output)
        writer.writerow(CSV_COLUMN_HEADERS)

        entry_count = 0
        page_count = 0

        while True:
            r = requests.get(
                SCOPUS_SEARCH_API_URL,
                params=params,
                headers=headers
            )

            if r.status_code != 200:
                print("Error:")
                print(r.reason)
                break

            body = r.json()
            results = body.get("search-results")

            if results is None:
                print("Error:")
                print(body)
                break

            page_count += 1

            # Extract information for each result on this page
            for entry in results["entry"]:
                title = entry.get("dc:title", "")

                author_set = set()

                author_list = entry.get("author", [])

                for author in author_list:
                    try:
                        name = author.get("given-name", "") + " " + \
                               author.get("surname", "")
                        author_set.add(name)
                    except:
                        continue

                if author_list[-1].get("auth_id") in query_ids:
                    # If last author in the author list is a PI,
                    # set PI to last listed author
                    pi = author_list[-1].get("surname", "")
                else:
                    # Else, the PI is the first in the author list
                    pi = author_list[0].get("surname", "")

                date = entry.get("prism:coverDate", "")
                citedby_count = entry.get("citedby-count", 0)
                pub = entry.get("prism:publicationName", "")
                page_range = entry.get("prism:pageRange", "")
                doi = entry.get("prism:doi", "")
                pubmed_id = entry.get("pubmed-id", "")
                scopus_id = entry.get("dc:identifier", "")
                eid = entry.get("eid", "")
                subtype = entry.get("subtypeDescription", "")
                fund_acr = entry.get("fund-acr", "")

                abstract_link = ""
                scopus_link = ""
                citedby_link = ""

                for linkobj in entry["link"]:
                    if linkobj["@ref"] == "self":
                        abstract_link = linkobj["@href"]
                    if linkobj["@ref"] == "scopus":
                        scopus_link = linkobj["@href"]
                    if linkobj["@ref"] == "scopus-citedby":
                        citedby_link = linkobj["@href"]

                authors = ";".join(author_set)

                writer.writerow((
                    title.encode("utf-8"), pi.encode("utf-8"),
                    authors.encode("utf-8"), date, citedby_count,
                    pub.encode("utf-8"), page_range, doi, pubmed_id, scopus_id,
                    eid, subtype, fund_acr, abstract_link, scopus_link,
                    citedby_link
                ))

                entry_count += 1

            # account for pagination
            start = int(results["opensearch:startIndex"])
            total = int(results["opensearch:totalResults"])
            per_page = int(results["opensearch:itemsPerPage"])

            # print("Start: %d, Total: %d, Per Page: %d" % (start, total, per_page))
            if start + per_page >= total:
                break

            # update "start" index for "next" page of results
            params["start"] = start + per_page

        print("%d results on %d pages" % (entry_count, page_count))


def create_query(fname):
    query_ids = set()
    query_str = ""

    with open(fname, 'r') as f:
        for line in f:
            if not line.startswith("#"):
                query_ids.add(line.strip())

    # Join all but the last AU-IDs with "OR"
    for au_id in list(query_ids)[:-1]:
        query_str += "AU-ID(" + au_id + ") OR "

    # Append the last AU-ID without the trailing "OR", and the date search
    # parameter
    # TODO: remove hard coded date
    query_str += "AU-ID(" + list(query_ids)[-1] + ") AND ORIG-LOAD-DATE AFT 20150807"
    return query_ids, query_str


if __name__ == "__main__":
    description = """Query Scopus Search API and output to csv file."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("fname", help="Scopus search file")
    parser.add_argument("outfile", help="Output CSV filename")
    # TODO: add args for file query or cli query
    args = parser.parse_args()

    SCOPUS_API_KEY = os.getenv("SCOPUS_API_KEY")

    if not SCOPUS_API_KEY:
        sys.exit("You must set the SCOPUS_API_KEY environment variable.")

    query_ids, query_str = create_query(args.fname)
    query_scopus(query_ids, query_str, args.outfile)
