from __future__ import print_function, unicode_literals

import argparse
import csv
import os
import requests
import sys
import pandas as pd

SCOPUS_SEARCH_API_URL = "http://api.elsevier.com/content/search/scopus"
CSV_COLUMN_HEADERS = (
    "Title", "PI", "Authors", "Date", "Cited-By Count", "Source Title", "Page Range",
    "DOI", "PubMed ID", "Scopus ID", "EID", "Type", "Funding Agency",
    "Abstract Link", "Scopus Link", "Cited-By Link"
)

def query_scopus(eids, outfile):
    auth_ids = set()
    missed = []
    with open('au-ids.txt', 'r') as f:
        for line in f:
            if not line.startswith("#"):
                auth_ids.add(line.strip())

    headers = {"X-ELS-APIKey": SCOPUS_API_KEY}

    with open(outfile, "w") as output:
        writer = csv.writer(output)
        writer.writerow(CSV_COLUMN_HEADERS)

        for eid in eids:
            params = {
                "view": "COMPLETE",
                "query": "eid(" + str(eid[0]) + ")",
            }

            try:
                r = requests.get(
                    SCOPUS_SEARCH_API_URL,
                    params=params,
                    headers=headers
                )
            except requests.exceptions.Timeout:
                sys.stdout.write("T")
                sys.stdout.flush()
                failed.append(eid)
                time.sleep(2)
                continue

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

            entry = results.get('entry')[0]
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


            pi = eid[1]

            date = entry.get("prism:coverDate", "")
            citedby_count = entry.get("citedby-count", 0)
            pub = entry.get("prism:publicationName", "")
            page_range = entry.get("prism:pageRange", "")
            doi = entry.get("prism:doi", "")
            pubmed_id = entry.get("pubmed-id", "")
            try:
                scopus_id = entry.get("dc:identifier", "").split(":")[1]
            except:
                print(eid)
                if eid not in missed:
                    missed.append(eid)
                scopus_id = 'NA'
                continue

            #eid = entry.get("eid", "")
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

    with open('missed_edids.txt', 'w') as f:
        for item in missed:
            f.write("%s\n" % ','.join(item))


def get_eids(fname):
    """pull the eids whose data we desire"""
    query_ids = set()
    query_str = ""

    print("[+] Gathering EIDS")
    dat = pd.read_csv(fname)
    if 'PI' in dat.columns.tolist():
        eids = [tuple(x) for x in dat[['EID', 'PI']].to_numpy()]
    else:
        dat.rename(columns={'SearchedAuthor':'PI'}, inplace=True)
        eids = [tuple(x) for x in dat[['EID', 'PI']].to_numpy()]

    return eids


if __name__ == "__main__":
    description = """Query Scopus Search API and output to csv file."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--ids", dest="fname", help="File with EIDs to query",
                        metavar="idfile", required=True)
    parser.add_argument("--out", dest="outfile", help="Output CSV filename",
                        metavar="output", required=True)
    # TODO: add args for file query or cli query
    args = parser.parse_args()

    SCOPUS_API_KEY = os.getenv("SCOPUS_API_KEY")

    if not SCOPUS_API_KEY:
        sys.exit("You must set the SCOPUS_API_KEY environment variable.")

    eids = get_eids(args.fname)
    query_scopus(eids, args.outfile)
