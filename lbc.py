#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests, sqlite3, re
from datetime import datetime
from lxml import html
from PyRSS2Gen import RSS2, RSSItem, Guid


def extract_offers(url):
    if isinstance(url, requests.Response):
        tree = html.fromstring(url.text)
    else:
        page = requests.get(url, timeout=2)
        tree = html.fromstring(page.text)

    return tree.xpath('//div[@class="list-lbc"]/a/@href')


re_id = re.compile('.*/(?P<id>[0-9]+)\.htm.*')
conn = sqlite3.connect('lbc.sqlite')
curs = conn.cursor()

conn.execute('CREATE TABLE IF NOT EXISTS offers_seen (id INTEGER PRIMARY KEY, title TEXT, link TEXT, description TEXT, date TEXT default CURRENT_TIMESTAMP)')


def scrape_url(url):

    main_page = requests.get(url, timeout=2)
    tree = html.fromstring(main_page.text)

    offers = []
    offers.extend(extract_offers(main_page))

    # Handling of next pages via paging links
    already_seen = []
    for u in tree.xpath('//ul[@id="paging"]//a/@href'):
        if u in already_seen: continue
    
        already_seen.append(u)
        offers.extend(extract_offers(u))

    return offers


def scrape_offers(offer_urls):

    items = []
    for o in offer_urls:
        m = re_id.match(o)
        if not m:
            continue
        else:
            article = { 'title': '', 'link': o, 'description': '', 'guid': Guid(o), 'pubDate': datetime.now(), }
            curs.execute('INSERT OR IGNORE INTO offers_seen (id) VALUES (?);', (m.group('id'), ))
            if curs.rowcount > 0:
                page = requests.get(o, timeout=2)
                tree = html.fromstring(page.text)
                for n in tree.xpath('//div[@class="lbcContainer"]//*'):
                    if n.tag == 'h2' and 'id' in n.attrib and n.attrib['id'] == 'ad_subject':
                        article['title'] = unicode(n.text.strip())
                    elif n.tag == 'th':
                        article['description'] += u"\n" + unicode(n.text.strip())
                    elif  n.tag == 'td' or \
                         (n.tag == 'span' and 'class' in n.attrib and n.attrib['class'] == 'price'):
                        article['description'] += unicode(n.text.strip())
                    elif n.tag == 'div' and 'class' in n.attrib and n.attrib['class'] == 'content':
                        article['description'] += u"\n\n" + unicode(n.text.strip())
                    elif n.tag == 'br' and n.tail:
                        article['description'] += u"\n" + unicode(n.tail.strip())

                if article['description']:
                    article['description'] = "<pre>%s</pre>" % (article['description'].strip(), )

                curs.execute('UPDATE offers_seen SET title = ?, link = ?, description = ? WHERE id = ?;',
                    (article['title'], article['link'], article['description'], m.group('id')) )
            else:
                curs.execute('SELECT title, description, date FROM offers_seen WHERE id = ?;', (m.group('id'), ))
                for title, description, date in curs:
                    article['title'] = title
                    #article['link'] = o
                    article['description'] = description
                    #article['guid'] = Guid(o)
                    article['pubDate'] = datetime.strptime(date.decode('utf-8'), '%Y-%m-%d %H:%M:%S')

            items.append(article)

    conn.commit()
    return items


if __name__ == '__main__':

    my_searchs = [
        ( u'Locations IdF', 'http://www.leboncoin.fr/locations/offres/ile_de_france/?f=a&th=1&mrs=350&mre=750', 'location_idf.rss'),
        ( u'Citroën C4 Bourgogne', 'http://www.leboncoin.fr/voitures/offres/bourgogne/?f=a&th=1&q=C4', 'C4_71.rss'),
    ]
    RSS_root = '/var/www/html/'
    URL_root = 'http://www.my_web_site.wtf/'
    
    for title, url, filename in my_searchs:
        offers = scrape_url(url)
        rss = RSS2(
            title = title.encode('utf-8'), link = URL_root + filename, description = title.encode('utf-8'), lastBuildDate = datetime.now(),
            items = [ RSSItem(**article) for article in scrape_offers(offers) ]
        )
        rss.write_xml(open(RSS_root + filename, "w"), encoding='utf-8')

    curs.execute("DELETE FROM offers_seen WHERE date < DATETIME('now', '-90 day');")
    curs.execute("VACUUM;")
    conn.commit()
    conn.close()

