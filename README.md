# Le projet IDKIT 

Bienvenue sur le logiciel IDKIT !

## Contexte du développement de IDKIT
Ce logiciel est développé par Simon Buré, Lionel Dalmau, Mayoran Raveendran, Olivia Seffacene et Jesus Uxue Mendez dans le cadre du projet de développement logiciel de la 4^e^ année du parcours **Bioinformatique et Modélisation** du département **Biosciences**. Ce projet est encadré et supervisé par le Dr Sergio Peigner, le Dr David Parsons ainsi que Lisa Chabrier, étudiante en thèse et enseignante pour le département Biosciences.

## Raison d'être de IDKIT
IDKIT est un logiciel qui vise à utiliser l'intelligence artificielle pour générer des portraits robots. IDKIT permettrait de créer de toutes nouvelles images à partir d'un modèle d'intelligence artificielle et s'affranchit ainsi des limitations d'une simple banque de données d'images.

IDKIT veut pouvoir aider les témoins et les victimes à reconstituer un portrait robot fiable à partir de leurs souvenirs du visage de la personne suspecte. Les utilisateurs indiquent au logiciel quelles images ressemblent le plus au souvenir qu'ils ont du suspect et le logiciel modifie cette image pour en générer de nouvelle qui seront à nouveau proposées à l'utilisateur, jusqu'à ce que le résultat soit satisfaisant ou qu'un nombre maximum d'itérations ait été atteint.

## De quoi avez-vous besoin pour utiliser IDKIT ?
IDKIT a été conçu avec **python 3.10.6**, il est donc garanti de fonctionner avec cette version. IDKIT utilise également les dépendances suivantes, qu'il sera nécessaire d'installer si ce n'est pas déjà fait:
 - Pillow 9.4.0
 - numpy 1.24.2
 - setuptools 67.6.0 
 - PyTorch 1.13.1

Afin de ne pas perturber le pc actuel, il est recommandé d'installer la librairie dans un nouvel environnement virtuel.

Comment créer un environement virtuel : https://it.engineering.oregonstate.edu/setting-virtual-environments-python

Si ce n'est pas déja le cas, il est nécessaire d'installer pip pour installer les librairies nécessaire au fonctionnement du programme :

Linux : `sudo apt-get python3-pip `

`pip install pillow==9.4.0 numpy==1.24.2 torch==1.13.1`

## Comment installer et utiliser IDKIT ?
IDKIT est disponible sur `pip`, le package manager de python. Pour installer notre logiciel il suffit donc de taper dans une console python `pip install -i https://test.pypi.org/simple/ INSA-IdKit` ou alors, directement dans un terminal, `python3 -m pip install -i https://test.pypi.org/simple/ INSA-IdKit`. Ce n'est pas tout, pour pouvoir fonctionner correctement, IDKIT a besoin avant tout autre chose d'exécuter un script python, contenu dans un fichier `setup.py`. Ce fichier est diponible sur Github dans le dossier projet à l'adresse suivante : https://github.com/Fallog/PROJET_DEV_LOG. Ce script initialise l'environnement et l'arborescence de dossiers nécessaire à IDKIT pour stocker et retrouver les images entre autres.

Une fois les librairies installées, il est possible de lancer le programme avec la commande :

`python3 <path_to:>/Setup_user.py`

Le script python fourni permettra la création de l'environnement de travail du programme et l'éxécution de l'interface graphique associé.

Si un problème se présente ou pour désinstaller le logiciel il suffit de lancer la commande :

`python3 <path_to:>/Setup_user.py uninstall`

Rapide description des différents boutons et fonctionnalités implémentées

Description de IDKIT dans sa version actuelle ?

