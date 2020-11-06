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
from data_gen.articles import ArticleList, load_articles
from data_gen.wikiapi import ArticleData, pull_articles
from neo4j_tools.comm import Neo4jComm

from linking.prelinked.linker import link as prelinked_link

# // Acts as documentation -- also used as 
# // 'help' printout for CLI
CLI_HELP = '''
-------------------------------------------------
CLI tool for orchestrating scripts in submodules.
-------------------------------------------------
Baic usage:
    Argument layout reflects piping of data. For
    example; arg1 is piped into arg2.

Arguments:
    -articles       Specify path where article
                    names are listed.

    -wikiapi        Uses data generated from 
                    <-articles> arg to pull data
                    from wikipedia.

    -neo4jpush      Pushes current state into neo4j.
                    Note, it is assumed that state
                    is data from -wikiapi. Arg vals
                    are expected to be in this form:
                        -neo4jpush uri,usr,pwd
                    
    -neo4j          Prepare a neo4j interface obj.
                    Arg vals are expected to be:
                        -neo4j uri,usr,pwd

    -link           try linking wiki nodes in neo4j
                    db using one of the following
                    strategies (specify as arg vals):
                        -prelinked
                    Note: expects -neo4j arg to be
                    used before this one.

Examples:
    Use data in './data.txt' to fetch article names
    and use that to retrieve data from wikipedia:
    > -articles ./data.txt -wikiapi

    Previous example but with pushing data into Neo4j:
    > ..previous.. -neo4jpush bolt://10.0.0.3,neo4j,neo4j

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
        '-articles' : [True, articles],
        '-wikiapi'  : [False, wikiapi],
        '-neo4jpush': [True, neo4jpush],
        '-neo4j'    : [True, neo4j],
        '-link'     : [True, link]
    }


def inspect(arg_id, arg_val, state)-> object:
    '@@ reserved hook for inspecting state'
    sample = (
        state[:2] 
        if type(state) is list else 
        state
    )
    print(f'''
        arg_id          : {arg_id}
        arg_val         : {arg_val}
        state type      : {type(state)}
        sample(if lst)  : {sample}
    ''')
    return state


def devhook(arg_id, arg_val, state)-> object:
    ''' @@ reserved for development; recieve <state> 
        for hooking up experimental modules.
    '''
    return state


def articles(arg_id, arg_val, _state): # // -> gen
    # // Handle file doesn't exist.
    assert os.path.exists(arg_val), f'''
        Used the following:
            Arg: '{arg_id}'
            Val: '{arg_val}'
        
        ...but the val is not a vald filename.
    '''
    return load_articles(path=arg_val)


def wikiapi(arg_id, _arg_val, state): # // -> gen
    
    for obj in state:
        assert type(obj) is ArticleList, '''
            Used the following:
                Arg: '{arg_id}'

            ..but could not access a state which
            contains valid wikipedia article names.
            Use -articles argument before this one.
        '''
        # // Split data
        topic, article_names = obj.topic, obj.article_names
        # // Get data and extract from generator.
        # // Should be one item there since querying
        # // a single artile name. 
        res = pull_articles(names=article_names)
        for r in res: # // Iterate generator.
            # // Attach prelinked topic before yield.
            r.topics_prelinked = topic
            yield r


def neo4jpush(arg_id, arg_val, state)-> object:
    arg_val = arg_val.split(',')
    assert len(arg_val) == 3, '''
        Used the following:
                Arg: '{arg_id}'
        .. but the following value
        did not contain enough info.
        Should be: <uri>,<usr>,<pwd>
        
    '''
    # // Instantiate neo4j communication tool
    uri, usr, pwd = arg_val
    n4jc = Neo4jComm(uri=uri, usr=usr, pwd=pwd)

    for obj in state:
        # // Verify that -wikiapi was used.
        assert type(obj) is ArticleData, f'''
            Used the following:
                Arg: '{arg_id}'

            .. but could not access a state 
            which contains valid wiki article
            data. Use -wikiapi before this.
        '''
        n4jc.push_any_node(
            label='wikidata',
            # // Load everything from ArticleData
            # // into the database.
            props=obj.__dict__
        )

    return state


def neo4j(arg_id, arg_val, state)-> Neo4jComm:
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
    n4jc = None
    try:
        n4jc = Neo4jComm(uri=uri, usr=usr, pwd=pwd)
    except Exception as e:
        print(f'''
            Error while setting up Neo4j interface.
            Ensure correct uri, usr and/or pwd.
            Msg: {e}
        ''')
    finally:
        return n4jc if n4jc else state
   

def link(arg_id, arg_val, state) -> None:
    # // Verify that a neo4j obj is in state.
    assert type(state) is Neo4jComm, f'''
        Used arg: '{arg_id}'
        ... but a neo4j interface was not
        in the current state. Use -neo4j
        arg before this one.
    '''
    # // Available strategies. Key is identifier
    # // associated with <arg_val>, while value
    # // is a list with this fmt:
    # //    [func, {kwargs}]
    linker_strategies = {
        'prelinked': [
            prelinked_link,
            {
                'n4jcomm': state,
                # // Magic vals are properties
                # // of wiki nodes. @standardise.
                'topic_key': 'topics_prelinked',
                'title_key': 'name',
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

    return state




def start() -> None:
    'Point of entry of CLI'

    # // List of arguments.
    args = sys.argv[1:]
    # // Keeping state between arguments, used for piping.
    state = None

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
            # // Use task func. Update state if anything is returned.
            res = func(current_arg, arg_val, state)
            state = res if res != None else state
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