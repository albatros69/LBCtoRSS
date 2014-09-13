LBCtoRSS
========

Script pour convertir une recherche sur leboncoin.fr en flux RSS

Installation
------------
Il suffit de récupérer le script (par clonage du dépôt github par exemple).
Les dépendances à installer sont :
 * [requests](http://docs.python-requests.org/en/latest/) : `$ pip install requests`
 * [lxml](http://lxml.de/) : `$ pip install lxml` (cela peut nécessiter l'installation des librairies xml et xlst, typiquement sous debian `$ sudo apt-get install libxml2-dev libxslt-dev`)
 * [PyRSS2Gen](http://www.dalkescientific.com/Python/PyRSS2Gen.html) : `$ pip install PyRSS2Gen`
 * [docopt](http://docopt.org/) : `$ pip install docopt`
 * [sqlite3](https://pysqlite.readthedocs.org/en/latest/sqlite3.html)
ou plus simplement : `pip install -r requirements.txt`

Vous pouvez ensuite ajouter une tâche CRON (`$ crontab -e`) ressemblant à :
    
    # Scraping LBC
    37  */2     *   *   *   cd $HOME/lbc ; /usr/bin/python $HOME/lbc/lbc.py


Paramétrages
------------
Pour customiser ce script, il faut d'abord spécifier les recherches dans
la liste `my_searchs`. Elle est composée de tuples contenant le titre du
flux RSS, l'URL de la recherche sur leboncoin.fr et le nom du fichier RSS
destination.

Il faut aussi spécifier le répertoire qui contiendra les fichiers RSS (prévoir
de donner les droits en écriture à l'utilisateur qui exécutera le script) et 
l'URL du site web où seront hébergés les flux RSS.

Fonctionnement
--------------
Pour chaque recherche définie, le script requête le site leboncoin.fr et parse
cette page à la recherche des annonces, puis des pages suivantes de résultats.
Ensuite, il va récupérer les annonces dans chacune de ces dernières.

Chacune des annonces est stockée dans une base SQLite. Cela permet de ne pas
récupérer à chaque exécution l'intégralité des annonces, mais de quand même produire
un fichier RSS complet. Le fichier SQLite sera stocké au même endroit que le script 
Python.

Arguments
--------------
`--ovh`
> Le Bon Coin bloque le range d'IP des serveurs ovh, mais en passant par l'ip et non
> l'alias DNS il est néanmoins possible de faire des requêtes.
> Cette option change donc www.leboncoin.fr par l'ip contenue dans la variable `ovh_ip`.
