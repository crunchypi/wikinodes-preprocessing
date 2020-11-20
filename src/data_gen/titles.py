'''
This module is meant for automating the process of parsing
article names from .txt lists such that they can be used
to fetch wiki data with APIs.

Impl:
    -   load_titles: parses .txt file
        containing topic- and article names.
        See func docstring for more details.

'''

from src.typehelpers import TitleTopicPair



def load_titles(path:str, delimiter:str='\t'): # // -> gen
    ''' Returns a generator which pulls content from
        <path> and gives src.data_gen.TitleTopicPair 
        objects. The file at <path> is expected to 
        have a very specific format:
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

            # // Row should be all titles on a single line.
            row = row.replace('\n', '').split(delimiter)
            for title in row:
                yield TitleTopicPair(
                    title=title,
                    topic=current_topic
                )
       
