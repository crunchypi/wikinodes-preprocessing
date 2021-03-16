'''
This module contains some standardization
for the purpose of convenience in this project
(a few vars to reduce hardcoding + typed dict).
'''

# // Label of wikipedia article nodes.
db_spec_wikidata_label = 'WikiData'
# // 'Label' of links between wiki article nodes.
db_spec_wikidata_link = 'HYPERLINKS'
# // Name of fulltext index.
db_spec_fulltext_index = 'ArticleContentIndex'


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
