

import queryplan
import json
import utils
import sys
import os
import platform

#Step 0: Inizializzazione
lista_tab_json = []
pri_dict = {}
names_set = dict()

#Lettura file configurazioni
conf_json = open('conf.json')

#Richiesta input
print("The following configurations are available: ")
configs = json.load(conf_json)
k = 1
for confs in configs:
	print("\n\t" + str(k) + ") " + confs["conf_name"], end='')
	k += 1

scelta = 0
while not (int(scelta) >= 1 and int(scelta) < k ):
	scelta = utils.parseUint(input("\n\nPlease choose one configuration (type a number from 1 to " + str(k-1) + "): "))

	if not (int(scelta) >= 1 and int(scelta) < k ):
		print("Invalid option.")

#Leggo i dati dalla configurazione
try:
	config = configs[(scelta-1)]
	#Per ogni tabella nelle configurazioni leggo relativi file descrittivi e di autorizzazioni
	for table in config["tables"]:
		f1 = open(table["table_file"])
		t_file = json.load(f1)
		a_file = json.load(open(table["auth_file"]))
		t_file["permissions"] = a_file["permissions"]
		lista_tab_json.append(t_file)
		names_set[t_file["name"]] = t_file["fullName"]

	qp_dict = json.load(open(config["query_file"]))
	pri_dict = json.load(open(config["priority_file"]))

except:
	print("An error occurred during the loading of the configuration. Most common errors are: \n- bad json format\n- files specified do not exist\n\nExiting the program")
	sys.exit(-1)


subj_dict = utils.build_initial_json(lista_tab_json)

#Assegno le priorità
utils.give_priority(subj_dict, pri_dict)

qp = queryplan.query_plan() 

for chiave, valore in qp_dict.items():
	qp.add_nodo(int(chiave), valore["op_type"], valore["op_detail"], set(valore["set_attr"]), set(valore["set_oper"]), set(valore["set_attrplain"]), valore["parent_id"], valore["order"])

qp.set_subj(subj_dict)

#Eventualmente disegno l'albero
scelta = ""
while scelta != "n" and scelta != "y":
	scelta = input("Do you want to draw the initial query tree plan? [y/n]: ").lower()

	if scelta != "n" and scelta != "y":
		print("Invalid option.") 

if scelta == "y":
	utils.draw_tree(qp, names_set, True)

#Step 1: Calcolo della funzione di assegnamento dei candidati
qp.esegui_step_rec(1, True)

#Step 2: Assegnazione del soggetto e estensione del query plan
qp.esegui_step_rec(1, False)

#Step 3: Output
print("\n============================\n\tOUTPUT\n============================\n\n")
lista_ocd = qp.get_ocd()
lista_asc = qp.get_asc()

for i in range(1, qp.get_num_nodi()+1):
	nodo = qp.get_nodo(i)
	vp, ve, ip, ie, eq, cand, assegn, operazione, attributi, operandi, dett_op = nodo.get_profilo()
	print("Node: " + str(i))
	
	
	#Parti di output generate in base al tipo di operazione
	if operazione == "gby":
		print("-> Operation: " + dett_op + " on " + str(operandi).replace("'", "") + ", grouping", end='')
	else:
		print("-> Operation: " + utils.ope_name[operazione], end='')

	if operazione != "base":
		print(" on " + str(attributi).replace("'", ""), end='')

	else:
		print(" " + names_set[list(operandi)[0]], end='')
	
	print("")

	if operazione != "base" and not qp.is_proj_after_base(i):
		print("-> Candidates: " + str(cand).replace("'", ""))

	print("-> Assignee: " + assegn)
	#Parti di output generate in base all'eventuale cifratura
	for ocd in lista_ocd:
		if i == ocd["figlio"] and ocd["tipo_op"] == "C":
			print("-> Encryption of " + str(ocd["adc"]).replace("'", ""))

		if i == ocd["padre"] and ocd["tipo_op"] == "D":
			print("-> Decryption of " + str(ocd["adc"]).replace("'", ""))

	print("\n\tvp: " + str(list(vp)).replace("'", "") + "\n\tve: " + str(list(ve)).replace("'", "") + "\n\tip: " + str(list(ip)).replace("'", "") + "\n\tie: " + str(list(ie)).replace("'", "") + "\n\teq: " + str(list(eq)).replace("'", ""))

	print("\n=====================\n")

print("\r\n=== KEY ENCRYPTION SETS ===")
for asc in lista_asc:
	print(" • " + str(asc["kes"]).replace("'", "") + " - Key to be given to " + str(asc["sogg"]).replace("'", ""))

print("\nEnd of computation\n\n")

#Eventualmente disegno l'albero
scelta = ""
while scelta != "n" and scelta != "y":
	scelta = input("Do you want to draw the resulting query tree plan? [y/n]: ").lower()

	if scelta != "n" and scelta != "y":
		print("Invalid option.") 

if scelta == "y":
	utils.draw_tree(qp, names_set, False)