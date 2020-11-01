import os
import wikiapi
import articles

# // Sime to check basic usage
data_simple = ['Last Thursdayism']

# // More realistic data.
data_path = '../data/wiki4schools_topics_raw.txt'
assert os.path.isfile(data_path), '''
    <data_path> does not lead to any valid file.
'''

print('''
    This test depends on <articles> module. Make
    sure it is tested before running this test.
''')


def data_gen():
    return articles.load_articles(path=data_path)


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
        data_simple
    )

    for item in gen:
        # // Left here for future inspection.
        # print(item.topic)
        return msg_fmt( func=f, status=True)
        
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
        if type(obj) is not articles.ArticleList:
            return msg_fmt(
                func=f,
                status=False,
                extra=f'Unexpected gen type:{type(obj)}'
            )
        
        # // Get article data from API pull.
        gen_sub = wikiapi.pull_articles(
            names=obj.article_names
        )

        # // Switch used for guarding empty generator.
        got_data = False
        
        # // Check generator content.
        for api_res in gen_sub:
            # // Abbreviation.
            rn = api_res.name
            # // Warn if query was modified.
            if rn not in obj.article_names:
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