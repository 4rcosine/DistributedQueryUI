
class nodo_plan:
	"""Classe che rappresenta il nodo dell'albero della query"""
	#id = identificativo del nodo, serve per identificare il padre
	#tipo_op = operazione eseguita
	#set_attr = attributi coinvolti dall'operazione
	#set_oper = operandi coinvolti nell'operazione (per group by)
	#id_padre = identificativo del nodo padre
	#set_attrplain = set degli attributi che è necessario siano in chiaro per l'operazione
	#ordine = posizione del nodo (per quando ci sono più nodi su un solo livello, come nelle set operation)
	#profilo = profilo del nodo
	#candidati = set dei possibili assegnatari per il nodo
	#assegnatario = soggetto a cui è stato assegnato il nodo

	def __init__(self, tipo_op, dett_op, set_attributi, set_operandi, set_attrplain, id_padre, ordine):
		self.tipo_op = tipo_op
		self.dett_op = dett_op
		self.set_attr = set_attributi
		self.set_oper = set_operandi
		self.id_padre = id_padre
		self.set_attrplain = set_attrplain
		self.ordine = ordine
		self.profilo = {}
		self.profilo["vp"] = set()
		self.profilo["ve"] = set()
		self.profilo["ip"] = set()
		self.profilo["ie"] = set()
		self.profilo["eq"] = []
		self.profilo["rn"] = dict()
		self.candidati = set()
		self.assegnatario = ""

	def get_profilo(self):
		return (self.profilo["vp"], self.profilo["ve"], self.profilo["ip"], self.profilo["ie"], self.profilo["eq"], self.candidati, self.assegnatario, self.tipo_op, self.set_attr, self.set_oper, self.dett_op)


class query_plan(object):
	"""Classe che rappresenta l'albero della query"""

	def __init__(self):
		self.lista_nodi = dict()
		self.soggetti = dict()
		self.op_cif_dec = list() #Operazioni di cifratura/decifratura iniettate nel secondo step

	def add_nodo(self, id, nodo):
		self.lista_nodi[id] = nodo

	def add_nodo(self, id, tipo_op, dett_op, set_attributi, set_operandi, set_attrplain, id_padre, ordine):
		nodo = nodo_plan(tipo_op=tipo_op, dett_op=dett_op, set_attributi=set_attributi, set_operandi=set_operandi, set_attrplain=set_attrplain, id_padre=id_padre, ordine=ordine)
		self.lista_nodi[id] = nodo

	def get_nodo(self, id):
		return self.lista_nodi[id]

	def get_num_nodi(self):
		return len(self.lista_nodi)

	def set_subj(self, soggetti):
		#Conversione delle liste in set
		for chiave, valore in soggetti.items():
			soggetti[chiave]["p"] = set(valore["p"])
			soggetti[chiave]["e"] = set(valore["e"])
			soggetti[chiave]["own"] = set(valore["own"])
		self.soggetti = soggetti

	def get_ocd(self):
		return self.op_cif_dec


	def pulisci_profili(self):
		#Candidati calcolati: sbianco tutto
		for id, nodo in self.lista_nodi.items():
			self.lista_nodi[id].profilo["vp"] = set()
			self.lista_nodi[id].profilo["ve"] = set()
			self.lista_nodi[id].profilo["ip"] = set()
			self.lista_nodi[id].profilo["ie"] = set()
			self.lista_nodi[id].profilo["eq"] = []
			self.lista_nodi[id].profilo["rn"] = {}

	#Funzione di ottenimento dei set degli attributi che devono essere cifrati con la stessa chiave
	def get_asc(self):
		ins_eq = self.lista_nodi[1].profilo["eq"]
		
		lista_set_adc = list()
		set_attr_singoli = set()

		#Calcolo l'insieme degli attributi che da qualche parte deve essere cifrata
		set_adc = set()
		for ocd in self.op_cif_dec:
			if ocd["tipo_op"] == "C":
				set_adc.update(ocd["adc"])
			
		for subset in ins_eq:
			if subset.issubset(set_adc):
				lista_set_adc.append(subset)

		#Aggiungo gli attributi da cifrare singolarmente
		for ocd in self.op_cif_dec:
			if ocd["tipo_op"] == "C":
				#Per ogni singolo attributo da cifrare controllo se esso fa parte di un set di equivalenza, se no lo aggiungo come set singleton
				for adc in list(ocd["adc"]):
					found = False
					for subset in lista_set_adc:
						if adc in subset:
							found = True

					if not found:
						lista_set_adc.append(set(adc))
		
		#Determino i possessori delle chiavi
		res = list()
		for kes in lista_set_adc:
			tmp = dict()
			tmp["kes"] = kes
			tmp["sogg"] = set()

			#Ciclo sui singoli attributi da cifrare, e ricerco nelle operazioni di cifratura gli id dei nodi dai quali reperirò i candidati a cui vanno assegnate le chiavi
			for adc in list(kes):
				for ocd in self.op_cif_dec:
					if adc in ocd["adc"]:
						tmp["sogg"].add(ocd["exec"])

			res.append(tmp)

		return res



	#I profili sono calcolati secondo una visita post-order
	def esegui_step_rec(self, id, first_step):

		#Se siamo al nodo radice e siamo al secondo step, pulisco i profili
		if self.lista_nodi[id].id_padre == 0 and not first_step : 
			self.pulisci_profili()

		#Uso una variabile temporanea per migliorare la leggibilità
		curr_n = self.lista_nodi[id]

		#Determino i figli del nodo corrente
		figli = []
		
		for indice, nodo_tmp in self.lista_nodi.items():
			if nodo_tmp.id_padre == id:
				figli.append(indice)

		if len(figli) > 0:
			#Lancio il esegui_step_rec ricorsivamente su tutti i figli
			for figlio in figli:
				self.esegui_step_rec(figlio, first_step)
			
				#Per tutti i figli, faccio l'union degli insiemi (escluso che per le join e prodotti cartesiani, il figlio sarà uno solo sempre)
				for i in {'vp', 've', 'ip', 'ie'}:
					self.lista_nodi[id].profilo[i].update(self.lista_nodi[figlio].profilo[i])

				if(len(self.lista_nodi[figlio].profilo["eq"]) > 0):
					for subset in self.lista_nodi[figlio].profilo["eq"]:
						self.lista_nodi[id].profilo["eq"].append(subset)

				self.lista_nodi[id].profilo["rn"].update(self.lista_nodi[figlio].profilo["rn"])
		
		#Bonifica attributi rinominati per i profili
		for pseudo, real in curr_n.profilo["rn"].items():
			if pseudo in curr_n.set_attr:
				self.lista_nodi[id].set_attr = curr_n.set_attr.difference(pseudo).union(real)

			if pseudo in curr_n.set_oper:
				self.lista_nodi[id].set_oper = curr_n.set_oper.difference(pseudo).union(real)

			if pseudo in curr_n.set_attrplain:
				self.lista_nodi[id].set_attrplain = curr_n.set_attrplain.difference(pseudo).union(real) 

		#Calcolo l'effettivo candidato che eseguirà l'operazione
		if not first_step:
			self.sistema_set(id)
			
			if curr_n.tipo_op == 'proj' and self.lista_nodi[figli[0]].tipo_op == "base":
				#Caso particolare di proiezione eseguita subito dopo una tabella base: eredito come candidato l'owner della tabella
				self.lista_nodi[id].assegnatario = self.lista_nodi[figli[0]].assegnatario

			elif curr_n.tipo_op == "base":
				#Caso particolare di tablela base: prendo come candidato l'owner (creo questo caso per saltare i controlli sugli attributi da cifrare)
				self.lista_nodi[id].assegnatario = list(self.lista_nodi[id].candidati)[0]

			else:
				#Caso normale: calcolo del candidato corretto
				candidato = ""
				sogg_ord = (sorted(self.soggetti, key=lambda x: (self.soggetti[x]["pri"])))
				for sogg in sogg_ord:
					if sogg in self.lista_nodi[id].candidati:
						candidato = sogg
						break


				self.lista_nodi[id].assegnatario = candidato #Prendo il soggetto con priorità massima (valore "pri" minimo)
				auth_cand = self.soggetti[candidato] #Ne leggo le autorizzazioni

				attr_da_cifrare = set()

				#cifrature per sistemare le auth su attributi in chiaro
				attr_da_cifrare.update((curr_n.profilo["vp"]).difference(auth_cand["p"]))

				#cifrature per sistemare le auth su attributi in insiemi di equivalenza
				for subset in curr_n.profilo["eq"]:
					if not subset.issubset(auth_cand["p"]) and not subset.issubset(auth_cand["e"]):
						#Se la visibilità non è uniforme, cifro gli attributi attualmente in chiaro (e che non sono già da cifrare)
						attr_da_cifrare.update((subset.difference(auth_cand["e"])).difference(attr_da_cifrare))

				#Effettuo la cifratura vera e propria
				self.lista_nodi[id].profilo["vp"] = curr_n.profilo["vp"].difference(attr_da_cifrare)
				self.lista_nodi[id].profilo["ve"] = curr_n.profilo["ve"].union(attr_da_cifrare)

				#Mi segno l'operazione di cifratura che ho iniettato, ricercando il figlio al quale affidarla
				for figlio in figli:
					#Prendo gli attributi da cifrare per il figlio come intersezione tra l'insieme degli attributi da cifrare e gli attributi nel Rvp del figlio
					adc_figlio = self.lista_nodi[figlio].profilo["vp"].intersection(attr_da_cifrare)
					if len(adc_figlio):
						self.op_cif_dec.append({ "padre" : id , "figlio" : figlio, "tipo_op" : "C",  "adc" : adc_figlio, "exec" : self.lista_nodi[figlio].assegnatario})
						#Aggiorno i profili per il nodo figlio (è lui che effettua la cifratura)
						self.lista_nodi[figlio].profilo["vp"] = self.lista_nodi[figlio].profilo["vp"].difference(adc_figlio)
						self.lista_nodi[figlio].profilo["ve"] = self.lista_nodi[figlio].profilo["ve"].union(adc_figlio)


		#Valutazione degli attributi che bisogna avere per forza decifrati per il nodo
		attr_da_decifrare = curr_n.profilo["ve"].intersection(curr_n.set_attrplain)
		if len(attr_da_decifrare) > 0:
			self.lista_nodi[id].profilo["ve"] = curr_n.profilo["ve"].difference(attr_da_decifrare)
			self.lista_nodi[id].profilo["vp"] = curr_n.profilo["vp"].union(attr_da_decifrare)

			if not first_step:
				self.op_cif_dec.append({ "padre" : id , "figlio" : figli[0], "tipo_op" : "D", "adc" : attr_da_decifrare, "exec" : self.lista_nodi[id].assegnatario})	

		#Determino il profilo del nodo corrente
		if curr_n.tipo_op == "base":
			if first_step:
				#Mandata di calcolo set candidati: eseguo l'injection della cifratura, per calcolare i candidati possibili
				self.lista_nodi[id].profilo["ve"] = curr_n.set_attr

			else:
				#Mandata di determinazione dell'assegnatario: calcolo il vero profilo
				self.lista_nodi[id].profilo["vp"] = curr_n.set_attr

		elif curr_n.tipo_op == "proj":
			self.lista_nodi[id].profilo["vp"] = curr_n.profilo["vp"].intersection(curr_n.set_attr)
			self.lista_nodi[id].profilo["ve"] = curr_n.profilo["ve"].intersection(curr_n.set_attr)

		elif curr_n.tipo_op == "sel_val":
			self.lista_nodi[id].profilo["ip"] = curr_n.profilo["ip"].union(curr_n.profilo["vp"].intersection(curr_n.set_attr))
			self.lista_nodi[id].profilo["ie"] = curr_n.profilo["ie"].union(curr_n.profilo["ve"].intersection(curr_n.set_attr))

		elif curr_n.tipo_op == "sel_attr":
		   self.lista_nodi[id].profilo["eq"].append(curr_n.set_attr)       #Qua viene aggiunto un set dentro al set → rappresentare il set di attributi come frozenset o come tupla

		elif curr_n.tipo_op == "join":
			self.lista_nodi[id].profilo["eq"].append(curr_n.set_attr)       #Discorso analogo per sel_attr

		elif curr_n.tipo_op == "gby":
			self.lista_nodi[id].profilo["vp"] = curr_n.profilo["vp"].intersection(curr_n.set_attr.union(curr_n.set_oper))
			self.lista_nodi[id].profilo["ve"] = curr_n.profilo["ve"].intersection(curr_n.set_attr.union(curr_n.set_oper))
			self.lista_nodi[id].profilo["ip"] = curr_n.profilo["ip"].union(curr_n.profilo["vp"].intersection(curr_n.set_attr))
			self.lista_nodi[id].profilo["ie"] = curr_n.profilo["ie"].union(curr_n.profilo["ve"].intersection(curr_n.set_attr))
		
		elif curr_n.tipo_op == "rename_p":
			self.lista_nodi[id].profilo["rn"][list(curr_n.set_oper)[0]] = list(curr_n.set_attr)[0]
			self.lista_nodi[id].profilo["vp"] = curr_n.profilo["vp"].difference(curr_n.set_attr).union(curr_n.set_oper)

		elif curr_n.tipo_op == "rename_e":
			self.lista_nodi[id].profilo["rn"][list(curr_n.set_oper)[0]] = list(curr_n.set_attr)[0]
			self.lista_nodi[id].profilo["ve"] = curr_n.profilo["ve"].difference(curr_n.set_attr).union(curr_n.set_oper)
		
		elif curr_n.tipo_op == "udf":
			self.lista_nodi[id].profilo["vp"] = curr_n.profilo["vp"].difference((curr_n.set_attr.difference(curr_n.set_oper)))
			self.lista_nodi[id].profilo["ve"] = curr_n.profilo["ve"].difference((curr_n.set_attr.difference(curr_n.set_oper)))
			self.lista_nodi[id].profilo["eq"].append(curr_n.set_attr)

		elif curr_n.tipo_op == "encr":
			self.lista_nodi[id].profilo["vp"] = curr_n.profilo["vp"].difference(curr_n.set_attr)
			self.lista_nodi[id].profilo["ve"] = curr_n.profilo["ve"].union(curr_n.set_attr)

		elif curr_n.tipo_op == "decr":
			self.lista_nodi[id].profilo["ve"] = curr_n.profilo["ve"].difference(curr_n.set_attr)
			self.lista_nodi[id].profilo["vp"] = curr_n.profilo["vp"].union(curr_n.set_attr)

		if first_step:
			#Calcolo i candidati per il nodo
			if curr_n.tipo_op != 'base':
				#Tabella non base: calcolo candidati
				for subj, auth in self.soggetti.items():
					#Controllo autorizzazione per il plain text
					aut_plain = (curr_n.profilo["vp"].union(curr_n.profilo["ip"])).issubset(auth["p"])
				
					#Controllo autorizzazione per il cifrato
					aut_encr = (curr_n.profilo["ve"].union(curr_n.profilo["ie"])).issubset(auth["p"].union(auth["e"]))

					aut_eq = True
					#Controllo autorizzazione per insiemi di equivalenza
					for subset in curr_n.profilo["eq"]:
						aut_eq = aut_eq and (subset.issubset(auth["p"]) or subset.issubset(auth["e"]))

					if aut_plain and aut_encr and aut_eq:
						self.lista_nodi[id].candidati.add(subj)
			else:
				#Tabella base: cerco l'owner
				for subj, auth in self.soggetti.items():
					if curr_n.set_oper.issubset(auth["own"]):
						self.lista_nodi[id].candidati.add(subj)
			

	def sistema_set(self, id):
		#Mi ottengo la lista degli attributi in eq
		set_attr = set()
		for elem in self.lista_nodi[id].profilo["eq"]:
			set_attr.update(elem)

		#Creo un dizionario dove per ogni attributo in eq viene specificato il set collassato di appartenenza
		newEq = {}
		oldEq = {'dummy'}

		while oldEq != newEq:
			oldEq = newEq.copy()
			for attr in set_attr:
				newEq[attr] = set()
				for subset in self.lista_nodi[id].profilo["eq"]:
					if attr in subset:
						newEq[attr].update(subset)

		#Terminato il form che crea il dizionario ho un dizionario dove per ogni attributo in eq ho il relativo set collassato: creo una lista ignorando i doppioni
		self.lista_nodi[id].profilo["eq"] = []
		for key, sel in newEq.items():
			if sel not in self.lista_nodi[id].profilo["eq"]:
				self.lista_nodi[id].profilo["eq"].append(sel)

	def is_proj_after_base(self, id_nodo):
		#Determino i figli del nodo corrente
		figli = []
		
		for indice, nodo_tmp in self.lista_nodi.items():
			if nodo_tmp.id_padre == id_nodo:
				figli.append(indice)

		return self.lista_nodi[id_nodo].tipo_op == 'proj' and self.lista_nodi[figli[0]].tipo_op == "base"

