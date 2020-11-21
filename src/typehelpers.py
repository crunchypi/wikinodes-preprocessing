'''
This module contains types which are used
for convenience in this project. They do
not contain any methods (only vals) and 
only act as documentation and an 
alternative to just passing around dicts. 
'''





class TitleTopicPair:
    ''' Used for loading wiki titles and
        topics (pre-categorised) from disk.
        These are primarily meant to be
        used for pulling data from the
        Wikipedia API.
    '''
    def __init__(self, title:str, topic:str):
        self.title = title
        self.topic = topic


class ArticleData:
    ''' Used for containing wiki article 
        data pulled from Wikipedia. Also,
        this class acts as a Neo4j node
        template for related nodes (the
        __dict__ of this class will be 
        mirrored).
    '''
    def __init__( # // Don't hit me, blame google :<
            self, 
            title:str, 
            url:str,
            content:str, 
            links:list,
            html:str
    ):
        self.title = title
        self.url = url
        self.content = content
        self.links = links
        self.html = html
        # // This is intended to be attached
        # // after init. Cannot be None because
        # // Neo4j complained about null property.
        self.topic = ''