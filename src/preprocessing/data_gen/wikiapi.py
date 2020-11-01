'''
Used to pull data from wikipedia using the
wikipedia python module. 

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
from wikipedia.wikipedia import WikipediaPage

# !! NOTE: Due to vague documentation of <wikipedia>,
# !! some notes are added in this comment block.
# !! 
# !! If there are issues with BeautifulSoup exceptions, see:
# !!    https://github.com/goldsmith/Wikipedia/issues/107
# !!
# !! If there are ambiguity issues, see:
# !!    https://github.com/goldsmith/Wikipedia/issues/199
# !! 



# // Used for pausing API requests to avoid spamming.
# // Relying on this more than the wikipedia (mod)
# // ratelimit setting.
api_pause_sec = 1

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



def __pull(name:str, ttl=5)-> WikipediaPage:
    ''' Recursively tries to pull API data.
        If <name> is not found on Wikipedia,
        a best match will be attempted 
        recursively until <ttl> hits 0.
    '''
    # // Exit strategy for recursion.
    if ttl <= 0:
        return None
    try:
        # // Impose voluntary hard rate-limit.
        time.sleep(api_pause_sec)
        return wikipedia.page(name, auto_suggest=False)
    except wikipedia.exceptions.DisambiguationError as e:
        opt = e.options # // Brevity.
        # // Recursive attempt.
        return __pull(name=opt[0], ttl=ttl-1) if opt else None



def pull_articles(names:list): # // -> Generator
    ''' Use a list of article <names> to create
        and return a generator which pulls
        articles from wiki (API) and gives them
        as ArticleData instances.
    '''

    for name in names:                
        data = __pull(name=name)
        # // Negate empty yield.
        if not data:
            continue

        yield ArticleData(
            name=name,
            url=data.url,
            content_raw=data.content,
            links=data.links,
            html=data.html
        )