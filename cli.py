'''
Main works as CLI tool for orchestrating
submodule scripts -- meant to be 'thin glue'
of loosly coupled modules (which should hide
complexity from this mod).

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

from typing import List
from src.typehelpers import TitleTopicPair
from src.typehelpers import ArticleData

from src.data_gen.titles import load_titles
from src.data_gen.wikiapi import pull_articles
from src.neo4j_tools.comm import Neo4jComm

from src.linking.hyperlinks.linker import link as hyperlinked_link
from src.linking.prelinked.linker import link as prelinked_link

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
                    
    -link          Try linking wiki nodes in neo4j
                    db using one of the following
                    strategies (specify as arg vals):
                        hyperlinked
                        prelinked
                    Note: expects -neo4j arg to be
                    used before this one.

Examples:
    Use data in './data.txt' to fetch article names
    and use that to retrieve data from wikipedia:
    > -titles ./data.txt -wikiapi

    Previous example but with pushing data into Neo4j (
    each argument is a new line for formatting purposes):
    >   -titles ./data.txt 
        -wikiapi 0
        -neo4j bolt://10.0.0.3,neo4j,neo4j
        -createdb

    Link nodes in db.
    > -neo4j bolt://10.0.0.1,neo4j,neo4j -link prelinked

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
        '-link'     : [True, link]
    }


def inspect(arg_id, arg_val, state)-> object:
    '@@ reserved hook for inspecting state'
    state_fmt = ''
    # // ''.join has an issue with \n
    for k, v in state.items():
        state_fmt += f'\n\t {k} : {v}'
    print("Current State:" + state_fmt)
    

def devhook(arg_id, arg_val, state)-> object:
    ''' @@ reserved for development; recieve <state> 
        for hooking up experimental modules.
    '''
   

def titles(arg_id, arg_val, state):
    # // Handle file doesn't exist.
    assert os.path.exists(arg_val), f'''
        Used the following:
            Arg: '{arg_id}'
            Val: '{arg_val}'
        
        ...but the val is not a vald filename.
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
    gen_title_topic_pair = state.get('-titles')
    assert gen_title_topic_pair is not None, '''
        Used the following:
            Arg: '{arg_id}'

        ..but could not access a state which
        contains valid wikipedia article titles.
        Use -titles argument before this one.
    '''

    # // Construct 'piped generator'. This is the
    # // first layer where ArticleTopicPair gen.
    # // is converted to ArticleData gen.
    g  = (
        pull_articles(
            titles=[obj.title],
            topics=[obj.topic],
            subsearch=arg_val
        )
        for obj in gen_title_topic_pair
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
    for article_data in gen_article_data:
        assert type(article_data) is ArticleData, '''
            Tried to create a db but the type inside
            generator (made with -wikiapi) is unexpected.
        '''

        n4jc.push_node(
            label='WikiData',
            # // Load everything from ArticleData
            # // into the database.
            props=article_data.__dict__
        )

   
def link(arg_id, arg_val, state) -> None:
    # // Try retrieve neo4j obj
    n4jc = state.get('-neo4j')
    assert n4jc != None, '''
        Tried to create a database but the
        object used for neo4j communication
        is missing. Use -neo4j arg before this.
    '''
    # // Available strategies. Key is identifier
    # // associated with <arg_val>, while value
    # // is a list with this fmt:
    # //    [func, {kwargs}]
    linker_strategies = {
        'prelinked': [          # // ID.
            prelinked_link,     # // Func.
            {                   # // Func args.
                'n4jcomm': n4jc,
                # // Magic vals are properties
                # // of src.typehelpers.ArticleData
                'topic_key': 'topic',
                'title_key': 'title',
            }
        ],
        'hyperlinked': [        # // ID
            hyperlinked_link,   # // Func.
            {                   # // Func params.
                'n4jcomm': n4jc,
                'title_key': 'title',
                'hlink_key': 'links'

            }
        ]
    }
    # // Ensure that valid link strategy is used.
    strategy_list = '\n'.join(linker_strategies.keys())
    assert arg_val in linker_strategies, f'''
        Used arg '{arg_id}' with val '{arg_val}'
        ... but the value was not a recognised 
        linking strategy. Use one of these:
            {strategy_list}
    '''
    # // Get action list.
    func_args = linker_strategies[arg_val]
    # // Put args into func.
    func_args[0](**func_args[1])


def start() -> None:
    'Point of entry of CLI'

    # // List of arguments.
    args = sys.argv[1:]
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