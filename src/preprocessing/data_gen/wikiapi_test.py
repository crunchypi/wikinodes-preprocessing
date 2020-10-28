import wikiapi


article_names = ['Last Thursdayism']


def test_pull_articles():
    gen = wikiapi.pull_articles(
        article_names
    )

    for item in gen:
        # // Left here for future inspection.
        # print(item.topic)
        return '\tstatus: ok'

    return '\tstatus: fail -- empty generator'



# ------------------test all------------------ # 
tests = [
    test_pull_articles
]

for t in tests:
    print(t())