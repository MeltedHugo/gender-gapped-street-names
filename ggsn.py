import overpy
import json
import os.path
import requests
from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.wbi_config import config
import re
from datetime import date

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

def parseDate(entity,type):
  dateRegex = re.compile(r"(?P<year>[+|-]\d*)[-](?P<month>\d{2})[-](?P<day>\d{2})[T](?P<hour>\d{2})[:](?P<minute>\d{2})[:](?P<second>\d{2})[Z]")
  if type == "birthday":
    if len(entity.claims.get('P569'))>0:
      bdData = entity.claims.get('P569')[0].mainsnak.datavalue
    else:
      return(None)
  if type == "deathday":
    if len(entity.claims.get('P570'))>0:
      bdData = entity.claims.get('P570')[0].mainsnak.datavalue
    else:
      return(None)
  print(bdData)
  if bdData and not bdData == None:
    d = bdData["value"]["time"]
    birthday = {
      "year": int(dateRegex.match(d).group("year")),
      "month": int(dateRegex.match(d).group("month")),
      "day": int(dateRegex.match(d).group("day"))
    }
    return(birthday)
  else:
    return(None)

def age(dbEntity):
  birth = dbEntity["birthday"]
  death = dbEntity["deathday"]
  if birth == None or death == None:
    return None
  else:
    return death["year"]-birth["year"]-((death["month"],death["day"])<(birth["month"],birth["day"]))

def getName(entity):
  name = str(entity.labels.get("de"))
  return name


print(getways('Aschaffenburg'))

for street in db:
  #print(street)
  db[street]["length"] = getLength(street)
  for i,id in enumerate(db[street]['wikidataId'].split(";")):
    entity = wbi.item.get(id)
    db[street]["wikidata"].append({})
    #print(entity.labels.get('de').value)
    if entity.claims.get('P31'):
      db[street]["wikidata"][i] = {
        "type": entity.claims.get('P31')[0].mainsnak.datavalue['value']['id']
      }
    else:
      db[street]["wikidata"][i] = {
        "type": "unknown"
      }
    db[street]["wikidata"][i]["id"] = id
    db[street]["wikidata"][i]["name"] = getName(entity)
    if db[street]["wikidata"][i]["type"] == "Q5":
      #print(entity.claims.get('P21'))
      db[street]["wikidata"][i]["genders"] = getsnaks(entity.claims.get('P21'))
      db[street]["wikidata"][i]["parties"] = getsnaks(entity.claims.get('P102'))
      db[street]["wikidata"][i]["jobs"] = getsnaks(entity.claims.get('P106'))
      db[street]["wikidata"][i]["birthday"] = parseDate(entity,"birthday")
      db[street]["wikidata"][i]["deathday"] = parseDate(entity,"deathday")
      db[street]["wikidata"][i]["age"] = age(db[street]["wikidata"][i])
      
    print(db[street])
  with open("db.json","w",encoding='utf8') as fp:
    del db[street]["ids"]
    del db[street]["wikidataId"]
    json.dump(db, fp, indent = 2, ensure_ascii=False)

#entity = wbi.item.get('Q582')
#print(entity.labels.get('de').value)

#for way in result.ways:
#    print("Name: %s" % way.tags.get("name", "n/a"))
#    print("  Highway: %s" % way.tags.get("highway", "n/a"))
#    print("  Nodes:")
#    for node in way.nodes:
#        print("    Lat: %f, Lon: %f" % (node.lat, node.lon))