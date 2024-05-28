## IMPORTS ##

import overpy
import json
import requests
from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.wbi_config import config
import re
import csv
import statistics
import os
from absl import flags
import sys


## CONFIG ##
city = 'Aschaffenburg'
lang = 'de'


## SETUP ##

# command line arguments setup
# op=all, op=osm, op=stat
flags.DEFINE_string('op','all','The operation mode')
FLAGS = flags.FLAGS
FLAGS(sys.argv)

# wikidata setup
config['USER_AGENT'] = 'Gender-Gapped Streetnames Analysis Tool'
wbi = WikibaseIntegrator()
api = overpy.Overpass()


# localization
if lang == 'de':
  strUnknown = 'Unbekannt'
  strType = 'Typ'
  strCount = 'Anzahl'
  strLength = 'Länge'
  strGender = 'Geschlecht'
  strJob = 'Tätigkeit'
  strParty = 'Partei'
else:
  strUnknown = 'unknown'
  strType = 'type'
  strCount = 'count'
  strLength = 'length'
  strGender = 'gender'
  strJob = 'job'
  strParty = 'party'


# variable initialization
db = {}
totalEntities = 0
genderCounts = {}
partyCounts = {}
streetLengthsByParty = {}
totalStreets = 0
totalHuman = 0
totalPoliticalHumans = 0
totalStreetLength = 0
streetLengthsByGender = {}
humanStreetLength = 0
naziStreetLength = 0
diverseGendersAmount = 0
jobsCounts = {}
streetLengthsByJob = {}
typesCounts = {}
typesLengths = {}
jobsOnlyMale = {}
jobsOnlyFemale = {}
availableGenders = []


# prepare local storage
if not os.path.exists("csv"):
    os.mkdir("csv")
    
if not os.path.exists("Q.json"):
  with open("Q.json","w",encoding='utf8') as f:
      json.dump({}, f, indent = 2, ensure_ascii=False)
with open('Q.json') as f:
  Q = json.load(f)

if not os.path.exists("db.json"):
  with open("db.json","w",encoding='utf8') as f:
      json.dump({}, f, indent = 2, ensure_ascii=False)
with open('db.json') as f:
  db = json.load(f)





## FUNCTIONS ##


# retrieve names from wikidata or Q.json
def name(id):
  if id in Q:
    out = Q[id]
  else:
    r = wbi.item.get(id).labels.get(lang)
    if r is not None:
      out = r.value
      print('Adding to local storage: '+out)
    else:
      out = strUnknown
  Q[id] = out
  with open("Q.json","w",encoding='utf8') as f:
    json.dump(Q, f, indent = 2, ensure_ascii=False)
  return(out)


# retrieve entities from a property and out them as a list
# argument is supposed to be entity.claims.get(Pxx)
def getsnaks(list):
  output = []
  length = len(list)
  for i in range(length):
    snak = list[i].mainsnak.datavalue['value']['id']
    output.append(snak)
  return output


# fetch all ways, nodes and relations with wikidata tags in area from OSM
def getways():
  result = api.query('area["boundary"~"administrative"]["de:place"~"city"]["name"~"'+city+'"];nwr["name:etymology:wikidata"](area);out;')
  for way in result.ways:
    if way.tags.get("name") not in db and not way.tags.get("name") == None:
      db[way.tags.get("name")] = {
        "wikidataId": way.tags.get("name:etymology:wikidata"),
        "ids": [way.id],
        "wikidata":[]
      }
    else:
      db[way.tags.get("name")]["ids"].append(way.id)
  return(db)


# fetch street length
# argument is supposed to be street dict with way ids
def getLength(street):
  ids = db[street]["ids"]
  q = ",".join(str(x) for x in ids)
  fullq = "[out:json];way(id:"+q+");make stats length=sum(length());out;"
  url = "https://www.overpass-api.de/api/interpreter?data="+fullq
  r = requests.get(url)
  length = float(json.loads(r.content)["elements"][0]["tags"]["length"])
  return(length)


# parse dates
# type argument is either "birthday" or "deathday"
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
  

# calculate age
def age(dbEntity):
  birth = dbEntity["birthday"]
  death = dbEntity["deathday"]
  if birth == None or death == None:
    return None
  else:
    return death["year"]-birth["year"]-((death["month"],death["day"])<(birth["month"],birth["day"]))



# round to two digits
def roundNumber(f):
  return("%.2f" % round(f, 2))


# sort dict by value
def sortByValue(dict):
  sorted_dict = {}
  for key in sorted(dict, key=dict.get):
    sorted_dict[key] = dict[key]
  return(sorted_dict)

# return sorted dict
def dictSorted(d):
  return(dict(reversed(sortByValue(d).items())))


# save csv
def saveCsv(data,name):
  csv_file_path = "csv/"+name+".csv"
  with open(csv_file_path,mode="w",newline='') as file:
    writer = csv.writer(file)
    writer.writerows(data)



# generate csv from dict
def generateCsvFromDict(d,xname,key1,key2):
  print("Generating CSV: "+xname)
  data = [
    [key1,key2]
  ]
  t = dictSorted(d)
  for item in t:
    if not item == "unknown":
      itemname = name(item)
    else:
      itemname = strUnknown
    data.append([
      itemname,int(t[item])
    ])
  saveCsv(data,xname)


# calculate average age
def averageAgeCalc():
  ages = []
  for street in db:
    for entity in db[street]["wikidata"]:
      if "age" in entity:
        if not entity["age"] == None and not entity["age"] < 0:
          ages.append(entity["age"])
  return(roundNumber(statistics.mean(ages)))


# calculate lowest age
def lowestAgeCalc():
  ages = []
  for street in db:
    for entity in db[street]["wikidata"]:
      if "age" in entity:
        if not entity["age"] == None and not entity["age"] < 0:
          ages.append(entity["age"])
  return(min(ages))


# calculate highest age
def highestAgeCalc():
  ages = []
  for street in db:
    for entity in db[street]["wikidata"]:
      if "age" in entity:
        if not entity["age"] == None and not entity["age"] < 0:
          ages.append(entity["age"])
  return(max(ages))


# generate people.json
def makePeopleLists():
  allPeople = []
  for street in db:
    for entity in db[street]["wikidata"]:
      if not entity["name"] in allPeople and entity["type"]=="Q5":
        allPeople.append(entity["id"])
  peoplelist = {
    "jobs": {},
    "parties": {},
  }
  peoplelistClear = {
    "jobs": {},
    "parties": {},
  }
  for person in allPeople:
    for street in db:
      for entity in db[street]["wikidata"]:
        if entity["id"] == person:
          if "jobs" in entity:
            for job in entity["jobs"]:
              if not job in peoplelist["jobs"]:
                peoplelist["jobs"][job] = [person]
              else:
                if not person in peoplelist["jobs"][job]:
                  peoplelist["jobs"][job].append(person)
          if "parties" in entity:
            for party in entity["parties"]:
              if not party in peoplelist["parties"]:
                peoplelist["parties"][party] = [person]
              else:
                if not person in peoplelist["parties"][party]:
                  peoplelist["parties"][party].append(person)
  for i in peoplelist:
    for j in peoplelist[i]:
      peoplelistClear[i][name(j)] = peoplelist[i][j]
  for i in peoplelistClear:
    for j in peoplelistClear[i]:
      peoplelistClear[i][j] = [item.replace(item, name(item)) for item in peoplelistClear[i][j]]
  with open("people.json","w",encoding='utf8') as fp:
    json.dump(peoplelistClear, fp, indent = 2, ensure_ascii=False)


# generate human readable db (readable_db.json)
def generateReadableDb():
  print("Generating readable_db.json")
  d = db.copy()
  for street in d:
    for entityIndex,entity in enumerate(d[street]["wikidata"]):
      #print(entityIndex,entity)
      if not d[street]["wikidata"][entityIndex]["type"] == "unknown":
        d[street]["wikidata"][entityIndex]["type"] = name(d[street]["wikidata"][entityIndex]["type"])
      if "genders" in d[street]["wikidata"][entityIndex]:
        for genderIndex,gender in enumerate(d[street]["wikidata"][entityIndex]["genders"]):
          d[street]["wikidata"][entityIndex]["genders"][genderIndex] = name(d[street]["wikidata"][entityIndex]["genders"][genderIndex])
      if "parties" in d[street]["wikidata"][entityIndex]:
        for partyIndex,party in enumerate(d[street]["wikidata"][entityIndex]["parties"]):
          d[street]["wikidata"][entityIndex]["parties"][partyIndex] = name(d[street]["wikidata"][entityIndex]["parties"][partyIndex])
      if "jobs" in d[street]["wikidata"][entityIndex]:
        for jobIndex,party in enumerate(d[street]["wikidata"][entityIndex]["jobs"]):
          d[street]["wikidata"][entityIndex]["jobs"][jobIndex] = name(d[street]["wikidata"][entityIndex]["jobs"][jobIndex])
  #print(d)
  with open("readable_db.json","w",encoding='utf8') as fp:
    json.dump(d, fp, indent = 2, ensure_ascii=False)



## MAIN PROGRAM ##

# get streets from OSM if opmode is 'all' or 'osm'
if FLAGS.op == "all" or FLAGS.op == "osm":
  print('Fetching streets for',city)
  getways()
  print('Done, fetched',len(db),'streets')

  # get details for eponyms
  for idx,street in enumerate(db):
    print(str(idx+1)+'/'+str(len(db))+' - Processing data for '+street)
    db[street]["length"] = getLength(street)
    for i,id in enumerate(db[street]['wikidataId'].split(";")):
      entity = wbi.item.get(id)
      db[street]["wikidata"].append({})
      if entity.claims.get('P31'):
        db[street]["wikidata"][i] = {
          "type": entity.claims.get('P31')[0].mainsnak.datavalue['value']['id']
        }
      else:
        db[street]["wikidata"][i] = {
          "type": "unknown"
        }
      db[street]["wikidata"][i]["id"] = id
      db[street]["wikidata"][i]["name"] = name(id)
      if db[street]["wikidata"][i]["type"] == "Q5":
        db[street]["wikidata"][i]["genders"] = getsnaks(entity.claims.get('P21'))
        db[street]["wikidata"][i]["parties"] = getsnaks(entity.claims.get('P102'))
        db[street]["wikidata"][i]["jobs"] = getsnaks(entity.claims.get('P106'))
        db[street]["wikidata"][i]["birthday"] = parseDate(entity,"birthday")
        db[street]["wikidata"][i]["deathday"] = parseDate(entity,"deathday")
        db[street]["wikidata"][i]["age"] = age(db[street]["wikidata"][i])
    with open("db.json","w",encoding='utf8') as fp:
      del db[street]["ids"]
      del db[street]["wikidataId"]
      json.dump(db, fp, indent = 2, ensure_ascii=False)



# process statistical data if opmode is 'all' or 'stat'
if FLAGS.op == 'all' or FLAGS.op == 'stat':
  for street in db:
    for entity in db[street]["wikidata"]:
      totalEntities = totalEntities +1

  for idx,street in enumerate(db):
    totalStreets = totalStreets+1
    for entity in db[street]["wikidata"]:
      print(str(idx+1)+'/'+str(totalEntities)+' - Processing entity: '+entity["name"])
      if entity["type"] in typesCounts:
        typesCounts[entity["type"]] = typesCounts[entity["type"]]+1
      else:
        typesCounts[entity["type"]] = 1
      if entity["type"] in typesLengths:
        typesLengths[entity["type"]] = typesLengths[entity["type"]]+db[street]["length"]
      else:
        typesLengths[entity["type"]] = db[street]["length"]
      if entity["type"] == "Q5":
        totalHuman = totalHuman+1
      if "genders" in entity:
        for gender in entity["genders"]:
          if gender in genderCounts:
            genderCounts[gender] = genderCounts[gender]+1
          else:
            genderCounts[gender] = 1
          if not gender == "Q6581097" and not gender == "Q6581072":
            diverseGendersAmount = diverseGendersAmount + 1
      if "parties" in entity:
        for party in entity["parties"]:
          #print(party)
          if party in partyCounts:
            partyCounts[party] = partyCounts[party]+1
          else:
            partyCounts[party] = 1
      if "jobs" in entity:
        for job in entity["jobs"]:
          if job in jobsCounts:
            jobsCounts[job] = jobsCounts[job]+1
          else:
            jobsCounts[job] = 1
      if "jobs" in entity and "genders" in entity:
        for job in entity["jobs"]:
          if "Q6581097" in entity["genders"]:
            if job in jobsOnlyMale:
              jobsOnlyMale[job] = jobsOnlyMale[job]+1
            else:
              jobsOnlyMale[job] = 1
          if "Q6581072" in entity["genders"]:
            if job in jobsOnlyFemale:
              jobsOnlyFemale[job] = jobsOnlyFemale[job]+1
            else:
              jobsOnlyFemale[job] = 1

  for party in partyCounts:
    totalPoliticalHumans = totalPoliticalHumans+partyCounts[party]

  naziList = []
  for street in db:
    for entity in db[street]["wikidata"]:
      if "parties" in entity:
        for party in entity["parties"]:
          if party == "Q7320":
            naziList.append(entity["name"])
            naziStreetLength = naziStreetLength + db[street]["length"]

  for street in db:
    totalStreetLength = totalStreetLength + db[street]["length"]
    for entity in db[street]["wikidata"]:
      if entity["type"] == "Q5":
        humanStreetLength = humanStreetLength + db[street]["length"]
        if "genders" in entity:
          for gender in entity["genders"]:
            if gender in streetLengthsByGender:
              streetLengthsByGender[gender] = streetLengthsByGender[gender]+db[street]["length"]
            else:
              streetLengthsByGender[gender] = db[street]["length"]
        if "jobs" in entity:
          for job in entity["jobs"]:
            if job in streetLengthsByJob:
              streetLengthsByJob[job] = streetLengthsByJob[job]+db[street]["length"]
            else:
              streetLengthsByJob[job] = db[street]["length"]
        if "parties" in entity:
          for party in entity["parties"]:
            if party in streetLengthsByParty:
              streetLengthsByParty[party] = streetLengthsByParty[party]+db[street]["length"]
            else:
              streetLengthsByParty[party] = db[street]["length"]

  for gender in genderCounts:
    availableGenders.append(gender)

  totalHumanPercentage = roundNumber((totalHuman/totalStreets)*100)
  malePercentage = roundNumber((genderCounts["Q6581097"]/totalHuman)*100)
  femalePercentage = roundNumber((genderCounts["Q6581072"]/totalHuman)*100)
  popularParty = name(max(partyCounts,key=partyCounts.get))
  politicalPercentage = roundNumber((totalPoliticalHumans/totalHuman)*100)
  popularPartyPercentage = roundNumber((partyCounts[max(partyCounts,key=partyCounts.get)]/totalPoliticalHumans)*100)
  maleStreetLengthPercentage = roundNumber((streetLengthsByGender["Q6581097"]/humanStreetLength)*100)
  femaleStreetLengthPercentage = roundNumber((streetLengthsByGender["Q6581072"]/humanStreetLength)*100)
  diverseGendersPercentage = roundNumber((diverseGendersAmount/totalHuman)*100)
  popularJob = name(max(jobsCounts,key=jobsCounts.get))
  popularJobPercentage = roundNumber((jobsCounts[max(jobsCounts,key=jobsCounts.get)]/totalHuman)*100)
  averageAge = averageAgeCalc()



  # console output
  print("Total streets with etymology tags in "+city+": "+str(totalStreets))
  print("Total length of streets with etymology tags in "+city+": "+str(int(totalStreetLength))+" meters")
  print("Total streets named after humans: "+str(totalHuman)+" ("+str(totalHumanPercentage)+" % of total streets)")
  print("Percentage of human cis male eponyms: "+malePercentage+" %")
  print("Percentage of human cis male eponym street length: "+maleStreetLengthPercentage+" % (total "+str(int(streetLengthsByGender["Q6581097"]))+" meters)")
  print("Percentage of human cis female eponyms: "+femalePercentage+" %")
  print("Percentage of human cis female eponym street length: "+femaleStreetLengthPercentage+"% (total "+str(int(streetLengthsByGender["Q6581072"]))+" meters)")
  print("Percentage of human eponyms with diverse genders: "+diverseGendersPercentage+" %")
  print("Most common job: "+popularJob+" ("+popularJobPercentage+" % of all human eponyms)")
  print("Percentage of politically involved human eponyms: "+politicalPercentage+" %")
  print("Most common party: "+popularParty+" ("+popularPartyPercentage+" % of all politically involved human eponyms)")
  print("Total length of streets named after NSDAP members: "+str(int(naziStreetLength))+" meters")
  print("Average age of people: "+averageAge)
  print("Oldest human eponym was "+str(highestAgeCalc())+" and youngest was "+str(lowestAgeCalc())+".")
  print("Total streets: "+str(len(db)))


  # generate files
  makePeopleLists()
  generateCsvFromDict(typesCounts,"TypesByNumbers",strType,strCount)
  generateCsvFromDict(typesLengths,"TypesByLength",strType,strLength)
  generateCsvFromDict(genderCounts,"GendersByNumbers",strGender,strCount)
  generateCsvFromDict(streetLengthsByGender,"GendersByLength",strGender,strLength)
  generateCsvFromDict(jobsCounts,"JobsByNumbers",strJob,strCount)
  generateCsvFromDict(streetLengthsByJob,"JobsByLength",strJob,strLength)
  generateCsvFromDict(partyCounts,"PartiesByNumbers",strParty,strCount)
  generateCsvFromDict(streetLengthsByParty,"PartiesByLength",strParty,strLength)
  generateCsvFromDict(jobsOnlyMale,"JobsOnlyMale",strJob,strCount)
  generateCsvFromDict(jobsOnlyFemale,"JobsOnlyFemale",strJob,strCount)
  generateReadableDb()