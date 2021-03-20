'''
This module is meant for automating the process of parsing
article names from .txt lists such that they can be used
to fetch wiki data with APIs.

Impl:
    -   load_titles: parses .txt file
        containing article names.
        See func dostring for more details.
'''


def load_titles(path:str, delimiter:str='\n'): # // -> gen
    ''' Returns a generator which pulls titles from
        <path>, where all titles are delimited with
        <delimiter> (empty and commented lines are ignored).

        <delimiter> is used to specify how copypaste topics
        are separated.
    '''
   
    # // Unsafe -- allowing crash.
    with open(path, 'r') as f:
        for line in f:
            # // Prob not a problem but include for safu.
            if len(line)==0:
                continue
            # // Ignore comments.
            if line[0]=='#':
                continue
            # // Ignore empty lines.
            if line =='\n':
                continue

            yield line.replace('\n', '')

