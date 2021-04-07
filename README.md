# wikinodes-preprocessing

This repo contains code for populating Neo4j(db) with nodes representing Wikipedia articles (and connecting them based on embedded hyperlinks) -- it's meant as a part of a larger project (Wikinodes). Code for serving content & a related React app is found at:
- [wikinodes-server](https://github.com/crunchypi/wikinodes-server)
- [wikinodes-app](https://github.com/crunchypi/wikinodes-app)

### Usage:

First, Neo4j should be installed and started. Additionally, there are a couple of (Python) module dependencies, namely 'neo4j' (driver module) and 'wikipedia' (wiki API interface module). The latter module seems to have a known issue which can trigger an exception, see details [here](https://github.com/goldsmith/Wikipedia/issues/107). Essentially, the module should be installed with ```python -m pip install --upgrade git+git://github.com/goldsmith/Wikipedia.git```.

</br>

Using this code is primarily done through the cli.py file in root, the options are as follows (help copy-paste):

```
-------------------------------------------------
CLI tool for orchestrating scripts in submodules.
-------------------------------------------------
Baic usage:
    Arguments are partially sensitive to position.
    State between arguments is kept, meaning that
    if arg2 needs data from arg1, then it will work
    as long as arg1 comes before arg2, even with an
    arbitrary amount args in-between.
Arguments:
    -titles         Specify path where article
                    names are listed.
    -wikiapi        Uses data generated from 
                    <-titles> arg to pull data
                    from wikipedia. This arg
                    expects a value specifying
                    the amount of subsearches for
                    each article. These sub-searches
                    are based on hyperlinks in each
                    article. 0 = None.
    -neo4j          Prepare a neo4j interface obj.
                    Arg vals are expected to be:
                        -neo4j uri,usr,pwd
    
    -createdb       Pushes data created with
                    -wikiapi into the neo4j db.
                    This arg has to come after
                        -wikiapi (for data)
                        -neo4j (for db connection).
                    
    -link          Try linking wiki nodes in neo4j.
                   Note: expects -neo4j arg to be
                   used before this one.
Examples:
    Use data in './data.txt' to fetch article names
    and use that to retrieve data from wikipedia:
    > -titles ./data.txt -wikiapi
    Previous example but with pushing data into Neo4j (
    each argument is a new line for formatting purposes):
    >   -titles ./data.txt 
        -wikiapi 0
        -neo4j neo4j://localhost:7687,neo4j,neo4j
        -createdb
    Link nodes in db.
    > -neo4j neo4j://localhost:7687,neo4j,neo4j -link

```


<br>

The schema is defined in 'src/typehelpers.py' and will be as follows:
- Node labels for each article: 'WikiData'
- Node relationships: 'HYPERLINKS'
- Property for wiki article title: 'title'
- Prop for wiki article url: 'url'
- Prop for wiki article content (cleaned ish): 'content'
- Prop for wiki article links (embedded hyperlinks): 'links'
- Prop for wiki article html (raw content): 'html'
- There is also a final property named 'topic' which is deprecated.

Should also mention that this CLI automatically creates a 'fulltext' index (see neo4j documentation) on WikiData.content (node and property); that is used for a search feature of the [server](https://github.com/crunchypi/wikinodes-server) and [app](https://github.com/crunchypi/wikinodes-app) repos (search bar for lookin for specific articles through their content). Index name is 'ArticleContentIndex' and the process is started in 'createdb' (func) in 'cli.py'. Also, this repo has a hardcoded rate limit (in addition to the rate limit set by the aforementioned 'wikipedia' module) of 1 second per request; that can be adjusted at the top of 'src/data_gen/wikiapi.py'.

<br>

Finally, the code is fairly well documented but I've also added a wiki [page](https://github.com/crunchypi/wikinodes-preprocessing/wiki) for this repo as a reference manual for completion purposes.
