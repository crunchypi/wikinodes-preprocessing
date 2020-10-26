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

Examples:
    Use data in './data.txt' to fetch article name
    and use that to retrieve data from wikipedia:
        > -articles ./data.txt -wikiapi

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
        '-wikiapi'  : [False, wikiapi]
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


def articles(arg_id, arg_val, _state)-> List[ArticleList]:
    # // Handle file doesn't exist.
    assert os.path.exists(arg_val), f'''
        Used the following:
            Arg: '{arg_id}'
            Val: '{arg_val}'
        
        ...but the val is not a vald filename.
    '''
    return load_articles(arg_val)


def wikiapi(arg_id, _arg_val, state)-> List[ArticleData]:
    err_str = '''
        Used the following:
            Arg: '{arg_id}'

        ..but could not access a state which
        contains valid wikipedia article names.
        Use -articles argument before this one.

    '''
    # // Verify that <state> is a list of ArticleList objs.
    assert type(state) is list, err_str
    for elm in state: 
        assert type(elm) is ArticleList, err_str
    # // aliasing for shorted lines.
    # mod = data_gen.wikiapi
    res = []
    for obj in state:
        # // Split data
        topic, article_names = obj.topic, obj.article_names
        # // For module isolation reasons, the following func call
        # // does not know of the typehint ArticleList. As such, it
        # // only accepts a list of names <article_names>. The var
        # // <topic> defined above will be added back after this call.
        res = pull_articles(names=article_names)
        for d in res:
            d.topics_prelinked = topic

    return res


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
        finally:
            # // In either case; increment counter.
            i += step

start()