# // Fixing python's absurd pathing so this
# // file can be ran from this folder.
import sys
sys.path.append('../../')

# // Modules for this test.
import os
from src.data_gen import titles


path = '../data/topics_titles_min.txt'





def test_load_titles():

    # // Verify that path exists.
    if not os.path.isfile(path):
        return f'\tstatus: fail -- file not found:{path}'

    # // Try get data
    gen = titles.load_titles(
        path=path
    )
    for item in gen:
        # // Left here for future inspection.
        # print(item.topic, item.title)
        return '\tstatus: ok'

    return '\tstatus: fail -- empty generator'


# ------------------test all------------------ # 
tests = [
    test_load_titles
]

for t in tests:
    print(t())