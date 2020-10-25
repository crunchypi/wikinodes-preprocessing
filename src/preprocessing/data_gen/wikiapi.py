'''
Used to pull data from wikipedia.
Contains:
    - ArticleData:      Class for containing the 
                        data of wikipedia articles,
                        mainly used for typehints

    - pull_articles():  Fetches data from wiki, using
                        a list of article names, and
                        returns a list of ArticleData

'''


import time
import wikipedia

from typing import List

# // Used for pausing API requests to avoid spamming.
api_pause_sec = 2

class ArticleData:
    'Used for typehints'
    def __init__(self, name:str, url:str, 
                    content_raw:str, links:list, html:str):
        self.name = name
        self.url = url
        self.content_raw = content_raw
        self.links = links
        self.html = html

        # // Vars below are meant to be filled 
        # // down-the-line.

        self.content_clean = ""     # // Cleaned content.raw
        self.topics_prelinked = []  # // Topic assignment.
        self.topics_autolinked = [] # // Topic assignment.


def pull_articles(names:list)-> List[ArticleData]:
    ''' Use a list of article <names> to fetch data 
        from wiki. Returns a list of ArticleData.
    '''
    res = []
    for name in names:
        # // Impose additional rate-limit for 
        # // ethical reasons.
        time.sleep(api_pause_sec)
        # // Fetch and append data
        data = wikipedia.page(name)
        res.append(ArticleData(
            name=name,
            url=data.url,
            content_raw=data.content,
            links=data.links,
            html=data.html
        ))
    return res

