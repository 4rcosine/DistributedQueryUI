

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

#Step 1: Calcolo della funzione di assegnamento dei candidati
qp.esegui_step_rec(1, True)

#Step 2: Assegnazione del soggetto e estensione del query plan
qp.esegui_step_rec(1, False)

#Step 3: Output
lista_ocd = qp.get_ocd()
lista_asc = qp.get_asc()
html_albero = ""
html_ls_nodi = ""
html_kes = ""

for i in range(1, qp.get_num_nodi()+1):
	
	html_ls_nodi += (", " if i != 1 else "") + "node" + str(i)

	html_nodo = ""
	nodo = qp.get_nodo(i)
	vp, ve, ip, ie, eq, cand, assegn, operazione, attributi, operandi, dett_op = nodo.get_profilo()
	html_nodo += "node" + str(i) + " = {\n"
	html_nodo += "parent: node" + str(nodo.id_padre) + "," if i != 1 else ""
	html_nodo += "innerHTML : \""
	
	for ocd in lista_ocd:
		if i == ocd["figlio"] and ocd["tipo_op"] == "C":
			html_nodo += "<div class='box_up'><p class='enc'>Encryption of " + str(ocd["adc"]).replace("'", "") + "</p></div><br/>"
	
	html_nodo += "<div class='box_left'><p class='op'><b>Operation:</b><br/>"

	#Parti di output generate in base al tipo di operazione
	if operazione == "gby":
		html_nodo += dett_op + " on " + str(operandi).replace("'", "") + ", grouping"
	else:
		html_nodo += utils.ope_name[operazione]

	if operazione != "base":
		html_nodo += " on " + str(attributi).replace("'", "")

	else:
		html_nodo += " " + names_set[list(operandi)[0]]
	
	html_nodo += "</p>"

	if operazione != "base" and not qp.is_proj_after_base(i):
		html_nodo += "<p class='cand'><b>Candidates:</b> " + str(cand).replace("'", "") + "</p>"

	html_nodo += "<p class='as'><b>Assignee:</b> " + assegn + "</p></div>"

	
	html_nodo += "<div class='arrow_left'></div><div class='box_right'><p class='prof'><b>Profile</b><br/>"
	html_nodo += "<i>vp</i>: " + str(list(vp)).replace("'", "") + "&nbsp;&nbsp;&nbsp;&nbsp;<i>ve</i>: " + str(list(ve)).replace("'", "") + "<br/>"
	html_nodo += "<i>ip</i>: " + str(list(ip)).replace("'", "") + "&nbsp;&nbsp;&nbsp;&nbsp;<i>ie</i>: " + str(list(ie)).replace("'", "") + "<br/>"
	html_nodo += "<i>eq</i>: " + str(list(eq)).replace("'", "") + "</p></div>"

	#Parti di output generate in base all'eventuale cifratura
	for ocd in lista_ocd:
		if i == ocd["padre"] and ocd["tipo_op"] == "D":
			html_nodo += "<br/><div class='box_down'><p class='enc'>Decryption of " + str(ocd["adc"]).replace("'", "") + "</p></div>"

	html_nodo += "\"\n};\n\n"
	html_albero += html_nodo

for asc in lista_asc:
	html_kes += "<li>" + str(asc["kes"]).replace("'", "") + " - Key to be given to " + str(asc["sogg"]).replace("'", "") + "</li>\n"

#Salvataggio dei dati nell'html finale
f_base_html = open('./base_html/index.html',mode='r')
base_html = f_base_html.read()
f_base_html.close()

end_html = base_html.replace("{{{nodes}}}", html_albero).replace("{{{n_list}}}", html_ls_nodi).replace("{{{kes}}}", html_kes)

out_html = open("./output/index.html", "w")
out_html.write(end_html)
out_html.close()

print("\nOpening output file...")
if platform.system() == "Darwin":
	os.system("open ./output/index.html")
else:
	os.system("start ./output/index.html")

print("End of computation\n\n")