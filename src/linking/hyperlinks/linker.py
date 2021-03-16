# // Only used for typehinting in this module.
from src.neo4j_tools.comm import Neo4jComm
# // Namings
import src.typehelpers as typehelpers

'''
Module containing a linker function which
links wiki nodes in Neo4j by hyperlinks.

Specifically; For all wiki nodes N, find
titles T representing hyperlinks in N,
then connect (N)-[HYPERLINKS]->(all in T)
'''

def link(n4jcomm:Neo4jComm, title_key:str, hlink_key:str):
    ''' Linker strategy for linking WikiData V to other
        WikiData W if W.<title_key> is in V.<hlink_key>.
        Relationship is (V)-[HYPERLINKS]->(W).
    '''
    assert type(n4jcomm) is Neo4jComm, '''
        Tried linking(hyperlinks) but did not get a valid
        neo4j comminication object <n4jcomm>.
    '''
    # // Get titles of all WikiData nodes.
    titles = n4jcomm.pull_node_prop(
        label=typehelpers.db_spec_wikidata_label,
        props={},
        prop=title_key
    )
    
    # // [1] Set for quick searches of titles.
    # // Useful because a potential (a)->(b) 
    # // relationship can be cancelled before, 
    # // it reaches the DB.
    titles = set(titles)

    for title in titles:
        # // Get all hyperlinks.
        hlinks = n4jcomm.pull_node_prop(
            label=typehelpers.db_spec_wikidata_label,
            props={title_key:title},
            prop=hlink_key
        )
        # // The property is a list, and every
        # // WikiData node has only one hyperlink
        # // list.
        hlinks = hlinks[0]
        # // Link current node with <title> as title
        # // to any other node which has <title_other>
        # // as title.
        for title_other in hlinks:
            if title == title_other:
                continue

            # // Quick drop, explained further up [1].
            if title_other not in titles:
                continue
            
            n4jcomm.push_rel(
                v_label=typehelpers.db_spec_wikidata_label,
                w_label=typehelpers.db_spec_wikidata_label,
                e_label=typehelpers.db_spec_wikidata_link,
                v_props={title_key:title},
                w_props={title_key:title_other},
                e_props={}
            )
