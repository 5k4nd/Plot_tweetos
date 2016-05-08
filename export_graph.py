#!/usr/bin/python2
# -*- coding: utf8 -*-
"""
@Bapt Abl, SI90, P16.

Ce script est une extension de https://github.com/medialab/gazouilloire et
doit être placé dans 'gazouilloire-master/bin/'.

Il recense et affiche les twittos twittant à propos de #digitalLabor (par exemple).
script standalone en tant que script (sauf pour gazouilloire/config.json), mais qui nécessite une
base de tweets habituellement construite avec gazouilloire.

ATTENTION :
    les tweets étudiés concernent uniquement un UNIQUE hashtag. on n'étudie
pas ici l'ensemble des tweets d'un tweetos (attention notamment pour le nombre
de tweets par twitto, c'est bien le "nombre de tweets relatifs AU SUJET ÉTUDIÉ
défini par le hashtag).


Les noeuds représentent des twittos. Deux twittos sont liés si l'un ou l'autre
a cité au moins une fois l'autre dans un tweet du hashtag. Plus un twitto est
foncé, plus il a tweeté sur le hashtag.


ToDo:
on pourrait afficher les images dans les noeuds

"""

import sys
import json
from pymongo import MongoClient

import networkx as nx
import matplotlib.pyplot as plt

import random



def extract_twittos_from_tweet(tweet):
    record = False
    twittos = []
    twitto = ''
    for char in tweet:
        if char is '@':
            record = True
        if record:
            if not char is " ":
                twitto += char
            else:
                record = False
        if not record:
            if twitto != '':
                twittos.append(twitto[1:].replace(
                    ':', '' # sometimes there is a ':'
                )) # remove the @
            twitto = ''

    return twittos

class Twitto:
    def __init__(self, id, label, name, profile_img):
        self.id = id
        self.label = label
        self.name = name
        self.profile_img = profile_img
        self.tweets = 1  # number of tweets
        self.neighbors = []  # filled with every @ in tweets from self


""" GRAPH :
  * noeud = twittos (label = @twittos)
  * couleur des noeuds = nb de tweets
  * liens entre les twittos = s'ils se citent les uns les autres
"""   


if __name__ == '__main__':
    # GET TWEETOS FROM DB
    twittos = {}  # {@label: Tweeto_object}

    with open('../config.json') as confile:
        conf = json.loads(confile.read())
    db = MongoClient(conf['mongo']['host'], conf['mongo']['port'])[conf['mongo']['db']]['tweets']

    tweets = db.find()
   
    for tweet in tweets:
        # ts = datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S +0000 Y').isoformat()
        
        label = tweet.get("user_screen_name")
        if label in twittos.keys():
            # twitto already in the db
            twitto = twittos[label]
            twitto.tweets += 1
        else:
            # we have to create the twitto
            user_id = int(tweet.get('user_id_str'))
            name = tweet.get("user_name", "")
            profile_img = tweet.get('user_profile_image_url')
            twitto = Twitto(user_id, label, name, profile_img)
            twittos[label] = twitto


        # getting neighbors
        for neighbor in extract_twittos_from_tweet(tweet.get('text').encode("utf-8")):
            if not neighbor in twitto.neighbors:
                twitto.neighbors += [neighbor]



    # GENERATE THE GRAPH
    G = nx.Graph()

    # create nodes
    for t in twittos.values():
        G.add_node(u'@'+t.label, tweets=t.tweets)
        for neighbor in t.neighbors:
            try:
                G.add_edge(u'@'+t.label, u'@'+unicode(neighbor))
            except:
                print repr(neighbor)

    # delete nodes with no tweets (generated from edges)
    for node in G.nodes(data=True):
        try:
            foo = node[1]['tweets']
        except:  # no tweets
            G.remove_node(node[0])


    plt.figure(figsize=(75, 75))
    plt.xlim(-1, 1)
    plt.ylim(-1, 1)
    plt.axis('off')
    

    node_colors = [node[1]['tweets'] for node in G.nodes(data=True)]
    node_positions = nx.spring_layout(G,
        # center=True,
    )

    # nx.draw_circular(G)
    # nx.draw_random(G)
    # nx.draw(G)
    nx.draw_networkx(G,
       node_size=500,
       pos=node_positions,
       font_size=10,
       # font_color='#a76613',
       font_color='red',
       node_color=node_colors,
       # cmap=plt.get_cmap('Oranges')
       cmap=plt.get_cmap('YlOrRd')  # http://matplotlib.org/examples/color/colormaps_reference.html
    )

    plt.savefig('../twittos.png')
