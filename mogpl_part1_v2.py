import numpy as np
import matplotlib.pyplot as plt
from constants import *
import datetime
import timeit
import time

"""
@param file_name: le nom d'un fichier contenant une instance du problème
@return sequences: 	une liste de deux listes. La première contient la description des lignes (une liste par ligne), 
				 	la deuxième la description des colonnes (une liste par colonne).

					Par exemple: pour l'exemple donné dans l'énoncé, la fonction renvoie 
					[[[3], [], [1, 1, 1], [3]], [[1, 1], [1], [1, 2], [1], [2]]]

					[3] - la première ligne contienne un bloc de la longueur 3
					[] - aucun bloc sur la deuxième ligne

					[1,1] - la première colonne contienne deux blocs, chacun de longueur 1

					etc.
"""
def read_file(file_name):
	sequences = [[], []] #première liste pour descriptions des lignes, deuxième piur description des colonnes
	
	indice = const.LINES # d'abord, on décrit les lignes - on va remplir sequences[0]

	with open(file_name) as file: 
		for line in file: #pour chaque ligne du fichier
			if len(line) > 0 and line[0] == '#': # on passe de la déscription des lignes à celle des colonnes
				indice = const.COLUMNS
			else: #il s'agit d'une ligne décrivant une ligne/colonne
				#on transforme la ligne des caractères en une liste des entiers, et on l'append à la fin de sequences[0]/sequences[1]
				sequences[indice].append(list(map(int, line.split()))) 
			
	return sequences


""" Réponse à la question Q4:

 Fonction qui permet de décider si il est possible de colorier la ligne avec sa séquence associée 
 @param line_length: le nombre de cases de la ligne
 @param line_sequence: la séquence des blocs avec lesquels on veut colorier la ligne
 @return : True si possible de colorier toute la ligne avec toutes les blocs, False sinon
"""
def colour_line(line_length, line_sequence):
	
	#si la séquence est vide (aucun bloc), on renvoie directement True
	if not line_sequence: 
		return True

	#sinon:

	T = np.zeros((line_length, len(line_sequence)+1)) #T[j][l] = True si possible de colorier j+1 premières cases avec l premiers blocs, False sinon

	#Quelques cas de base: 
	for j in range(line_length): 
		T[j][0] = True #il est toujours possible de colorier n'importe quel nombre de cases avec 0 blocs
		T[j][1] = (j >= line_sequence[0]-1) #cas où on a un seul bloc - on peut colorier la ligne avec ssi sa longueur est <= nombre de cases considérées

	for l in range(2, len(line_sequence)+1): #cas où ou considère au moins 2 blocs
		for j in range(line_length): 
			if j < sum(line_sequence[0:l]): #si la somme des longueurs des blocs est plus grand que le nombre de cases considérés, T[j][l] est fausse
				T[j][l] = False
			else: #sinon
				# - soit le dernière bloc finit sur la case j+1. Dans un tel cas, T[j][l] est vraie ssi on peut faire rentrer les blocs précédents aux cases
				#	 devant le début de ce dernière bloc (il ne faut pas oublié une espace blanche entre deux blocs!)

				# - soit la dernière case est blanche. Dans ce cas, T[j][l] ssi T[j-1][l]
				T[j][l] = T[j - line_sequence[l-1] -1][l-1] or T[j-1][l]
	
	#On renvoie la "dernière" case du tableau indiquant si on peut colorier toute la ligne avec toute la séquence
	return T[-1][-1]


""" Réponse à la question 6: 
	La fonction permet de décider si on peut colorier toute la ligne avec toute la séquence, sachant que certaines cases 
	sont déjà fixées à noire ou blanche.

	@param line: une liste de longueur M (M = nombre de colonnes) dont le i-ième élément est:
					- const.BLACK si la i-ième case de la ligne est déjà noire
					- const.WHITE si li i-ième case de la ligne est déjà blanche
					- const.NOT_COLORED si la case n'était pas encore coloriée
	@param line_sequence: la séquence des blocs avec lesquels on veut colorier la ligne
 	@return : True si possible de colorier toute la ligne avec toutes les blocs, False sinon
"""


def colour_line_bis(line, line_sequence):
	#si la séquence est vide (aucun bloc), la réponse est TRUE ssi il n'y a pas de case déjà coloriée à noir.
	if not line_sequence:
		return (const.BLACK not in line)
		
	
	#sinon:
	line_length = len(line)  
	T = np.zeros((line_length, len(line_sequence)+1)) #T[j][l] = True si possible de colorier j+1 premières cases avec l premiers blocs, False sinon
	

	#Cas où on considère 0 blocs
	for j in range(line_length):
		T[j][0] = (const.BLACK not in line)

	
	for j in range(line_length):
		if j < line_sequence[0]-1: # -1 oublié!!!! Maintenant, ça devrait marcher
			T[j][1] = False
		else:
			#print("j = ", j)
			last_black = const.WHITE not in line[j - line_sequence[0]+1:j+1]
			#print("last black: ",last_black)
			box_before = (j-line_sequence[0] < 0) or (j-line_sequence[0] >= 0 and line[j - line_sequence[0]] != const.BLACK)
			#print("box before: ", box_before)
			box_after = (j+1 >= line_length) or (j+1 < line_length and line[j+1] != const.BLACK)
			#print("box after: ", box_after)
			T[j][1] = last_black and box_before and box_after and (list(line[0:j+1]).count(const.BLACK) <= line_sequence[0])
			T[j][1] = T[j][1] or (T[j-1][1] and line[j] != const.BLACK) 
	#print("Fin cas 1 bloc, T = ", T)
	#On considère enfin plus qu'un bloc:
	for l in range(2, len(line_sequence)+1):
		#print(T)
		for j in range(line_length):
			if j < sum(line_sequence[0:l]): #si la somme des longueurs des blocs est plus grand que le nombre de cases considérés, T[j][l] est fausse
				T[j][l] = False
			else:
				#print("l et j: ",l, j)
				#soit le dernier bloc finit sur la dernière case considéré:
				last_black = const.WHITE not in line[j - line_sequence[l-1]+1:j+1]
				#print("last black: ",last_black)
				box_before = (j-line_sequence[l-1] < 0) or (j-line_sequence[l-1] >= 0 and line[j - line_sequence[l-1]] != const.BLACK)
				#print("box before: ", box_before)
				box_after = (j+1 >= line_length) or (j+1 < line_length and line[j+1] != const.BLACK)
				#print("box after: ", box_after)
				recurence = ((j - line_sequence[l-1] > 0)  and (T[j - line_sequence[l-1] -1][l-1])) or (j - line_sequence[l-1] <= 0) 
				#print("recurrence: ", recurence)
				T[j][l] = last_black and box_before and box_after and recurence and (list(line[0:j+1]).count(const.BLACK) <= sum(line_sequence[0:l])) and (list(line[j+1:]).count(const.BLACK) <= sum(line_sequence[l:]))
				#print("T[j][l]: ", T[j][l])
				#soit le dernier bloc finit avant:
				T[j][l] = T[j][l] or (T[j-1][l] and line[j] != const.BLACK) 
				#print(T[j][l])
			
	#print(T)
	return T[-1][-1]

def coloration(A, sequences):
	lines_to_see = [i for i in range(len(A))]
	columns_to_see = [i for i in range(len(A[0]))]

	

	while lines_to_see or columns_to_see:
		for i in lines_to_see:
			new_to_see = []
			for j in range(len(A[i])):
				can_colour = [False, False]
				if A[i][j] == const.NOT_COLORED:
					A[i][j] = const.WHITE
					can_colour[const.WHITE] = colour_line_bis(A[i], sequences[const.LINES][i]) 
					A[i][j] = const.BLACK
					can_colour[const.BLACK] = colour_line_bis(A[i], sequences[const.LINES][i]) 

					if (can_colour[const.WHITE]) and (not can_colour[const.BLACK]):
						A[i][j] = const.WHITE
						new_to_see += [j]
					elif (can_colour[const.BLACK]) and (not can_colour[const.WHITE]):
						A[i][j] = const.BLACK
						new_to_see += [j]
					elif (can_colour[const.WHITE]) and (can_colour[const.BLACK]):
						A[i][j] = const.NOT_COLORED
					else:
						return null #pas de solution

			columns_to_see = list(set().union(columns_to_see, new_to_see))
		
		lines_to_see = []
		
		for j in columns_to_see:
			new_to_see = []
			for i in range(len(np.transpose(A)[j])):
				can_colour = [False, False]
				if A[i][j] == const.NOT_COLORED:
					A[i][j] = const.WHITE
					can_colour[const.WHITE] = colour_line_bis(np.transpose(A)[j], sequences[const.COLUMNS][j]) 
					A[i][j] = const.BLACK
					can_colour[const.BLACK] = colour_line_bis(np.transpose(A)[j], sequences[const.COLUMNS][j]) 
					if (can_colour[const.WHITE]) and (not can_colour[const.BLACK]):
						A[i][j] = const.WHITE
						new_to_see += [i]
					elif (can_colour[const.BLACK]) and (not can_colour[const.WHITE]):
						A[i][j] = const.BLACK
						new_to_see += [i]
					elif (can_colour[const.WHITE]) and (can_colour[const.BLACK]):
						A[i][j] = const.NOT_COLORED
					else:
						return null #pas de solution
			
			lines_to_see = list(set().union(lines_to_see, new_to_see))
		
		columns_to_see = []
		
	return A 


#Quelques testes - TODO 29.1.2017: à nettoyer/organiser
num = 10
sequences = read_file(str(num)+".txt")
print("Contenu du fichier: ",sequences)

nb_lines = len(sequences[0])
nb_columns = len(sequences[1])
A = np.full((nb_lines, nb_columns), const.NOT_COLORED)
"""A = np.array([[ 0,  0,  0,  1,  1],
 [ 1,  1,  1, -1, -1],
 [ 0,  1,  0,  1,  0],
 [ 1, -1,  0,  0, -1]])"""
start_time = timeit.default_timer()
coloration(A, sequences)
elapsed = timeit.default_timer() - start_time
print("Temps d'execution: ",elapsed)

#T = colour_line(nb_columns, sequences[0][2])
#print(T)



#pour visualiser la coloriage - utile peut être dans la suite, le test ici ne donne pas de sens, 
#c'était juste pour comprendre comment peut-on faire se genre de graphique...

#plt.subplot(211)
plt.imshow(A, cmap = "Greys", interpolation = "nearest")
#plt.rcParams["figure.figsize"] = (50,50)
ax = plt.gca()

# Major ticks
ax.set_xticks(np.arange(0, nb_columns, 1));
ax.set_yticks(np.arange(0, nb_lines, 1));

# Minor ticks
ax.set_xticks(np.arange(-.5, nb_columns, 1), minor=True);
ax.set_yticks(np.arange(-.5, nb_lines, 1), minor=True);

ax.grid(which = "minor", color='grey', linestyle='-', linewidth=2)

plt.show()
ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d-%H-%M-%S')
plt.savefig(str(st)+"image"+str(num)+".png")


line = [-1 for i in range(nb_columns)]
line[3] = const.BLACK
print(colour_line_bis(line, sequences[0][2]))