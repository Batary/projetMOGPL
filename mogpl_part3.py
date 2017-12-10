# -*- coding: utf-8 -*-

from gurobipy import *
import numpy as np
import matplotlib.pyplot as plt
from constants import *
import time
import multiprocessing
from multiprocessing import Queue

from mogpl_part1_v2 import coloration

#TODO a terminer

# Algorithme tentant d'abord la resolution par programmation dynamique, puis la resolution en PLNE avec la valeur de retour.
# Le out_q sert a renvoyer le resultat en cas d'appel avec timeout.
def algo_hybride(sequences, out_q=Queue()):
	m = Model("mogpl")
	
	# sequences des lignes et des colonnes
	sl = sequences[const.LINES]
	sc = sequences[const.COLUMNS]
	nblines = len(sl)
	nbcolumns = len(sc)
	
	# declaration des variables
	x = []
	y = []
	z = []
	for i in range(nblines):
		x.append([])
		y.append([])
		z.append([])
		for j in range(nbcolumns):
			# xij
			x[i].append(m.addVar(vtype=GRB.BINARY, lb=0, name="x(%d,%d)" % (i, j)))
			y[i].append([])
			z[i].append([])
			
			# parcours des sequences de la ligne i
			for t in range(len(sl[i])):
				# yijt
				if sum(sl[i][:t]) + t <= j and sum(sl[i][t:]) + len(sl[i]) - (t + 1) <= nbcolumns - j:
					y[i][j].append(m.addVar(vtype=GRB.BINARY, lb=0, name="y(%d,%d,%d)" % (i, j, t)))
				else:
					y[i][j].append(0)
			
			# parcours des sequences de la colonne j
			for t in range(len(sc[j])):
				# zijt
				if sum(sc[j][:t]) + t <= i and sum(sc[j][t:]) + len(sc[j]) - (t + 1) <= nblines - i:
					z[i][j].append(m.addVar(vtype=GRB.BINARY, lb=0, name="z(%d,%d,%d)" % (i, j, t)))
				else:
					z[i][j].append(0)
				
				# pour t variant de 0 a nb_blocks dans la ligne/colonne :
				# si sum(block[t]) + t < i : yijt = 0
				# si sum(block[t]) + t < j : zijt = 0
				# --> on peut retirer ces éléments du modèle
	
	# maj du modele pour integrer les nouvelles variables
	m.update()
	
	# obj = LinExpr();
	# obj = sum([x[i][j] for i in range(nblines) for j in range(nbcolumns)])
	
	# definition de l'objectif
	m.setObjective(0, GRB.MINIMIZE)
	
	# Definition des contraintes
	for i in range(nblines):
		
		for t in range(len(sl[i])):
			# un bloc ne doit apparaitre qu'une seule fois sur une ligne
			m.addConstr(sum([y[i][j][t] for j in range(nbcolumns)]) == 1)
		
		# il doit y avoir le bon nombre de cases par ligne
		m.addConstr(sum(x[i]) - sum(sl[i]) == 0)
		
		for j in range(nbcolumns):
			
			# parcours des blocs d'une ligne
			for t in range(len(sl[i])):
				
				# le bloc t+1 doit se trouver apres le bloc t
				if t + 1 < len(sl[i]):
					m.addConstr(y[i][j][t] - sum([y[i][b][t + 1] for b in range(j + sl[i][t] + 1, nbcolumns)]) <= 0)
				
				# si le bloc t demarre a la position j, alors les cases qui suivent doivent etre noires sur la longueur du bloc
				if nbcolumns >= j + sl[i][t]:
					m.addConstr(y[i][j][t] - sum([x[i][j + k] for k in range(sl[i][t])]) / sl[i][t] <= 0)
				# else:
				# 	m.addConstr(y[i][j][t] == 0)  # a enlever en retirant les variables
			
			# parcours des blocs d'une colonne
			for t in range(len(sc[j])):
				
				# le bloc t+1 doit se trouver apres le bloc t
				if t + 1 < len(sc[j]):
					m.addConstr(z[i][j][t] - sum([z[b][j][t + 1] for b in range(i + sc[j][t] + 1, nblines)]) <= 0)
				
				# si le bloc t demarre a la position i, alors les cases qui suivent doivent etre noires sur la longueur du bloc
				if nblines >= i + sc[j][t]:
					m.addConstr(z[i][j][t] - sum([x[i + k][j] for k in range(sc[j][t])]) / sc[j][t] <= 0)
				# else:
				# 	m.addConstr(z[i][j][t] == 0)  # a enlever en retirant les variables
	
	for j in range(nbcolumns):
		# un bloc ne doit apparaitre qu'une seule fois sur une colonne
		for t in range(len(sc[j])):
			m.addConstr(sum([z[i][j][t] for i in range(nblines)]) == 1)
		
		# il doit y avoir le bon nombre de cases par ligne
		m.addConstr(sum([x[i][j] for i in range(nblines)]) - sum(sc[j]) == 0)
		
	#Pretraitement par l'algorithme dynamique: 
	pre = np.full((len(sequences[0]), len(sequences[1])), const.NOT_COLORED)
	coloration(pre, sequences)
	
	#On fixe la valeur des cases déterminées: 
	for i in range(len(pre)):
		for j in range(len(pre[0])):
			#Si la case a été coloriée lors de pretraitement:
			if pre[i][j] == const.BLACK: #pour la case noire
				x[i][j].LB = const.BLACK #on fixe la borne inférieure de la variable correspondante à 1
			elif pre[i][j] == const.WHITE: #pour la case blanche
				x[i][j].UB = const.WHITE #on fixe la borne supérieure de la variable correspondante à 0
	
	m.optimize()
	nb_lines = len(x)
	nb_columns = len(x[0])
	A = [[x[i][j].x for j in range(nb_columns)] for i in range(nb_lines)]
	out_q.put(A)
	return A
