# -*- coding: utf-8 -*-

from gurobipy import *
import numpy as np
import matplotlib.pyplot as plt
from constants import *
import datetime
import timeit
import time
import multiprocessing
from multiprocessing import Queue
import os

from mogpl_part1_v2 import *
from mogpl_part3 import *

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
# TODO a completer


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
	
	return m, x, y, z


# Appel rapide a la fonction de resolution en PLNE.
# Le out_q sert a renvoyer le resultat en cas d'appel avec timeout.
def algo_plne(sequences, out_q=Queue()):
	m, x, y, z = (get_model(sequences))
	m.optimize()
	nb_lines = len(x)
	nb_columns = len(x[0])
	A = [[x[i][j].x for j in range(nb_columns)] for i in range(nb_lines)]
	out_q.put(A)
	return A


# Appel rapide a la fonction de resolution en programmation dynamique.
# Le out_q sert a renvoyer le resultat en cas d'appel avec timeout.
def algo_dynamique(sequences, out_q=Queue()):
	A = np.full((len(sequences[0]), len(sequences[1])), const.NOT_COLORED)
	coloration(A, sequences)
	out_q.put(A)
	return A


# affiche la figure correspondant a la solution
def printfigure(A):
	# print(A)
	
	plt.imshow(A, cmap="Greys", interpolation="nearest")
	ax = plt.gca()
	
	# Minor ticks
	ax.set_xticks(np.arange(-.5, len(A[0]), 1), minor=True);
	ax.set_yticks(np.arange(-.5, len(A), 1), minor=True);
	
	ax.grid(which="minor", color='grey', linestyle=':', linewidth=1)
	
	plt.show()


# test des differentes methodes (passees dans un tableau)
# path : le chemin du dossier des instances
# timeout : temps en secondes (0 = aucun)
# min : le numero de la premiere instance a traiter
# max : la derniere instance
# save : booleen pour sauvegarder les images calculees
# print_image : afficher les images calculees /!| ATTENTION met en pause l'execution !
def testMethods(path, functions, timeout=120, min=0, max=16, save=False, print_image=False):
	all_times = [[] for x in range(min, max + 1)]
	out_q = Queue()
	
	for i in range(min, max + 1):
		
		sequences = read_file(os.path.join(path, str(i) + ".txt"))
		for f in functions:
			print("\nTest sur " + str(i) + ".txt : " + f.__name__ + " ...\n")
			start_time = time.time()
			execution_time = timeout * 1.1  # on rajoute 10% pour distinguer de ceux qui ont termine juste avant la fin
			if __name__ == '__main__':
				# executer le processus en parallele
				p = multiprocessing.Process(target=f, args=(sequences, out_q))
				p.start()
				p.join(timeout)
				
				# On stoppe p s'il est trop long
				if p.is_alive():
					print("\nTemps dépassé, arret du processus de l'instance " + str(i) + " (" + f.__name__ + ")")
					p.terminate()
					p.join()
				else:
					execution_time = time.time() - start_time
					print(
						"\nTest terminé, temps d'execution de l'instance " + str(i) + " (" + f.__name__ + ") : " + str(
							execution_time) + "\n")
					A = out_q.get()
					
					# test de la validite du resultat
					if any(A[l][c] == const.NOT_COLORED for l in range(len(A)) for c in range(len(A[0]))):
						print("La solution n'est pas valide.\n")
						execution_time = timeout * 1.1
					
					# generation de la figure
					plt.imshow(A, cmap="Greys", interpolation="nearest")
					ax = plt.gca()
					
					# Minor ticks
					ax.set_xticks(np.arange(-.5, len(A[0]), 1), minor=True);
					ax.set_yticks(np.arange(-.5, len(A), 1), minor=True);
					
					ax.grid(which="minor", color='grey', linestyle=':', linewidth=1)
					
					st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
					
					if (save): plt.savefig("image" + str(i) + "_" + f.__name__ + "_" + str(st) + ".png")
					
					if (print_image): plt.show()
			
			all_times[i - min].append(execution_time)
	
	# generation et sauvegarde du graphe
	plt.gcf().clear()
	
	lines = [[] for f in range(len(functions))]
	for f in range(len(functions)):
		lines[f], = plt.plot([all_times[i][f] for i in range(len(all_times))], label=functions[f].__name__)
	plt.legend(handles=lines)
	
	st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
	plt.savefig("benchmark_all" + "_" + str(st) + ".png")
	
	print("\nLe graphe a été enregistré dans le répertoire courant.")  # affichage d'une seule instance
	plt.show()


# Ancienne methode pour avoir une instance

# m, x, y, z = (get_model(read_file("instances/14.txt")))
# m.optimize()
# nb_lines = len(x)
# nb_columns = len(x[0])
# A = [[x[i][j].x for j in range(nb_columns)] for i in range(nb_lines)]
# printfigure(x)

# Test global de toutes les methodes avec toutes les instances
testMethods("instances", [algo_plne, algo_dynamique, algo_hybride], timeout=5, min=0, max=16, save=False, print_image=False)
