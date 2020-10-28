import neo4j_credentials
from comm import Neo4jComm

# // Keep connection at pkg lvl, most(all?)
# // tests will use it.
N4JC = Neo4jComm(
    uri='', 
    usr='', 
    pwd=''
)


def fmt_msg(func, status:bool)-> str:
    fn_name = func.__name__
    ok_msg  = f'\t status: ok ({fn_name})'
    err_msg = f'\t status: fail ({fn_name})'
    return ok_msg if status else err_msg


def test_create_any_node():
    N4JC.clear()
    N4JC.create_any_node(
        label='Person',
        name='abc'
    )
    # // Check manually if task is done.
    res = N4JC._Neo4jComm__push_get(
        cql='''
            MATCH (n:Person {name:'abc'})
            RETURN n
        '''
    )
    # // Unpack generator.
    ok = False
    for item in res:
        # // ok if any.
        if item: ok = True

    # // Return msg.
    return fmt_msg(
        func=test_create_any_node,
        status=ok
    )


def test_create_any_rel():
    N4JC.clear()
    N4JC.create_any_node(
        label='Person',
        name='aaa'
    )
    N4JC.create_any_node(
        label='Person',
        name='bbb'
    )
    N4JC.create_any_rel(
        label='POINTS_TO',
        id_a='aaa',
        id_b='bbb',
        data='ccc'
    )
    # // Check manually if task is done.
    # // NOTE: rel props not used, as 
    # // the db is cleared at the start
    # // of this func.
    res = N4JC._Neo4jComm__push_get(
        cql='''
            MATCH (n:Person), 
                  (m:Person)
            WHERE n.name = 'aaa'
              AND m.name = 'bbb'
              AND (n)-[]->(m)
           RETURN n, m
        '''
    )
    # // Unpack generator.
    ok = False
    for item in res:
        # // ok if any.
        if item: ok = True

    return fmt_msg(
        func=test_create_any_rel,
        status=ok
    )


def test_retrieve_any_node():
    N4JC.clear()
    N4JC.create_any_node(
        label='Person',
        name='testname_a'
    )
    res = N4JC.retrieve_any_node(
        label='Person',
        name='testname_a'
    )
    # // Check if node created above is
    # // in any element in res lst.
    ok = False
    for elm in res:
        ok = elm.get('name') == 'testname_a'
  
    return fmt_msg(
        func=test_retrieve_any_node,
        status=ok
    )


def test_create_wiki_rel():
    N4JC.clear()
    N4JC.create_any_node(
        label='Person',
        title='aaa'
    )
    N4JC.create_any_node(
        label='Person',
        title='bbb'
    )
    N4JC.create_wiki_rel(
        label='POINTS_TO',
        wiki_title_a='aaa',
        wiki_title_b='bbb',
        data='stuff'
    )
    # // Check manually if task is done.
    # // NOTE: rel props not used, as 
    # // the db is cleared at the start
    # // of this func.
    res = N4JC._Neo4jComm__push_get(
        cql='''
            MATCH (n:Person), 
                  (m:Person)
            WHERE n.name = 'aaa'
              AND m.name = 'bbb'
              AND (n)-[]->(m)
           RETURN n, m
        '''
    )
    # // Unpack generator.
    ok = False
    for item in res:
        # // ok if any.
        if item: ok = True

    return fmt_msg(
        func=test_create_any_rel,
        status=ok # // Did not crash; ok.
    )



# // --------------Run all--------------// #
tests = [
    test_create_any_node,
    test_create_any_rel,
    test_retrieve_any_node,
    test_create_wiki_rel
]

print('Running all tests:')
for t in tests:
    print(t())
