'''
Main works as CLI tool for orchestrating
submodule scripts -- meant to be 'thin glue'
for the other modules in this project.

See mod lvl <CLI_HELP> str for more info.

Convention:
    argument should be named as its mapped function
    (see cli_actions()) and the module it uses. So 
    arg x should use func x which uses the in x mod.

    For uniformity, each task function should 
    have the same signature as dev() in this mod.
'''

import sys
import os

from src.typehelpers import ArticleData
from src.typehelpers import db_spec_wikidata_label
from src.typehelpers import db_spec_fulltext_index

from src.data_gen.titles import load_titles
from src.data_gen.wikiapi import pull_articles
from src.neo4j_tools.comm import Neo4jComm

from src.linking.hyperlinks.linker import link as hyperlinked_link

# // Acts as documentation -- also used as 
# // 'help' printout for CLI
CLI_HELP = '''
-------------------------------------------------
CLI tool for orchestrating scripts in submodules.
-------------------------------------------------
Baic usage:
    Arguments are partially sensitive to position.
    State between arguments is kept, meaning that
    if arg2 needs data from arg1, then it will work
    as long as arg1 comes before arg2, even with an
    arbitrary amount args in-between.


Arguments:
    -titles         Specify path where article
                    names are listed.

    -wikiapi        Uses data generated from 
                    <-titles> arg to pull data
                    from wikipedia. This arg
                    expects a value specifying
                    the amount of subsearches for
                    each article. These sub-searches
                    are based on hyperlinks in each
                    article. 0 = None.

    -neo4j          Prepare a neo4j interface obj.
                    Arg vals are expected to be:
                        -neo4j uri,usr,pwd
    
    -createdb       Pushes data created with
                    -wikiapi into the neo4j db.
                    This arg has to come after
                        -wikiapi (for data)
                        -neo4j (for db connection).
                    
    -link          Try linking wiki nodes in neo4j.
                   Note: expects -neo4j arg to be
                   used before this one.

Examples:
    Use data in './data/titles_min.txt' to fetch article
    names and use that to retrieve data from wikipedia:
    > -titles ./data/titles_min.txt -wikiapi 0

    Previous example but with pushing data into Neo4j (
    each argument is a new line for formatting purposes):
    >   -titles ./data/titles_min.txt
        -wikiapi 0
        -neo4j neo4j://localhost:7687,neo4j,neo4j
        -createdb

    Link nodes in db.
    > -neo4j neo4j://localhost:7687,neo4j,neo4j -link

'''


def cli_actions()-> dict:
    ''' Binds CLI arguments to funcs. 
        Keys are CLI argument identifiers,
        while vals are used as such:
            [0] Does this arg expect a value?
                if not, then the next item in
                sys.argv will be interpreted as 
                another arg.

            [1] associated function.
    '''
    return {
        # // reserved for development     # // 
        '-inspect'  : [False, inspect],
        '-devhook'  : [False, devhook],
        # // ---------------------------- # //
        '-titles' : [True, titles],
        '-wikiapi'  : [True, wikiapi],
        '-neo4j'    : [True, neo4j],
        '-createdb': [False, createdb],
        '-link'     : [False, link]
    }


def inspect(arg_id, arg_val, state):
    '@@ reserved hook for inspecting state'
    state_fmt = ''
    # // ''.join has an issue with \n
    for k, v in state.items():
        state_fmt += f'\n\t {k} : {v}'
    print("Current State:" + state_fmt)
    

def devhook(arg_id, arg_val, state):
    ''' @@ reserved for development; recieve <state> 
        for hooking up experimental modules.
    '''
   

def titles(arg_id, arg_val, state):
    # // Handle file doesn't exist.
    assert os.path.exists(arg_val), f'''
        Used the following:
            Arg: '{arg_id}'
            Val: '{arg_val}'
        
        ...but the val is not a valid filename.
    '''
    state[arg_id] = load_titles(path=arg_val)


def wikiapi(arg_id, arg_val, state):
    try:
        arg_val = int(arg_val)
    except: 
        print(f'''
        Used the following:
            Arg: '{arg_id}'

        ..but the following value was not
        a integer. Got: '{arg_val}'
        ''')
        return

    # // Try accessing necessary state data.
    gen_titles = state.get('-titles')
    assert gen_titles is not None, '''
        Used the following:
            Arg: '{arg_id}'

        ..but could not access a state which
        contains valid wikipedia article titles.
        Use -titles argument before this one.
    '''

    # // Construct 'piped generator'. This is the
    # // first layer where article title gen.
    # // is converted to ArticleData gen.
    g  = (
        pull_articles(
            titles=[title],
            subsearch=arg_val
        )
        for title in gen_titles
    )
    # // State unwraps sub gen.
    state[arg_id] = (
        sub for sub in g for sub in sub
    )


def neo4j(arg_id, arg_val, state):
    arg_val = arg_val.split(',')
    assert len(arg_val) == 3, f'''
        Used the following:
                Arg: '{arg_id}'
        .. but the following value did not 
        contain the right amount of into.
        Should be: 
            <uri>,<usr>,<pwd>
        Got:
            {','.join(arg_val)}
    '''
    # // Instantiate neo4j communication tool
    uri, usr, pwd = arg_val
    # // Safety for pesky connection issues.
    try:
        state[arg_id] = Neo4jComm(
            uri=uri, usr=usr, pwd=pwd)
    except Exception as e:
        raise ValueError(f'''
            Error while setting up Neo4j interface.
            Ensure correct uri, usr and/or pwd. And
            that Neo4j is running.
            Msg: {e}
        ''')

def createdb(arg_id, arg_val, state):
    # // Try fetch data.
    gen_article_data = state.get('-wikiapi')
    assert gen_article_data is not None, '''
        Tried to create a database but data
        is missing. Use -wikiapi arg before this.
    '''
    # // Try retrieve neo4j obj
    n4jc = state.get('-neo4j')
    assert n4jc != None, '''
        Tried to create a database but the
        object used for neo4j communication
        is missing. Use -neo4j arg before this.
    '''
    try:
        n4jc.create_ftindex(
            name=db_spec_fulltext_index,
            label=db_spec_wikidata_label,
            # // Refers to the content property of
            # // ArticleData (in typehelpers.py).
            prop='content'
        )
    except:
        pass

    for article_data in gen_article_data:
        assert type(article_data) is ArticleData, '''
            Tried to create a db but the type inside
            generator (made with -wikiapi) is unexpected.
        '''

        n4jc.push_node(
            label=db_spec_wikidata_label,
            # // Load everything from ArticleData
            # // into the database.
            props=article_data.__dict__
        )

   
def link(arg_id, arg_val, state):
    # // Try retrieve neo4j obj
    n4jc = state.get('-neo4j')
    assert n4jc != None, '''
        Tried to create a database but the
        object used for neo4j communication
        is missing. Use -neo4j arg before this.
    '''
    # // Call linking routine; vals of <title_key> and
    # // <hlink_key> refer to properties of ArticleData
    # // found in typehelpers.py.
    hyperlinked_link(
            n4jcomm=n4jc,
            title_key='title',
            hlink_key='links'
    )


def start():
    'Point of entry of CLI'

    # // List of arguments.
    args = sys.argv[1:]
    if len(args) == 0 :
        print(CLI_HELP)
        return
    # // Keeps shared state between arguments. It is
    # // passed as an arg to each task func, where old or
    # // previous state is accessed and new state is set.
    state = {}

    # // Odd looping because it enables argument jumping.
    # // Some arguments don't accept values, while others
    # // do, so having flexibility in iteration is good.
    i = 0
    while i < len(args):
        step = 1
        try:
            # // Assumed to be a recognised arg.
            current_arg = args[i]
            # // Unpack for readability and check if arg is valid.
            arg_targets = cli_actions().get(current_arg)
            assert arg_targets, f'Unrecognised arg: {current_arg}'
            # // Unpack vals for readability.
            next_is_val, func = arg_targets
            # // Optional val for current arg.
            arg_val = args[i+1] if next_is_val else None
            # // Use task func of current arg&val.
            func(current_arg, arg_val, state)
            # // Adding potential step.
            step += 1 if next_is_val else 0

        except Exception as e:
            print(f'issue on arg "{args[i]}": '+ 
                    f'\n\tException: {e}')

            print("\n\n", CLI_HELP)
            # // Failed; no point in continuing
            return
        finally:
            # // In either case; increment counter.
            i += step

start()
