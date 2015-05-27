#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests, sqlite3 #, re, os
from time import sleep

conn = sqlite3.connect('lbc.sqlite')
curs = conn.cursor()

if __name__ == '__main__':

    curs.execute("SELECT COUNT(*) FROM offers_seen;")
    print curs.fetchone()[0], "annonces"
    curs.execute("DELETE FROM offers_seen WHERE date < DATETIME('now', '-61 day');")
    print curs.rowcount, "annonces de plus de 2 mois supprimées"
    offers_deleted = []
    for i, u in curs.execute("SELECT id, link FROM offers_seen WHERE date < DATETIME('now', '-10 day');"):
        try:
            r = requests.head(u, timeout=2)
            #print i, u, r.status_code
        except:
            sleep(2)
            continue
        if r.status_code != 200:
            offers_deleted.append(str(i))
        sleep(0.5)

    curs.execute("DELETE FROM offers_seen WHERE id in (%s);" % (",".join(offers_deleted), ));
    print len(offers_deleted), "annonces introuvables supprimées"
    curs.execute("VACUUM;")
    conn.commit()
    conn.close()

