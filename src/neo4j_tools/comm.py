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


    def clear(self, label:str=None)-> None:
        ''' Clear the database. Adding <label> will 
            narrow down what will be cleared by
            labels
        ''' 
        cql = f'''
            MATCH (x{':'+label if label else ''})
            DETACH DELETE x
        '''
        self.__push(cql=cql)


    def __construct_props(self, names:list, alias:str)-> str:
        ''' Convenience hack for creating a str
            which can be used to bind properties
            to a neo4j node/rel. Returns the 
            following fmt:
                '{
                    <prop1>:$<alias><prop1>, 
                    <prop2>:$<alias><prop2>, 
                    ... 
                }'
        '''
        p_str = '{'
        # // Used to know when to stop putting commas
        # // after each property id.
        n = len(names) - 1
        for i, k in enumerate(names):
            p_str += f'{k}:${alias}{k}'
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


    def push_node(self, label:str, props:dict)-> None:
        ''' Attemts to create a node with <label> as label.
            Properties are arbitrary, specified as <props>
            such that keys are prop names and vals are vals.
            Batching not supported because it might cause
            a neo4j stack overflow.
        '''
        # // Crash if safety enabled.
        _SAFECHECK()
        # // Open CQL
        cql = f'MERGE (_:{label}'
        # // Add property binding names
        cql += self.__construct_props(
            names=props.keys(), 
            alias=''
        )
        # // Close CQL and push.
        cql += ')'
        self.__push(cql=cql, **props)


    def pull_node(self, label:str, props:dict): # -> gen
        ''' Attempts to retrieve any node with <label> as
            label. Properties are arbitrary, specified as 
            <props> such that keys are prop names and vals 
            are vals. Can fetch multiple nodes.
        '''
        cql = f'MATCH (n:{label}'
        # // Add property binding names.
        cql += self.__construct_props(
            names=props.keys(),
            alias=''
        )
        cql += ') RETURN n'

        res = self.__push_get(cql, **props)
        return self.__extract_neo4j_node(n4j_res_gen=res)


    def pull_node_prop(self, label:str, 
                            props:dict, prop:str)-> list:
        ''' Equivalent of self.pull_any_node but only
            returns the value of node prop named <prop>.
            Meant for retrieving a specific property from
            all nodes. For instance, get all wiki article
            titles.
        '''
        cql = f'MATCH (n:{label}'
        # // Add property binding names.
        cql += self.__construct_props(
            names=props.keys(),
            alias=''
        )
        cql += f') RETURN n.{prop}'

        res = self.__push_get(cql, **props)
        res = next(res)
        
        # // Unpack all items in all records in res.
        return [itm for rec in res for itm in rec]

    
    def push_rel(self, v_label:str, w_label:str, e_label:str,
                             v_props:dict, w_props:dict, e_props:dict):
        ''' Create a relationship between any two nodes, where vertice
            v has label <v_label> with <v_props> as properties --  
            likewise for vertice w. Relationship/edge will be (v)->(w), 
            labeled with <e_label> and have <e_props> as properties.
            Note; MERGE operation as opposed to CREATE.
        '''
        # // Aliases to differentiate dict keys when pushing.
        # // Not doing this can be an issue if v_props and
        # // w_props share keys, which is likely the case.
        # // Aliasing e_props just in case.
        v_al, w_al, e_al = 'v', 'w', 'e'

        # // Abbreviation.
        props = self.__construct_props
        # // Construct props, using aliased keys. Done before
        # // transforming dict keys (next code block) to
        # // preserve the original intended names/keys.
        v_props_names = props(names=v_props.keys(), alias=v_al)
        w_props_names = props(names=w_props.keys(), alias=w_al)
        e_props_names = props(names=e_props.keys(), alias=e_al)

        # // Transform dicts to take into account aliases.
        # // Note; assuming all keys are strings.
        v_props = {v_al+k:v for k,v in v_props.items()}
        w_props = {w_al+k:v for k,v in w_props.items()}
        e_props = {e_al+k:v for k,v in e_props.items()}
        
        # // CQL.
        cql = f'''
            MATCH 
                (v:{v_label} {v_props_names}),
                (w:{w_label} {w_props_names})
                
            MERGE (v)-[_:{e_label} {e_props_names}]->(w)
        '''
        
        # // send to db.
        self.__push(cql=cql, **{**v_props, **w_props, **e_props})


# !! Not refactoring <pull_any_rel> even though its _very_ similar to 
# !! <push_any_rel> for simplicity purposes.
# !!
    def pull_rel(self, v_label:str, w_label:str, e_label:str,
                            v_props:dict, w_props:dict, e_props:dict):
        ''' Attemts to pull nodes by a relationship where vertice v
            has a label <v_label> with <v_props> as properties -- 
            likewise for vertice w. Relationship/edge is specified
            similarly as well, with <e_label> and <e_props>.

            The query will have direction (v)->(w) and the result
            will be a list in the following format:
                Each odd index is data for 'from-node'
                Each even index is data for 'to-node'         
        '''
        # // Aliases to differentiate dict keys when pushing.
        # // Not doing this can be an issue if v_props and
        # // w_props share keys, which is likely the case.
        # // Aliasing e_props just in case.
        v_al, w_al, e_al = 'v', 'w', 'e'

        # // Abbreviation.
        props = self.__construct_props
        # // Construct props, using aliased keys. Done before
        # // transforming dict keys (next code block) to
        # // preserve the original intended names/keys.
        v_props_names = props(names=v_props.keys(), alias=v_al)
        w_props_names = props(names=w_props.keys(), alias=w_al)
        e_props_names = props(names=e_props.keys(), alias=e_al)

        # // Transform dicts to take into account aliases.
        # // Note; assuming all keys are strings.
        v_props = {v_al+k:v for k,v in v_props.items()}
        w_props = {w_al+k:v for k,v in w_props.items()}
        e_props = {e_al+k:v for k,v in e_props.items()}
        
        # // CQL.
        cql = f'''
            MATCH 
                (v:{v_label} {v_props_names}),
                (w:{w_label} {w_props_names})
                 
            WHERE (v)-[:{e_label} {e_props_names}]->(w)
            RETURN v,w
        '''
        
        # // send to db.
        res = self.__push_get(
            cql=cql, 
            **{**v_props, **w_props, **e_props}
        )

        return self.__extract_neo4j_node(n4j_res_gen=res)


    def create_ftindex(self, name:str, label:str, prop:str):
        ''' Creates a fulltext index unsafely (i.e doesn't check
            if one exists and without parameterization). Only one
            label & prop allowed.
        '''
        self.__push(cql=f'''
            CALL db.index.fulltext.createNodeIndex(
                '{name}', ['{label}'], ['{prop}'])
        ''')

