import json
from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.wbi_config import config
import plotly.express as px
import plotly.graph_objects as go
import os
import csv

if not os.path.exists("images"):
    os.mkdir("images")
if not os.path.exists("csv"):
    os.mkdir("csv")

wbi = WikibaseIntegrator()
config['USER_AGENT'] = 'Gender-Gapped Streetnames Analysis Tool'

with open('db.json') as f:
  db = json.load(f)

with open('Q.json') as f:
  Q = json.load(f)


def saveImage(fig,name):
  fig.write_image("images/"+name+".png")

def saveCsv(data,name):
  csv_file_path = "csv/"+name+".csv"
  with open(csv_file_path,mode="w",newline='') as file:
    writer = csv.writer(file)
    writer.writerows(data)


## STATS BY GENDER ##

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

for street in db:
  totalStreets = totalStreets+1
  for entity in db[street]["wikidata"]:
    #print(entity)

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

#for gender in counts:
  
#print(counts)


def st(f):
  return("%.2f" % round(f, 2))

def sortByValue(dict):
  sorted_dict = {}
  for key in sorted(dict, key=dict.get):
    sorted_dict[key] = dict[key]
  return(sorted_dict)

def dictSorted(d):
  return(dict(reversed(sortByValue(d).items())))

def wbname(id, lang):
  if id in Q:
    out = Q[id]
  else:
    r = wbi.item.get(id).labels.get(lang)
    print(r)
    if r is not None:
      out = r.value
    else:
      out = "Unbekannt"
  Q[id] = out
  with open("Q.json","w",encoding='utf8') as f:
    json.dump(Q, f, indent = 2, ensure_ascii=False)
  return(out)

def shortname(id):
  print(id)
  sn = wbi.item.get(id).claims.get('P1813')[0].mainsnak.datavalue
  print(sn)
  return(sn)

def generateCsvFromDict(d,name,key1,key2):
  print("Generating CSV: "+name)
  data = [
    [key1,key2]
  ]
  t = dictSorted(d)
  for item in t:
    if not item == "unknown":
      itemname = wbname(item,"de")
    else:
      itemname = "Unbekannt"
    data.append([
      #itemname, str(+t[item]).replace('.',',')
      itemname,round(t[item])
    ])
  saveCsv(data,name)


for party in partyCounts:
  totalPoliticalHumans = totalPoliticalHumans+partyCounts[party]


naziList = []
for street in db:
  for entity in db[street]["wikidata"]:
    if "parties" in entity:
      for party in entity["parties"]:
        if party == "Q7320":
          naziList.append(street)
          naziStreetLength = naziStreetLength + db[street]["length"]

print(naziList)

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

#print(streetLengthsByGender)

totalHumanPercentage = st((totalHuman/totalStreets)*100)
malePercentage = st((genderCounts["Q6581097"]/totalHuman)*100)
femalePercentage = st((genderCounts["Q6581072"]/totalHuman)*100)
popularParty = wbname(max(partyCounts,key=partyCounts.get),"de")
politicalPercentage = st((totalPoliticalHumans/totalHuman)*100)
popularPartyPercentage = st((partyCounts[max(partyCounts,key=partyCounts.get)]/totalPoliticalHumans)*100)
maleStreetLengthPercentage = st((streetLengthsByGender["Q6581097"]/humanStreetLength)*100)
femaleStreetLengthPercentage = st((streetLengthsByGender["Q6581072"]/humanStreetLength)*100)
diverseGendersPercentage = st((diverseGendersAmount/totalHuman)*100)
popularJob = wbname(max(jobsCounts,key=jobsCounts.get),"en")
popularJobPercentage = st((jobsCounts[max(jobsCounts,key=jobsCounts.get)]/totalHuman)*100)

#print(sortByValue(partyCounts))
#print(sortByValue(jobsCounts))

print("Total streets with etymology tags in town: "+str(totalStreets))
print("Total length of streets with etymology tags in town: "+str(int(totalStreetLength))+" meters")
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



## CHARTS GENERATION ##

def chartEponymTypesByNumbers():
  name = "eponymTypesByNumbers"
  print("Generating "+name)
  labels = ["Andere"]
  values = [0]
  threshold = 2
  for type in typesCounts:
    if typesCounts[type] <= threshold:
      values[0] = values[0]+typesCounts[type]
    else:
      if not type == "unknown": 
        labels.append(wbname(type,"de"))
      else:
        labels.append("Unbekannt")
      values.append(typesCounts[type])
  fig = go.Figure(data=[go.Pie(labels=labels,values=values,title="Arten von Eponymen nach Anzahl")])
  saveImage(fig,name)

def chartEponymTypesByLength():
  name = "eponymTypesByLength"
  print("Generating "+name)
  labels = ["Andere"]
  values = [0]
  threshold = 1000
  for type in typesLengths:
    if typesLengths[type] <= threshold:
      values[0] = values[0]+typesLengths[type]
    else:
      if not type == "unknown":
        labels.append(wbname(type,"de"))
      else:
        labels.append("Unbekannt")
      values.append(typesLengths[type])
  fig = go.Figure(data=[go.Pie(labels=labels,values=values,title="Arten von Eponymen nach Straßenlänge")])
  saveImage(fig,name)

def chartGenderByNumbers():
  name = "genderByNumbers"
  print("Generating "+name)
  labels = ["Andere"]
  values = [0]
  threshold = 1
  for gender in genderCounts:
    if genderCounts[gender] <= threshold:
      values[0] = values[0]+genderCounts[gender]
    else:
      if not gender == "unknown":
        labels.append(wbname(gender,"de"))
      else:
        labels.append("Unbekannt")
      values.append(genderCounts[gender])
  fig = go.Figure(data=[go.Pie(labels=labels,values=values,title="Verteilung der Geschlechter nach Anzahl")])
  saveImage(fig,name)

def chartGenderByLength():
  name = "genderByLength"
  print("Generating "+name)
  labels = ["Andere"]
  values = [0]
  threshold = 1000
  for gender in streetLengthsByGender:
    if streetLengthsByGender[gender] <= threshold:
      values[0] = values[0]+streetLengthsByGender[gender]
    else:
      if not gender == "unknown":
        labels.append(wbname(gender,"de"))
      else:
        labels.append("Unbekannt")
      values.append(streetLengthsByGender[gender])
  fig = go.Figure(data=[go.Pie(labels=labels,values=values,title="Verteilung der Geschlechter nach Straßenlänge")])
  saveImage(fig,name)

def chartJobsByNumbers():
  name = "jobsByNumbers"
  print("Generating "+name)
  labels = ["Andere"]
  values = [0]
  threshold = 8
  for job in jobsCounts:
    if jobsCounts[job] <= threshold:
      values[0] = values[0]+jobsCounts[job]
    else:
      if not job == "unknown": 
        labels.append(wbname(job,"de"))
      else:
        labels.append("Unbekannt")
      values.append(jobsCounts[job])
  fig = go.Figure(data=[go.Pie(labels=labels,values=values,title="Tätigkeiten nach Anzahl")])
  saveImage(fig,name)

def chartJobsByLength():
  name = "jobsByLength"
  print("Generating "+name)
  labels = ["Andere"]
  values = [0]
  threshold = 4000
  for job in streetLengthsByJob:
    if streetLengthsByJob[job] <= threshold:
      values[0] = values[0]+streetLengthsByJob[job]
    else:
      if not job == "unknown":
        labels.append(wbname(job,"de"))
      else:
        labels.append("Unbekannt")
      values.append(streetLengthsByJob[job])
  fig = go.Figure(data=[go.Pie(labels=labels,values=values,title="Tätigkeiten nach Straßenlänge")])
  saveImage(fig,name)

def chartPartiesByNumbers():
  name = "partiesByNumbers"
  print("Generating "+name)
  labels = ["Andere"]
  values = [0]
  threshold = 0
  for party in partyCounts:
    if partyCounts[party] <= threshold:
      values[0] = values[0]+partyCounts[party]
    else:
      if not party == "unknown": 
        labels.append(wbname(party,"de"))
      else:
        labels.append("Unbekannt")
      values.append(partyCounts[party])
  fig = go.Figure(data=[go.Pie(labels=labels,values=values,title="Parteizugehörigkeit nach Anzahl")])
  saveImage(fig,name)

def chartPartiesByLength():
  name = "partiesByLength"
  print("Generating "+name)
  labels = ["Andere"]
  values = [0]
  threshold = 300
  for party in streetLengthsByParty:
    if streetLengthsByParty[party] <= threshold:
      values[0] = values[0]+streetLengthsByParty[party]
    else:
      if not party == "unknown":
        labels.append(wbname(party,"de"))
      else:
        labels.append("Unbekannt")
      values.append(streetLengthsByParty[party])
  fig = go.Figure(data=[go.Pie(labels=labels,values=values,title="Parteizugehörigkeit nach Straßenlänge")])
  saveImage(fig,name)




def generateAllCsvs():
  generateCsvFromDict(typesCounts,"TypesByNumbers","Typ","Anzahl")
  generateCsvFromDict(typesLengths,"TypesByLength","Typ","Länge")
  generateCsvFromDict(genderCounts,"GendersByNumbers","Geschlecht","Anzahl")
  generateCsvFromDict(streetLengthsByGender,"GendersByLength","Geschlecht","Länge")
  generateCsvFromDict(jobsCounts,"JobsByNumbers","Tätigkeit","Anzahl")
  generateCsvFromDict(streetLengthsByJob,"JobsByLength","Tätigkeit","Länge")
  generateCsvFromDict(partyCounts,"PartiesByNumber","Partei","Anzahl")
  generateCsvFromDict(streetLengthsByParty,"PartiesByLength","Partei","Länge")

generateAllCsvs()


def drawAllCharts():
  chartEponymTypesByNumbers()
  chartEponymTypesByLength()
  chartGenderByNumbers()
  chartGenderByLength()
  chartJobsByNumbers()
  chartJobsByLength()
  chartPartiesByNumbers()
  chartPartiesByLength()

#drawAllCharts()