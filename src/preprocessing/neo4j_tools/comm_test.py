from comm import Neo4jComm


# !! Beware of repetition -- implemented as 
# !! non-convoluted as possible for safety
# !! purposes; this is a test, after-all




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


def test_push_any_node():
    N4JC.clear()
    N4JC.push_any_node(
        label='Person',
        props={'name':'abc'}
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

    # // Cleanup.
    N4JC.clear()

    # // Return msg.
    return fmt_msg(
        func=test_push_any_node,
        status=ok
    )


def test_pull_any_node():
    N4JC.clear()
    label = 'Person'
    prop = 'name'
    name = 'doesntmatter'

    N4JC.push_any_node(
        label=label,
        props={prop:name}
    )
    res = N4JC.pull_any_node(
        label=label,
        props={prop:name}
    )
    # // Check if node created above is
    # // in any element in res lst.
    ok = False
    for elm in res:
        ok = elm.get(prop) == name
  
    # // Cleanup
    N4JC.clear(label=label)

    return fmt_msg(
        func=test_pull_any_node,
        status=ok
    )
    

def test_pull_any_node_prop():
    N4JC.clear()
    label = 'Person'
    prop = 'someprop'
    propval_a, propval_b = 'aa', 'bb'
    N4JC.push_any_node(
        label=label,
        props={prop:propval_a}
    )
    N4JC.push_any_node(
        label=label,
        props={prop:propval_b}
    )
    # // Check one single item.
    res = N4JC.pull_any_node_prop(
        label=label,
        props={},
        prop=prop
    )

    # // Cleanup.
    N4JC.clear(label=label)

    for item in res:
        if item not in [propval_a, propval_b]:
            return fmt_msg(
                func=test_pull_any_node_prop,
                status=False
            )
    return fmt_msg(
        func=test_pull_any_node_prop,
        status=True
    )


def test_push_any_rel():
    N4JC.clear()

    # // Vertex no. 1
    v_label = 'Person'
    v = {'name':'aaa'}
    # // Vertex no. 2
    w_label = 'Person'
    w = {'name':'bbb'}

    # // Edge.
    e_label = 'POINTS_TO'
    e = {'data':'ccc'}

    # // Insert both nodes.
    nodes = [(v_label, v), (w_label, w)]
    for pair in nodes:
        N4JC.push_any_node(
            label=pair[0],
            props=pair[1]
        )

    # // Link both nodes.
    N4JC.push_any_rel(
        v_label=v_label,
        w_label=w_label,
        e_label=e_label,
        v_props=v,
        w_props=w,
        e_props=e
    )

    # // Check manually if task is done.
    # // NOTE: rel props not used, as 
    # // the db is cleared at the start
    # // of this func.
    res = N4JC._Neo4jComm__push_get(
        cql=f'''
            MATCH (v:Person), 
                  (w:Person)
            WHERE v.name = 'aaa'
              AND w.name = 'bbb'
              AND (v)-[]->(w)
           RETURN v, w
        '''
    )
    # // Unpack generator.
    ok = False
    for item in res:
        # // ok if any.
        if item: ok = True

    # // Cleanup.
    N4JC.clear()

    return fmt_msg(
        func=test_push_any_rel,
        status=ok
    )


def test_pull_any_rel():
    N4JC.clear()

    # // Vertex no. 1
    v_label = 'Person'
    v = {'name':'aaa'}
    # // Vertex no. 2
    w_label = 'Person'
    w = {'name':'bbb'}

    # // Edge.
    e_label = 'POINTS_TO'
    e = {'data':'ccc'}

    # // Insert both nodes.
    nodes = [(v_label, v), (w_label, w)]
    for pair in nodes:
        N4JC.push_any_node(
            label=pair[0],
            props=pair[1]
        )

    # // Link both nodes.
    N4JC.push_any_rel(
        v_label=v_label,
        w_label=w_label,
        e_label=e_label,
        v_props=v,
        w_props=w,
        e_props=e
    )
    # // Also tested with multiple, it's ok.
    res = N4JC.pull_any_rel(
        v_label=v_label,
        w_label=w_label,
        e_label=e_label,
        v_props=v,
        w_props=w,
        e_props=e
    )

    # // Cleanup
    N4JC.clear()
    return fmt_msg(
        func=test_pull_any_rel,
        # // Verify that odd index is 'from' and
        # // even index is 'to'.
        status=(
            res[0].get('name') == v.get('name') and
            res[1].get('name') == w.get('name')
        )
    )




# // --------------Run all--------------// #
tests = [
    test_push_any_node,
    test_pull_any_node,
    test_pull_any_node_prop,
    test_push_any_rel,
    test_pull_any_rel
]

print('Running all tests:')
for t in tests:
    print(t())
