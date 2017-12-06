# -*- coding: utf-8 -*-

from gurobipy import *
import numpy as np
import matplotlib.pyplot as plt
from constants import *
import datetime
import timeit
import time

# xij = 1 si (i,j) case noire, 0 si case blanche
# yijt = 1 si le bloc t de la ligne i commence en (i,j), 0 sinon
# zijt = 1 si le bloc t de la colonne j commence en (i,j), 0 sinon


# Q12
# min z = sum(x[i, j]
# s.c.
# (pour tout i,j)
#
#   x[i,j] € {0,1}
#
#   sum( y[i, j, t] = 1 ) , t € [0..sli-1]
#TODO a completer


# Q13
# pour t variant de 0 a nb_blocks dans la ligne/colonne :
# si sum(block[t]) + t < i : yijt = 0
# si sum(block[t]) + t < j : zijt = 0
# --> on peut retirer ces éléments du modèle



"""
@param file_name: le nom d'un fichier contenant une instance du problème
@return sequences: 	une liste de deux listes. La première contient la description des lignes (une liste par ligne),
					la deuxième la description des colonnes (une liste par colonne).

					Par exemple: pour l'exemple donné dans l'énoncé, la fonction renvoie
					[[[3], [], [1, 1, 1], [3]], [[1, 1], [1], [1, 2], [1], [2]]]

					[3] - la première ligne contient un bloc de longueur 3
					[] - aucun bloc sur la deuxième ligne

					[1,1] - la première colonne contient deux blocs, chacun de longueur 1

					etc.
"""


def read_file(file_name):
	sequences = [[], []]  # première liste pour descriptions des lignes, deuxième pour description des colonnes
	
	indice = const.LINES  # d'abord, on décrit les lignes - on va remplir sequences[0]
	
	with open(file_name) as file:
		for line in file:  # pour chaque ligne du fichier
			if len(line) > 0 and line[0] == '#':  # on passe de la description des lignes à celle des colonnes
				indice = const.COLUMNS
			else:  # il s'agit d'une ligne décrivant une ligne/colonne
				# on transforme la ligne des caractères en une liste d'entiers, et on l'ajoute à la fin de sequences[0]/sequences[1]
				sequences[indice].append(list(map(int, line.split())))
	
	return sequences


def get_model(sequences):
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
				if sum(sl[i][:t]) + t <= j and sum(sl[i][t:]) + len(sl[i]) - (t+1) <= nbcolumns - j:
					y[i][j].append(m.addVar(vtype=GRB.BINARY, lb=0, name="y(%d,%d,%d)" % (i, j, t)))
				else:
					y[i][j].append(0)
			
			# parcours des sequences de la colonne j
			for t in range(len(sc[j])):
				# zijt
				if sum(sc[j][:t]) + t <= i and sum(sc[j][t:]) + len(sc[j]) - (t+1) <= nblines - i:
					z[i][j].append(m.addVar(vtype=GRB.BINARY, lb=0, name="z(%d,%d,%d)" % (i, j, t)))
				else:
					z[i][j].append(0)
					
			# pour t variant de 0 a nb_blocks dans la ligne/colonne :
			# si sum(block[t]) + t < i : yijt = 0
			# si sum(block[t]) + t < j : zijt = 0
			# --> on peut retirer ces éléments du modèle
	
	# maj du modele pour integrer les nouvelles variables
	m.update()
	
	obj = LinExpr();
	obj = sum([x[i][j] for i in range(nblines) for j in range(nbcolumns)])
	
	# definition de l'objectif
	m.setObjective(obj, GRB.MINIMIZE)
	
	# Definition des contraintes
	for i in range(nblines):
		
		for t in range(len(sl[i])):
			# un bloc ne doit apparaitre qu'une seule fois sur une ligne
			m.addConstr(sum([y[i][j][t] for j in range(nbcolumns)]) == 1)
			
		# il doit y avoir le bon nombre de cases par ligne
		m.addConstr(sum(x[i][:]) - sum(sl[i]) == 0)
		
		
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
				
				# for k in range(sl[i][t]):
				# 	# le bloc t+1 doit etre a au moins st+1 cases du bloc t
				# 	if t + 1 < len(sl[i]) and j + k + 1 < nbcolumns:
				# 		m.addConstr(y[i][j + k + 1][t + 1] - (1 - y[i][j][t]) <= 0)
			
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
				
				# for k in range(sc[j][t]):
				# 	# le bloc t+1 doit etre a au moins st+1 cases du bloc t
				# 	if t + 1 < len(sc[j]) and i + k + 1 < nblines:
				# 		m.addConstr(z[i + k + 1][j][t + 1] - (1 - z[i][j][t]) <= 0)
	
	for j in range(nbcolumns):
		# un bloc ne doit apparaitre qu'une seule fois sur une colonne
		for t in range(len(sc[j])):
			m.addConstr(sum([z[i][j][t] for i in range(nblines)]) == 1)
			
		# il doit y avoir le bon nombre de cases par ligne
		# print(sum(sc[j]))
		m.addConstr(sum([x[i][j] for i in range(nblines)]) - sum(sc[j]) == 0)
		
	return m, x, y, z


def solve(m):
	m.optimize()
	
	"""
	print
	'Solution optimale:'
	for j in range(2):
		print
		'w%d' % j, '=', w[j].x
	print
	"""


# print('Valeur de la fonction objectif :', m.objVal)

# affiche la figure correspondant a la solution
def printfigure(x):
	nb_lines = len(x)
	nb_columns = len(x[0])
	A = [[x[i][j].x for j in range(nb_columns)] for i in range(nb_lines)]
	
	plt.imshow(A, cmap="Greys", interpolation="nearest")
	# plt.rcParams["figure.figsize"] = (50,50)
	ax = plt.gca()
	
	# Major ticks
	ax.set_xticks(np.arange(0, nb_columns, 1));
	ax.set_yticks(np.arange(0, nb_lines, 1));
	
	# Minor ticks
	ax.set_xticks(np.arange(-.5, nb_columns, 1), minor=True);
	ax.set_yticks(np.arange(-.5, nb_lines, 1), minor=True);
	
	ax.grid(which="minor", color='grey', linestyle='-', linewidth=2)
	
	plt.show()


# ts = time.time()
# st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d-%H-%M-%S')
# plt.savefig(str(st) + "image" + str(num) + ".png")


m, x, y, z = (get_model(read_file("instances/16.txt")))
solve(m)

# for i in range(len(y)):
# 	for j in range(len(y[i])):
# 		for t in range(len(y[i][j])):
# 			if y[i][j][t].x != 0: print(y[i][j][t])
# for i in range(len(z)):
# 	for j in range(len(z[i])):
# 		for t in range(len(z[i][j])):
# 			if z[i][j][t].x != 0: print(z[i][j][t])

printfigure(x)
