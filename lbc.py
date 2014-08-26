#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests, sqlite3, re
from datetime import datetime
from time import sleep
from lxml import html
from PyRSS2Gen import RSS2, RSSItem, Guid
from docopt import docopt


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
    if arguments['--ovh']:
        url = url.replace("www.leboncoin.fr", ovh_ip)
    main_page = requests.get(url, timeout=2)
    tree = html.fromstring(main_page.text)

    offers = []
    offers.extend(extract_offers(main_page))

    # Handling of next pages via paging links
    already_seen = []
    next_pages = list(tree.xpath('//ul[@id="paging"]//a/@href'))
    errors = 0
    while next_pages and errors <= 10:
        u = next_pages.pop(0)
        if arguments['--ovh']:
            u = u.replace("www.leboncoin.fr", ovh_ip)
        if u in already_seen: continue
    
        try:
            offers.extend(extract_offers(u))
        except requests.exceptions.Timeout:
            errors += 1
            sleep(2)
            next_pages.append(u)
        else:
            already_seen.append(u)

    return offers


def scrape_offers(offer_urls):

    items = []
    for o in offer_urls:
        m = re_id.match(o)
        if arguments['--ovh']:
            o = o.replace("www.leboncoin.fr", ovh_ip)
        if not m:
            continue
        else:
            article = { 'title': '', 'link': o, 'description': '', 'guid': Guid(o), 'pubDate': datetime.now(), }
	    img = u"\n"
            curs.execute('INSERT OR IGNORE INTO offers_seen (id) VALUES (?);', (m.group('id'), ))
            if curs.rowcount > 0:
                try:
                    page = requests.get(o, timeout=2)
                except requests.exceptions.Timeout:
                    # Pour récupérer l'annonce à la prochaine exécution
                    curs.execute('DELETE FROM offers_seen WHERE id=?;', (m.group('id'), ))
                    sleep(2)
                    continue

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
		    elif n.tag == 'span' and 'class' in n.attrib and n.attrib['class'] == 'thumbs':
			img += u"<p><img src=\"" + unicode(n.attrib['style'].split("'")[1].replace('thumbs', 'images')) + u"\"></p>"

                if article['description'] and img:
                    article['description'] = "<pre>%s\n%s</pre>" % (article['description'].strip(), img.strip(), )
                elif article['description']:
                    article['description'] = "<pre>%s</pre>" % (article['description'].strip(), )

	        if arguments['--ovh']:
		    article['link'] = article['link'].replace(ovh_ip, "www.leboncoin.fr")

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

    help = """LBCtoRSS
    
    Usage:
        lbc.py [--ovh]
    
    Options:
        -h --help     C'est généré automatiquement.
        --ovh         Change l'url du site le bon coin par une ip accessible depuis un serveur OVH.
    
    """
    
    arguments = docopt(help)
    ovh_ip = '193.164.196.13'

    my_searchs = [
	( u'Appartement Lyon 8', 'http://www.leboncoin.fr/ventes_immobilieres/offres/rhone_alpes/?f=a&th=1&ps=6&pe=9&sqs=7&ros=3&location=Lyon%2069008', 'Appart_69008.rss'),
	( u'Appartement Lyon 7', 'http://www.leboncoin.fr/ventes_immobilieres/offres/rhone_alpes/?f=a&th=1&ps=6&pe=9&sqs=7&ros=3&location=Lyon%2069007', 'Appart_69007.rss'),
	( u'Appartement Lyon 3', 'http://www.leboncoin.fr/ventes_immobilieres/offres/rhone_alpes/?f=a&th=1&ps=6&pe=9&sqs=7&ros=3&location=Lyon%2069003', 'Appart_69003.rss'),
	( u'Appartement Lyon 6', 'http://www.leboncoin.fr/ventes_immobilieres/offres/rhone_alpes/?f=a&th=1&ps=6&pe=9&sqs=7&ros=3&location=Lyon%2069006', 'Appart_69006.rss'),
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

