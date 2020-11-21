
# // Only used for typehinting in this module.
from src.neo4j_tools.comm import Neo4jComm


'''
Module containing a linker function which
links wiki nodes in Neo4j by their pre-
assigned topics. See func docstring for
more info.
'''

# !! There is currently a large inefficiency in the link
# !! function; the most straight-forward thing to do is 
# !! to send a CQL str to the db which looks like this:
# !!
# !!  MATCH (v:WikiData), (b:WikiData)
# !!  WHERE v.title <> w.title
# !! CREATE (v)-[:TOPIC {confidence:1}]->(w)
# !!
# !! .. but this is not possible due to how Neo4jComm is 
# !! created. The current approach is more convoluted
# !! and relies more on Python, but this is percieved to
# !! be of little consequence at the time (201121) because
# !! this linker strategy relies on a small amount of
# !! pre-categorised data ('wikipedia for schools').


def link(n4jcomm:Neo4jComm, topic_key:str, title_key:str)-> None:
    ''' Linking strategy which links neo4j wiki nodes by their 
        pre-assigned topics, located in the property named
        <topic_key> of each node.

        If node V, W share a topic, then the following is created:
            (V)-[TOPIC:{confidence:1.0}]->(W) // V != W
        
        Confidence, as noted above, will always be 1.0 with this
        linking strategy because it is assumed that all nodes
        with a non-empty <topic_key> property have an accurate
        topic assigned.
    '''
    assert type(n4jcomm) is Neo4jComm, '''
        Tried linking(prelinked) but did not get a neo4j
        communication object.
    '''
    # // Magic convention: this is the label of all
    # // wiki nodes.
    wikidata_label = 'WikiData'

    # // Fetch all possible topics 
    topics = n4jcomm.pull_node_prop(
        label=wikidata_label,
        props={},
        prop=topic_key
    )
    # // Only unique.
    topics = set(topics)
    # // Drop case where topic is not set.
    try:
        topics.remove('')
    except:
        pass

    # // Topic-oriented relationship creation.
    for topic in topics:

        # // Fetch all titles associated with
        # // the current <topic>
        titles = n4jcomm.pull_node_prop(
            label=wikidata_label,
            props={topic_key:topic},
            prop=title_key
        )
        # // Yes, this.. could be done differentlu. 
        # // Explanation given in the comment block 
        # // at the start of this file.
        for title_v in titles:
            for title_w in titles:
                # // None of these: (v)-[]->(v)
                if title_v == title_w:
                    continue

                n4jcomm.push_rel(
                    v_label=wikidata_label,
                    w_label=wikidata_label,
                    e_label='TOPIC',
                    v_props={title_key:title_v, topic_key:topic},
                    w_props={title_key:title_w, topic_key:topic},
                    e_props={'confidence': 1.0}
                )