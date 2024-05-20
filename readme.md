# Gender Gapped Street Names
This is a repository for the tools I'm using for my paper on street names.

To run the full script, run:  
`python main.py`

To fetch streets and generate a basic db with OSM data only, run:  
`python main.py --op=osm`

To fill db and generate reports only with existing db.json, run:  
`python main.py --op=stat`


### Files:
* **Q.json**: auto-generated storage for wikidata entities and their names. Delete the provided Q.json if you want to make your own project, I included it because I modified it due to discriminatory language in job names provided by wikidata.
* **db.json**: all streets with associated eponyms, with wikidata IDs.
* **readable_db.json**: same as db.json, but with human-readable values
* **people.json**: a reverse dict of jobs and parties, with people as values (because people keep asking me about this)

* **ggsn.py** and **compute.py**: old scripts. They do the same as main.py, but aren't documented. Will delete these from the repo soon.