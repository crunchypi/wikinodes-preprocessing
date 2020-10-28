'''
This module is meant for automating the process of parsing
article names from .txt lists such that they can be used
to fetch wiki data with APIs.

Impl:
    -   ArticleList: Class for typehinting
    -   load_articles: parses .txt file
        containing topic- and article names.
        See func docstring for more details.

'''





class ArticleList:
    'Used for typehinting'
    def __init__(self, topic:str, article_names:list):
        self.topic = topic
        self.article_names = article_names



def load_articles(path:str, delimiter:str='\t'): # // -> gen
    ''' Returns a generator which pulls content from
        <path> and gives ArticleList objects. The file
        at <path> is expected to have a very specific
        format:
            -   '#' are ignored lines, used for commenting
            -   '[TOPIC=XYZ]' denotes topic start and end.
                Everything below this notation should be
                a list of article names -- they will be
                assigned to the current topic.

        <delimiter> is used to specify how copypaste topics
        are separated.
    '''
   
    # // Unsafe -- allowing crash.
    with open(path, 'r') as f:
        current_topic = ''
        for row in f:
            # // Drop comments.
            if '#' in row: 
                continue

            # // Drop empty rows.
            if row.replace(' ', '').replace('\n', '') == '':
                continue

            # // Set new topics.
            if 'TOPIC' in row:
                # // Remove formatting, only topic name remains.
                current_topic = row
                for elm in ['TOPIC', '[', ']', '=', ' ', '\n']:
                    current_topic = current_topic.replace(elm, '')
                continue

            # // Add res content as list.
            row = row.replace('\n', '').split(delimiter)
            yield ArticleList(
                topic=current_topic,
                article_names=row
            )

