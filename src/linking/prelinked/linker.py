
# // Only used for typehinting in this module.
from src.neo4j_tools.comm import Neo4jComm


'''
Module containing a linker function which
links wiki nodes in Neo4j by their pre-
assigned topics. See func docstring for
more info.
'''


def link(n4jcomm:Neo4jComm, topic_key:str, title_key:str)-> None:
    ''' Linking strategy which links neo4j wiki nodes by their 
        pre-assigned topics indirectly through an index node with
        label 'IndexNode' (will be created with this func). These
        index nodes will have the following property:
            1)  Mirrors wiki node property that contains a topic 
                (specified with <topic_key>).

        Each link between a wiki node and index node will be 
        labeled with <PRELINKED> and contain the following 
        property:
            1)  'confidence' score (will always be 1.0 because
                it is assumed that topic info in the database is 
                correct).
    '''
    assert type(n4jcomm) is Neo4jComm, '''
        Tried linking(prelinked) but did not get a neo4j
        communication object.
    '''
    # // Get all titles.
    node_titles = n4jcomm.pull_node_prop(
        label='WikiData',
        props={}, # Blank because it can be anything.
        prop=title_key
    )
    # // Combine titles with topics.
    topics_titles = {}
    for title in node_titles:
        # // Get topic for current title.
        topic = n4jcomm.pull_node_prop(
            label='WikiData',
            props={title_key:title},
            prop=topic_key
        )
        if not topic:
            continue
        
        # // Update topics_titles to add new
        # // titles to each topic.
        topic = topic[0]
        prev = topics_titles.get(topic)
        topics_titles[topic] = (
            prev + [title]
            if prev else
            [title]
        )

    # // Create an index node for each title.
    for topic in topics_titles.keys():
        n4jcomm.push_node(
            label='IndexNode',
            props={topic_key:topic}
        )

    # // Connect wiki nodes by their topic
    # // with an Index node.
    for topic, titles in topics_titles.items():
        # // Titles is list.
            for title in titles:
                n4jcomm.push_rel(
                    v_label='WikiData',
                    w_label='IndexNode',
                    e_label='PRELINKED',
                    v_props={title_key: title},
                    w_props={topic_key: topic},
                    # // 100% because presorted.
                    e_props={'confidence':1.0},
                )
