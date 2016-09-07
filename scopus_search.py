from __future__ import print_function
import requests
import argparse
import json
import sys
import csv
import codecs
import cStringIO
import os

# Authors,Title,Year,Source title,Volume,Issue,Art. No.,Page start,Page end,Page count,Cited by,Link,DOI,PubMed ID,Document Type,Source
# Authors, Title, Year, Source title, Cited by, Link, DOI, PubMed ID, Document Type, Source

class UnicodeCSVWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('query', help='Scopus search query')
    parser.add_argument('outfile', help='Output CSV filename')

    args = parser.parse_args()

    query = args.query
    if not query:
        parser.error('query string must be non-empty')

    headers = {}
    headers['Accept'] = 'application/json'
    headers['X-ELS-APIKey'] = os.getenv("SCOPUS_API_KEY")

    # authenticate to the API
    r = requests.get('http://api.elsevier.com/authenticate', params={'platform':'SCOPUS'}, headers=headers)
    jresp = r.json()
    print(jresp)
    sys.exit()
    authtoken = jresp['authenticate-response']['authtoken']

    # set authtoken header for subsequent requests
    headers['X-ELS-Authtoken'] = authtoken

    params = {}
    # fields determined from this chart: http://api.elsevier.com/documentation/search/SCOPUSSearchViews.htm
    # TODO: switch to manually specified fields instead of "COMPLETE view" once I figure out the "link" field
    # params['field'] = 'dc:identifier,dc:title,author,prism:coverDate,prism:publicationName,link ref=scopus,link ref=scopus-citedby,prism:doi,pubmed-id'
    params['view'] = 'COMPLETE'
    params['query'] = query
    params['count'] = 100
    params['start'] = 0

    outfile = open(args.outfile, 'wb')
    output = UnicodeCSVWriter(outfile)
    output.writerow(['Title', 'Authors', 'Date', 'Cited-By Count', 'Source Title',
            'Page Range', 'DOI', 'Type', 'Abstract Link', 'Scopus Link', 'Cited-By Link'])

    entry_count = 0
    page_count = 0
    while True:
        r = requests.get('http://api.elsevier.com/content/search/scopus', params=params, headers=headers)
        body = r.json()

        try:
            results = body['search-results']
        except:
            print("Error:")
            print(body)
            break

        page_count += 1

        # extract information for each result on this page
        for entry in results['entry']:
            # scopus_id = entry['dc:identifier']
            title = entry['dc:title']
            authors = set()
            for authobj in entry.get('author', []):
                try:
                    name = authobj.get('given-name', '') + ' ' + authobj.get('surname', '')
                    authors.add(name)
                except TypeError:
                    pass
            date = entry['prism:coverDate']
            citedby_count = entry.get('citedby-count', 0)
            pub = entry['prism:publicationName']
            page_range = entry.get('prism:pageRange', '')
            doi = entry.get('prism:doi', '')
            subtype = entry['subtypeDescription']
            # pubmed_id = entry['pubmed-id']
            abstract_link, scopus_link, citedby_link = '', '', ''
            for linkobj in entry['link']:
                if linkobj['@ref'] == 'self':
                    abstract_link = linkobj['@href']
                if linkobj['@ref'] == 'scopus':
                    scopus_link = linkobj['@href']
                elif linkobj['@ref'] == 'scopus-citedby':
                    citedby_link = linkobj['@href']

            output.writerow([title, ';'.join(authors), date, citedby_count, pub, page_range,
                    doi, subtype, abstract_link, scopus_link, citedby_link])

            entry_count += 1

        # account for pagination
        start = int(results['opensearch:startIndex'])
        total = int(results['opensearch:totalResults'])
        per_page = int(results['opensearch:itemsPerPage'])
        # print('Start: %d, Total: %d, Per Page: %d' % (start, total, per_page))
        if start + per_page >= total:
            break

        # update 'start' index for 'next' page of results
        params['start'] = start + per_page

    print('%d results on %d pages' % (entry_count, page_count))
    outfile.close()

if __name__ == '__main__':
    main()
