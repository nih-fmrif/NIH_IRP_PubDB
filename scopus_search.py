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

def query_scopus(query_strs, outfile):

    headers = {"X-ELS-APIKey": SCOPUS_API_KEY}
    total_entries = 0
    eid_list = []
    with open(outfile, "w") as output:
        writer = csv.writer(output)
        writer.writerow(CSV_COLUMN_HEADERS)

        for pi in query_strs.keys():
            params = {
                "view": "COMPLETE",
                "query": query_strs[pi],
                "count": 25,
                "start": 0
            }
            page_count = 0
            pi_entries = 0

            print("[+] Sending " + pi + " query to SCOPUS Search API...")
            while True:
                r = requests.get(
                    SCOPUS_SEARCH_API_URL,
                    params=params,
                    headers=headers
                )
                time.sleep(.25)

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

                if results['opensearch:totalResults'] != '0':
                    page_count += 1

                    # Extract information for each result on this page
                    for entry in results["entry"]:
                        if entry.get("eid", "") not in eid_list:
                            title = entry.get("dc:title", "")

                            author_set = set()

                            author_list = entry.get("author", [])

                            for author in author_list:
                                firstname = author.get("given-name", "")
                                lastname = author.get("surname", "")

                                if firstname is None:
                                    firstname = ""

                                if lastname is None:
                                    lastname = ""

                                author_set.add(firstname + " " + lastname)

                            date = entry.get("prism:coverDate", "")
                            citedby_count = entry.get("citedby-count", 0)
                            pub = entry.get("prism:publicationName", "")
                            page_range = entry.get("prism:pageRange", "")
                            doi = entry.get("prism:doi", "")
                            pubmed_id = entry.get("pubmed-id", "")
                            scopus_id = entry.get("dc:identifier", "").split(":")[1]
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
                                title, pi,
                                authors, date, citedby_count,
                                pub, page_range, doi, pubmed_id, scopus_id,
                                eid, subtype, fund_acr, abstract_link, scopus_link,
                                citedby_link
                            ))

                            pi_entries += 1
                            eid_list.append(eid)

                # account for pagination
                start = int(results["opensearch:startIndex"])
                total = int(results["opensearch:totalResults"])
                per_page = int(results["opensearch:itemsPerPage"])

                # print("Start: %d, Total: %d, Per Page: %d" % (start, total, per_page))
                if start + per_page >= total:
                    print("[+] Done! %d records found." % (pi_entries))
                    break

                # update "start" index for "next" page of results
                params["start"] = start + per_page

            else:
                pass


def create_query(fname, start):
    """Generate query IDs and query string from input file and start date."""
    query_strs = {}
    query_dict = {}

    print("[+] Gathering AU-IDs...")
    query_dict = {}
    with open(fname, 'r') as f:
        local_ids = []
        for line in f:
            if line.startswith('#') and len(local_ids)==0:
                pi = line.strip()[2:].split(' ')[-1]
            if line.startswith('#') and len(local_ids)>0:
                query_dict[pi] = local_ids
                local_ids = []
                pi = line.strip()[2:].split(' ')[-1]
            if not line.startswith("#"):
                local_ids.append(line.strip())

        query_dict[pi] = local_ids
            

    # Join all but the last AU-IDs with "OR"
    for pi in query_dict.keys():
        query_strs[pi] = "AU-ID(" + ") OR AU-ID(".join(query_dict[pi]) + ") AND ORIG-LOAD-DATE AFT " + start

    return query_strs


if __name__ == "__main__":
    description = """Query Scopus Search API and output to csv file."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--ids", dest="fname", help="File with SCOPUS AU-IDs to query",
                        metavar="idfile", required=True)
    parser.add_argument("--out", dest="outfile", help="Output CSV filename",
                        metavar="output", required=True)
    parser.add_argument("--start", dest="start", help="Start date for query (YYYYMMDD).",
                        metavar="startdate", required=True)
    # TODO: add args for file query or cli query
    args = parser.parse_args()

    SCOPUS_API_KEY = os.getenv("SCOPUS_API_KEY")

    if not SCOPUS_API_KEY:
        sys.exit("You must set the SCOPUS_API_KEY environment variable.")

    query_strs = create_query(args.fname, args.start)
    query_scopus(query_strs, args.outfile)
