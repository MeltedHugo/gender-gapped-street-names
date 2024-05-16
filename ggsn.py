import overpy
import json
import os.path
import requests
from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.wbi_config import config

config['USER_AGENT'] = 'Gender-Gapped Streetnames Analysis Tool'
wbi = WikibaseIntegrator()
api = overpy.Overpass()
db = {}


## Wikibase Variables function ##

def wbname(id):
  return(wbi.item.get(id).labels.get('de').value)

def getsnaks(list):
  output = []
  length = len(list)
  for i in range(length):
    snak = list[i].mainsnak.datavalue['value']['id']
    output.append(snak)
  return output


def getways(city):
  # fetch all ways and nodes
  result = api.query('area["boundary"~"administrative"]["de:place"~"city"]["name"~"'+city+'"];nwr["name:etymology:wikidata"](area);out;')

  for way in result.ways:
    if way.tags.get("name") not in db:
      db[way.tags.get("name")] = {
        "wikidataId": way.tags.get("name:etymology:wikidata"),
        "ids": [way.id],
        "wikidata":[]
      }
    else:
      db[way.tags.get("name")]["ids"].append(way.id)

  return(db)



def getLength(street):
  ids = db[street]["ids"]
  q = ",".join(str(x) for x in ids)
  fullq = "[out:json];way(id:"+q+");make stats length=sum(length());out;"
  print(fullq)

  url = "https://www.overpass-api.de/api/interpreter?data="+fullq
  r = requests.get(url)
  length = float(json.loads(r.content)["elements"][0]["tags"]["length"])
  #length = api.query(fullq)
  #print(length)
  #fullLength = 0
  #for id in db[street]["ids"]:
  #  partLength = api.query("way(id:"+str(id)+");make stats length=sum(length());out;")
  #  print(partLength)
  #  length = length + partLength

  return(length)



print(getways('Aschaffenburg'))

for street in db:
  #print(street)
  db[street]["length"] = getLength(street)
  for i,id in enumerate(db[street]['wikidataId'].split(";")):
    entity = wbi.item.get(id)
    db[street]["wikidata"].append({})
    db[street]["wikidata"][i]["id"] = id
    #print(entity.labels.get('de').value)
    if entity.claims.get('P31'):
      db[street]["wikidata"][i] = {
        "type": entity.claims.get('P31')[0].mainsnak.datavalue['value']['id']
      }
    else:
      db[street]["wikidata"][i] = {
        "type": "unknown"
      }
    if db[street]["wikidata"][i]["type"] == "Q5":
      #print(entity.claims.get('P21'))
      db[street]["wikidata"][i]["genders"] = getsnaks(entity.claims.get('P21'))
      db[street]["wikidata"][i]["parties"] = getsnaks(entity.claims.get('P102'))
      db[street]["wikidata"][i]["jobs"] = getsnaks(entity.claims.get('P106'))
    print(db[street])
  with open("db.json","w",encoding='utf8') as fp:
    del db[street]["ids"]
    json.dump(db, fp, indent = 2, ensure_ascii=False)

#entity = wbi.item.get('Q582')
#print(entity.labels.get('de').value)

#for way in result.ways:
#    print("Name: %s" % way.tags.get("name", "n/a"))
#    print("  Highway: %s" % way.tags.get("highway", "n/a"))
#    print("  Nodes:")
#    for node in way.nodes:
#        print("    Lat: %f, Lon: %f" % (node.lat, node.lon))