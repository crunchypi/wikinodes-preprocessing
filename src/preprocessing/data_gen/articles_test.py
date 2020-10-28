import articles
import os

path = '../data/wiki4schools_topics_raw.txt'



def test_load_articles():

    # // Verify that path exists.
    if not os.path.isfile(path):
        return f'\tstatus: fail -- file not found:{path}'

    # // Try get data
    gen = articles.load_articles(
        path='../data/wiki4schools_topics_raw.txt'
    )
    for item in gen:
        # // Left here for future inspection.
        # print(item.topic)
        return '\tstatus: ok'

    return '\tstatus: fail -- empty generator'


# ------------------test all------------------ # 
tests = [
    test_load_articles
]

for t in tests:
    print(t())