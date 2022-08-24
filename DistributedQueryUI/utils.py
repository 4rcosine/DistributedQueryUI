#Modulo delle Utilities (funzioni ad uso comune)

ope_name = {
		"base" : "base table",
		"proj" : "projection",
		"sel_val" : "selection (by value)",
		"sel_attr" : "selection (by attribute comparison)",
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

			##Per ogni soggetto che ha autorizzazione in chiaro sull'attributo della tabella...
			#for subj_plain in json["permissions"][attr]["plain"]:

			#	#... se il soggetto non è presente in lista lo aggiungo e gli aggiungo anche l'attributo in p
			#	if not subj_plain in subj_json:
			#		subj_json[subj_plain] = { "p" : [attr],  "e" : [], "own" : [], "pri" : -1}

			#	#... se il soggetto è presente in lista gli aggiungo l'attributo in p
			#	else:
			#		if attr not in subj_json[subj_plain]["p"]:
			#			subj_json[subj_plain]["p"].append(attr)

			#for subj_enc in json["permissions"][attr]["encr"]:
			#	#... se il soggetto non è presente in lista lo aggiungo e gli aggiungo anche l'attributo in e
			#	if not subj_enc in subj_json:
			#		subj_json[subj_enc] = { "p" : [],  "e" : [attr], "own" : [], "pri" : -1}

			#	#... se il soggetto è presente in lista gli aggiungo l'attributo in e
			#	else:
			#		if attr not in subj_json[subj_enc]["e"]:
			#			subj_json[subj_enc]["e"].append(attr)
						
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