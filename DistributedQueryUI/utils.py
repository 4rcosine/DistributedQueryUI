#Modulo delle Utilities (funzioni ad uso comune)

ope_name = {
		"base" : "",
		"proj" : "projection",
		"sel_val" : "selection",
		"sel_attr" : "selection",
		"join" : "join",
		"gby" : "aggregation",
		"rename_p" : "rename",
		"rename_e" : "rename",
		"udf" : "user defined function",
		"encr" : "encryption",
		"decr" : "decryption"
	}

def build_initial_json(lista_tab_json):
	#Per ogni tabella caricata...
	subj_json = dict()

	for json in lista_tab_json:
		
		#se nella lista soggetti non c'è l'owner lo aggiungo. Se c'è già lo imposto come owner
		if not json["owner"] in subj_json:
			subj_json[json["owner"]] = { "p" : [],  "e" : [], "own" : [json["name"]], "pri" : -1}
		
		else:
			subj_json[json["owner"]]["own"].append(json["name"])

		#Per ogni attribuito della tabella...
		for soggetto in json["permissions"]:

			if not soggetto in subj_json:
				subj_json[soggetto] = { "p" : [],  "e" : [], "own" : [], "pri" : -1}

			subj_json[soggetto]["p"] = list(set(subj_json[soggetto]["p"] + json["permissions"][soggetto]["plain"]))
			subj_json[soggetto]["e"] = list(set(subj_json[soggetto]["e"] + json["permissions"][soggetto]["encr"]))

		for sj in subj_json:
			if subj_json[sj]["p"] == [] and subj_json[sj]["e"] == []:
				subj_json[sj]["p"] = subj_json["any"]["p"]
				subj_json[sj]["e"] = subj_json["any"]["e"]
				
		del subj_json["any"]

	return subj_json

#Assegnamento priorità a partire dalla mappa
def give_priority(subj_json, priority_map):
	for subj in priority_map:
		subj_json[subj]["pri"] = priority_map[subj]


def parseUint(str):
	try:
		return int(str)
	except:
		return -1