import numpy as np
import matplotlib.pyplot as plt
from constants import *

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
def color_line(line_length, line_sequence):
	
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
def color_line_bis(line, line_sequence):

	#si la séquence est vide (aucun bloc), on renvoie directement True
	if not line_sequence:
		return True
	
	#sinon:
	line_length = len(line)  
	T = np.zeros((line_length, len(line_sequence)+1)) #T[j][l] = True si possible de colorier j+1 premières cases avec l premiers blocs, False sinon

	#Cas où on considère 0 blocs
	for j in range(line_length):
		T[j][0] = True

	#Si on considère un seul bloc:
	for j in range(line_length):
		if j< line_sequence[0] -1: #si le nombre de cases est plus petit que la taille d'un bloc
			T[j][1] = False
		elif j == line_sequence[0]-1 : #nombre de cases est exactement la taille d'un bloc 
			#le bloc commence sur la première case et finit sur la dernière case considérée. La case suivante n'est pas noire
			T[j][1] = ((const.WHITE not in line[j-line_sequence[0]+1:j+1]) and (line[j+1] != const.BLACK)) 
		elif j< line_length-1:
			#si le nombre de cases est au moins la longueur du bloc, mais pas la ligne en entière:
			# - soit le bloc finit sur la case j+1. Dans ce cas, toutes les cases entre son début et fin doivent être noires ou indéterminés. 
			#	La case juste avant le début ne peut pas être noire, et la case après la fin ne peut pas être noire non plus. 
			# - soit le bloc se finit avant (partie droite de la disjonction)
			T[j][1] = ((const.WHITE not in line[j-line_sequence[0]+1:j+1]) and (line[j-line_sequence[0]] != const.BLACK) and (line[j+1] != const.BLACK)) or (True in T[:,1][0:j])
		else: #on considère la ligne en entière - le même cas que précédamment, on n'a juste pas la case suivante
			T[j][1] = ((const.WHITE not in line[j-line_sequence[0]+1:j+1]) and (line[j-line_sequence[0]] != const.BLACK)) or (True in T[:,1][0:j])

	
	#On considère enfin plus qu'un bloc:
	for l in range(2, len(line_sequence)+1):
		for j in range(line_length):
			if j < sum(line_sequence[0:l]): #si la somme des longueurs des blocs est plus grand que le nombre de cases considérés, T[j][l] est fausse
				T[j][l] = False
			elif j< line_length-1: 
				# - soit le dernier bloc finit sur la case j+1. Dans ce cas là, aucune case entre le début et la fin du bloc ne peut pas être coloriée à blanche, 
				#	et la case suivante et précédente ne peut pas être noire.
				# - soit le dernier bloc finit avant, dans quel cas la case j+1 ne peut pas être noire et T[j-1][l] doit être vraie pour qu'on ait T[j][l] vraie
				T[j][l] = (T[j - line_sequence[l-1] -1][l-1] and const.WHITE not in line[j-line_sequence[l-1]+1:j+1] and line[j-line_sequence[l-1]] != const.BLACK and line[j+1] != const.BLACK) or (T[j-1][l] and line[j] != const.BLACK)
				
			else: # j = line_lenght+1
				T[j][l] = (T[j - line_sequence[l-1] -1][l-1] and const.WHITE not in line[j-line_sequence[l-1] +1 :j+1] and line[j-line_sequence[l-1]] != const.BLACK) or (T[j-1][l] and line[j] != const.BLACK)
	print(T)
	return T[-1][-1]


#Quelques testes - TODO 29.1.2017: à nettoyer/organiser
sequences = read_file("0.txt")
print("Contenu du fichier: ",sequences)

nb_lines = len(sequences[0])
nb_columns = len(sequences[1])

T = color_line(nb_columns, sequences[0][2])
print(T)


#pour visualiser la coloriage - utile peut être dans la suite, le test ici ne donne pas de sens, 
#c'était juste pour comprendre comment peut-on faire se genre de graphique...
"""
plt.subplot(211)
plt.imshow(T, cmap = "Greys", interpolation = "nearest")
ax = plt.gca()

# Major ticks
ax.set_xticks(np.arange(0, nb_columns, 1));
ax.set_yticks(np.arange(0, nb_lines, 1));

# Minor ticks
ax.set_xticks(np.arange(-.5, nb_columns, 1), minor=True);
ax.set_yticks(np.arange(-.5, nb_lines, 1), minor=True);

ax.grid(which = "minor", color='grey', linestyle='-', linewidth=2)
plt.show()
"""


line = [-1 for i in range(nb_columns)]
line[3] = const.BLACK
print(color_line_bis(line, sequences[0][2]))