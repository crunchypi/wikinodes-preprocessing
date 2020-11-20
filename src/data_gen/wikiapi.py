'''
Used to pull data from wikipedia using the
wikipedia python module.

    - pull_articles():  Fetches data from wiki, using
                        a list of article names, and
                        returns a list of ArticleData

'''


import time
import wikipedia
# // Convenience.
from wikipedia.wikipedia import WikipediaPage
#
# // What this module should ultimately generate.
from src.typehelpers import ArticleData

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
API_PAUSE_SEC = 1




def __pull(title:str, ttl=5)-> WikipediaPage:
    ''' Recursively tries to pull API data.
        If <title> is not found on Wikipedia,
        a best match will be attempted
        recursively until <ttl> hits 0.
    '''
    # // Exit strategy for recursion.
    if ttl <= 0:
        return None
    try:
        # // Impose voluntary hard rate-limit.
        time.sleep(API_PAUSE_SEC)
        return wikipedia.page(title, auto_suggest=False)
    except wikipedia.exceptions.DisambiguationError as e:
        opt = e.options # // Brevity.
        # // Recursive attempt.
        return __pull(title=opt[0], ttl=ttl-1) if opt else None



def pull_articles(titles:list, topics:list=[]): # // -> Generator
    ''' Use a list of article <titles> to create
        and return a generator which pulls
        articles from wiki (API) and gives them
        as src.typehelpers.ArticleData instances.

        If <topics> is provided, then each yielded
        ArticleData will get an attached topic --
        the match is done by index. Example:
            ArticleData of title[0] will have
            topics[0] as topic.
    '''

    for i, title in enumerate(titles):
        data = __pull(title=title)
        # // Negate empty yield.
        if not data:
            continue

        article_data = ArticleData(
            title=title,
            url=data.url,
            content=data.content,
            links=data.links,
            html=data.html()
        )
        if len(topics) > i:
            article_data.topic = topics[i]

        yield article_data