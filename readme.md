# Gender Gapped Street Names
This is a repository for the tools I'm using for my paper on street names.

Check the config section in main.py to define the city you want to analyze, as well as the language.

To run the full script, run:  
`python main.py`

To fetch streets and generate a basic db with OSM data only, run:  
`python main.py --op=osm`

To fill db and generate reports only with existing db.json, run:  
`python main.py --op=stat`


There is a LaTeX document, but I don't really know anything about LaTeX. It generates a horrible looking pdf, maybe if I'm bored I'll actually learn how to use this.


### Files:
* **Q.json**: auto-generated storage for wikidata entities and their names. Delete the provided Q.json if you want to make your own project, I included it because I modified it due to discriminatory language in job names provided by wikidata.
* **db.json**: all streets with associated eponyms, with wikidata IDs.
* **readable_db.json**: same as db.json, but with human-readable values
* **people.json**: a reverse dict of jobs and parties, with people as values (because people keep asking me about this)