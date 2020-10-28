from neo4j import GraphDatabase as GDB
import types

'''
Package containing Neo4jComm -- a class
for neo4j communication.

NOTE:   Not made with particular security
        or performance in mind (use with
        caution -- it's a hackjob).
'''

# // Switch for allowing unsafe method calls.
# // ..can at least pretend to have some
# // safety conscientiousness. True for dev.
_UNSAFE = True
# // Convenience func which is called where
# // some safety is desired. It will crash
# // if __UNSAFE == False
def _SAFECHECK():
    if _UNSAFE == False:
        raise Exception('''
            Crashed because an unsafe method
            was called and the pkg (comm.py)
            has safety enabled. Edit _UNSAFE
            (mod lvl var) to False to allow 
            unsafetly.
        ''')


class Neo4jComm:
    ''' Handles communication with neo4j.
        More info in method docstrings.
    '''
    def __init__(self, uri:str, usr:str, pwd:str):
        self.__driver = GDB.driver(
            uri=uri,
            auth=(usr, pwd),
            encrypted=False
        )

    def __del__(self):
        'Close driver just 2 b sure.'
        if self.__driver:
            self.__driver.close()


    def __push(self, cql:str, **bindings)-> None:
        'Generic pusher'
        with self.__driver.session() as sess:
            sess.run(cql, **bindings)


    def __push_get(self, cql:str, **bindings)-> object:
        'Generic pusher which yields results'
        with self.__driver.session() as sess:
            yield sess.run(cql, **bindings)


    def clear(self)-> None:
        'Clear the entire database'
        self.__push(cql='MATCH (x) DETACH DELETE x')


    def __construct_props(self, names:list)-> str:
        ''' Convenience hack for creating a str
            which can be used to bind properties
            to a neo4j node/rel. Returns the 
            following fmt:
                '{prop1:$prop1, prop2:$prop2, ... }'
        '''
        p_str = '{'
        # // Used to know when to stop putting commas
        # // after each property id.
        n = len(names) - 1
        for i, k in enumerate(names):
            p_str += f'{k}:${k}'
            # // Do not add a comma after last prop.
            if i < n:
                p_str += ','
        # // Close CQL.
        p_str += '}'
        return p_str


    def __extract_neo4j_node(self, n4j_res_gen)-> list:
        'Attempt to extract neo4j result into a lst of dct'
        res = []
        # // Weak typecheck for some safety.
        is_generator = isinstance(
            n4j_res_gen, 
            types.GeneratorType
        )
        assert is_generator , '''
            __extract_neo4j_node: input not a generator.
        '''
        # // Go through generator.
        for n4j_res in n4j_res_gen:
            # // .. and record.
            for record in n4j_res:
                # // .. and result type.
                for obj in record:
                    # // Only use nodes. Rels seem to
                    # // have varying obj names.
                    name = obj.__class__.__name__
                    if 'Node' not in name:
                        continue
                    # // Include obj dict in res.
                    res.append({k:v for k,v in obj.items()})
        return res


    def create_any_node(self, label:str, **kwargs)-> None:
        ''' Attemts to create a node with <label> as label.
            Properties are arbitrary, specified as kwargs
            such that keys are prop names and vals are vals.
            Batching not supported because it might cause
            a neo4j stack overflow.
        '''
        # // Crash if safety enabled.
        _SAFECHECK()
        # // Open CQL
        cql = f'MERGE (_:{label}'
        # // Add property binding names
        cql += self.__construct_props(names=kwargs.keys())
        # // Close CQL and push.
        cql += ')'
        self.__push(cql=cql, **kwargs)


    def retrieve_any_node(self, label:str, **kwargs): # -> gen
        ''' Attempts to retrieve any node with <label> as
            label. Properties are arbitrary, specified as 
            kwargs such that keys are prop names and vals 
            are vals. Can fetch multiple nodes.
        '''
        cql = f'MATCH (n:{label}'
        cql += self.__construct_props(names=kwargs.keys())
        cql += ') RETURN n'

        res = self.__push_get(cql, **kwargs)
        return self.__extract_neo4j_node(n4j_res_gen=res)



    def create_any_rel(self, label:str, id_a:str, 
                                id_b:str, **kwargs)-> None:
        ''' Attemts to create a relationship with <label> as
            label. Nodes are arbitrary; the entire db will
            be searched twice to find node A with any prop
            val which matches <id_a> and likewise with node
            B (this will create a (A)->(B) rel). As such,
            this method is exceptionally expensive.
            NOTE kwargs keys aID and bID are reserved.
        '''
        # // Crash if safety enabled.
        _SAFECHECK()
        # // Prop names which match kwargs.
        prop_names = self.__construct_props(names=kwargs.keys())
        cql = f'''
            MATCH (a), (b)
            // # Look through all nodes to find
            // # any property which matches $aID
            WITH a, b, [x in keys(a) 
                    WHERE a[x] = $aID] as aMatch

            // # Same as above but for (b) & $bID
            WITH a, b, [x in keys(b) 
                    WHERE b[x] = $bID] as bMatch

            // # Select two nodes based on match
           WHERE size(aMatch) > 0 
             AND size(bMatch) > 0

             // # Link 
            CREATE (a)-[_:{label} {prop_names}]->(b)
        '''
        self.__push(
            cql=cql,
            # // Pass kwargs but add node prop IDs
            **{**kwargs,'aID':id_a, 'bID':id_b}
        )
    
    def create_wiki_rel(self, label:str, wiki_title_a:str,
                        wiki_title_b:str, **kwargs)-> None:
        ''' 
            Attemts to create a relationship with <label> as
            label -- between two nodes, both of which have
            an attribute named 'title'. This attribute will
            be matched with <wiki_title_a> and <wiki_title_b>
            such that rel is (a)->(b). <kwargs> will be used
            as attribute & values in the relationship.
            NOTE <kwargs> keys 'title_a' & 'title_b' are 
            reserved.
        '''
        # // Crash if safety enabled.
        _SAFECHECK()
        # // Prop names which match kwargs.
        prop_names = self.__construct_props(names=kwargs.keys())
        cql = f'''
            MATCH (a), (b)
            WHERE a.title = $title_a
              AND b.title = $title_b
           CREATE (a)-[_:{label} {prop_names}]->(b)
        '''
        # // Additional bindings to match titles;
        # // created there for readability.
        more_bindings = {
            'title_a':wiki_title_a, 
            'title_b':wiki_title_b
        }
        self.__push(
            cql=cql,
            # // Pass kwargs and add more.
            **{**kwargs, **more_bindings}
        )

