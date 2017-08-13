from __future__ import print_function, unicode_literals

import argparse
import csv
import os
import requests
import sys
import time

SCOPUS_SEARCH_API_URL = "http://api.elsevier.com/content/search/scopus"

def get_eids_from_file(fname):
    """Return a list of EIDs given a csv file of citation counts."""
    _eids = []
    print("[+] Get list of EIDs from %s..." % fname)
    with open(fname) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            _eids.append(row["EID"])
    return _eids


def scopus_query_citation_count(eidlist):
    """Take a list of EIDs and return a dictionary of EID -> citation_count
    mapping."""
    eiddict = {}
    failed = []
    failed_count = 0
    max_failed_attempts = 5
    headers = {"X-ELS-APIKey": SCOPUS_API_KEY}

    sys.stdout.write("[+] Query EIDs from SCOPUS Search API")
    sys.stdout.flush()

    while failed_count < max_failed_attempts:
        if failed_count == 0:
            eidlist = eidlist
        else:
            eidlist = failed
            sys.stdout.write("[+] Retrying failed EIDs from SCOPUS Search API")
            sys.stdout.flush()

        for eid in eidlist:
            params = {
                "field": "eid,citedby-count",
                "query": "eid(" + eid + ")"
            }

            try:
                r = requests.get(
                    SCOPUS_SEARCH_API_URL,
                    params=params,
                    headers=headers,
                    timeout=3
                )
            except requests.exceptions.Timeout:
                sys.stdout.write("T")
                sys.stdout.flush()
                failed.append(eid)
                time.sleep(2)
                continue

            if r.status_code != 200:
                sys.stdout.write("F")
                sys.stdout.flush()

                if eid not in failed:
                    failed.append(eid)

                time.sleep(2)
                continue

            if failed_count > 0:
                failed.remove(eid)

            body = r.json()
            results = body.get("search-results")

            if results is None:
                sys.stdout.write("N")
                sys.stdout.flush()
                continue

            # Extract information for each result on this page
            entry = results.get("entry")[0]
            eid = entry.get("eid")
            citedby_count = entry.get("citedby-count", "0")

            if eid:
                eiddict.update({eid: citedby_count})
                sys.stdout.write(".")
                sys.stdout.flush()

        if failed:
            failed_count += 1
            print()

    return eiddict


def write_csvfile(fname, output, eiddict):
    """Writes input csv file with the Cited By column updated."""
    print("[+] Writing to updated citation counts to %s" % output)
    with open(fname) as csvfile:
        reader = csv.DictReader(csvfile)
        fields = reader.fieldnames
        with open(output, "w") as outfile:
            fieldnames = fields
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                old_cited_by = row["Cited By"]
                new_cited_by = eiddict.get(row["EID"])
                if not new_cited_by:
                    new_cited_by = old_cited_by

                writer.writerow({
                    "Cite Rank": row["Cite Rank"],
                    "IC": row["IC"],
                    "PI": row["PI"],
                    "PI Count":row["PI Count"],
                    "Authors": row["Authors"],
                    "Title": row["Title"],
                    "Year": row["Year"],
                    "Source title": row["Source title"],
                    "Cited By": new_cited_by,
                    "DOI": row["DOI"],
                    "Link": row["Link"],
                    "PubMed ID": row["PubMed ID"],
                    "Document Type": row["Document Type"],
                    "EID": row["EID"],
                    "SCOPUS_ID": row["SCOPUS_ID"],
                    "API Abstract Link": row["API Abstract Link"],
                    "Cited By Link": row["Cited By Link"],
                })


if __name__ == "__main__":
    description = """Take CSV file with EID column and output CSV file with
    updated citation counts."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--input", dest="fname", help="Citation count csv filename",
                        metavar="csvfile", required=True)
    parser.add_argument("--output", dest="output", help="Output CSV filename",
                        metavar="outfile", required=True)
    args = parser.parse_args()

    SCOPUS_API_KEY = os.getenv("SCOPUS_API_KEY")

    if not SCOPUS_API_KEY:
        sys.exit("You must set the SCOPUS_API_KEY environment variable.")

    eids = get_eids_from_file(args.fname)
    eiddict = scopus_query_citation_count(eids)
    write_csvfile(args.fname, args.output, eiddict)
