'''
Main works as CLI tool for orchestrating
submodule scripts. See mod lvl <cli_help> str
for more info.

Convention:
    argument should be named as its mapped function
    (see cli_actions()) and the module it uses. So 
    arg x should use func x which uses the in x mod.

    For uniformity, each task function should 
    accept: current_arg, state, arg value. 
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
            [0] position for CLI arg val.
            [1] associated function.
    '''
    return {
        '-articles' : [1, articles],
        '-wikiapi'  : [0, wikiapi]
    }



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

    # // Always assume that arg comes right after command.
    for i  in range(0, len(args), 2):
        try:
            # // Assumed to be keys in dct
            current_arg = args[i]
            # // Unpack for readability.
            arg_targets = cli_actions().get(current_arg)
            assert arg_targets, f'Unrecognised arg: {current_arg}'
            argjump, func = arg_targets
            # // Point of action -- only update state if 
            # // task-func returns anything.
            res = func(current_arg, args[i+argjump], state)
            state = res if res != None else state

        except Exception as e:
            print(f'issue on arg "{args[i]}": '+ 
                    f'\n\tException: {e}')

            print("\n\n", CLI_HELP)
        # // @ Deb
        print(state)

start()