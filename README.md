LBCtoRSS
========

Script pour convertir une recherche sur leboncoin.fr en flux RSS

Installation
------------
Il suffit de récupérer le script (par clonage du dépôt github par exemple).
Les dépendances à installer (de préférence dans un virtualenv) sont :
 * [requests](http://docs.python-requests.org/en/latest/) : `$ pip install requests`
 * [PyRSS2Gen](http://www.dalkescientific.com/Python/PyRSS2Gen.html) : `$ pip install PyRSS2Gen`

ou plus simplement : `$ pip install -r requirements.txt`

Vous pouvez ensuite ajouter une tâche CRON (`$ crontab -e`) ressemblant à :

    # Scraping LBC
    37  */2     *   *   *   cd $HOME/lbc ; ./bin/python lbc.py

À adapter évidement si vous n'utilisez pas un virtualenv.


Paramétrages
------------
Pour customiser ce script, il faut d'abord spécifier les recherches dans
la liste `my_searchs`. Elle est composée de tuples contenant le titre du
flux RSS, les paramètres de la recherche sur leboncoin.fr au format json
et le nom du fichier RSS destination.

Il faut aussi spécifier le répertoire qui contiendra les fichiers RSS (prévoir
de donner les droits en écriture à l'utilisateur qui exécutera le script) et
l'URL du site web où seront hébergés les flux RSS.

Fonctionnement
--------------
Pour chaque recherche définie, le script requête le site api.leboncoin.fr et
formatte le résulat reçu sous forme de fichiers RSS (un par recherche).

