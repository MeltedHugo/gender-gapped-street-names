import json
from wikibaseintegrator import WikibaseIntegrator,wbi_helpers
from wikibaseintegrator.wbi_config import config

with open('db.json') as f:
  db = json.load(f)

wbi = WikibaseIntegrator()
config['USER_AGENT'] = 'Gender-Gapped Streetnames Analysis Tool'


# männlich  Q6581097
# weiblich  Q6581072
# inter     Q1097630
# transfem  Q1052281
# transmasc Q2449503
# nonbinary Q48270

#writer Q36180


def getEntities(gender,job):
  query = """
    SELECT ?p ?pLabel
    WHERE
    {
      ?p wdt:P31 wd:Q5.
      ?p wdt:P21* ?gender.
      ?p wdt:P106 wd:Q36180.
      ?p wdt:P27 wd:Q183.
      FILTER( ?gender IN(wd:Q48270, wd:Q1052281))
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE]". }
    }
  """ % (gender,job)

  res = {}
  for entity in wbi_helpers.execute_sparql_query(query)["results"]["bindings"]:
    res[entity["pLabel"]["value"]] = entity["p"]["value"]
  print(res)
  return()

print(getEntities("Q48270","Q36180"))