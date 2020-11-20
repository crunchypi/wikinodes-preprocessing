# // Fixing python's absurd pathing so this
# // file can be ran from this folder.
import sys
sys.path.append('../../')

import os
from src.data_gen import wikiapi
from src.data_gen import titles

from src.typehelpers import TitleTopicPair

# // Sime to check basic usage
DATA_SIMPLE = ['Last Thursdayism']

# // More realistic data.
data_path = '../data/topics_titles_min.txt'
assert os.path.isfile(data_path), f'''
    '!! {data_path}' does not lead to any valid file.
'''

print('''
    ?? This test depends on <src..data_gen.titles> module. 
    ?? Make sure it is tested before running this test.
''')


def data_gen():
    return titles.load_titles(path=data_path)


def msg_fmt(func, status, extra='')-> str:
    'Formatter for err msg'
    # // Simple status.
    msg = f"\tstatus: {'ok' if status else 'fail'} {extra}."
    # // Add funk name before return.
    return msg + f' (func: {func.__name__})'


def test_simple_pull_articles():
    # // Abbreviation.
    f = test_simple_pull_articles
    gen = wikiapi.pull_articles(
        titles=DATA_SIMPLE
    )

    for item in gen:
        # // Left here for future inspection.
        # print(item.url)
        return msg_fmt(func=f, status=True)
        
    return msg_fmt(
            func=test_simple_pull_articles,
            status=False,
            extra='Empty generator.'
        )


def test_realistic_pull_articles():
    # // Abbreviation.
    f = test_realistic_pull_articles
    # // Used for return value to see how much was pulled.
    articles_checked = 0
    for obj in data_gen():
        # // Verify correct generator val type.
        if type(obj) is not TitleTopicPair:
            return msg_fmt(
                func=f,
                status=False,
                extra=f'Unexpected gen type:{type(obj)}'
            )
        
        # // Get article data from API pull.
        gen_sub = wikiapi.pull_articles(
            titles=[obj.title]
        )

        # // Switch used for guarding empty generator.
        got_data = False
        
        # // Check generator content.
        for api_res in gen_sub:
            # // Abbreviation.
            rn = api_res.title
            # // Warn if query was modified.
            if rn not in obj.title:
                print("\twarn: Modified res:'{rn}'")
                
            # // Tick and verify.
            articles_checked += 1
            got_data = True

        # // Handle empty generator.
        if not got_data:
            return msg_fmt(
                func=f,
                status=False,
                extra=f'Empty API gen'
            )
    # // Signal ok.
    return msg_fmt(
        func=f, 
        status=True, 
        extra=f'Article count: {articles_checked}'
    )

# ------------------test all------------------ # 
tests = [
    test_simple_pull_articles,
    test_realistic_pull_articles
]

for t in tests:
    print(t())