def trouver_plus_grand_nombre(liste):
    if not liste:
        return None  # Gérer le cas d'une liste vide
    plus_grand = liste[0]  # Initialiser avec le premier élément
    for nombre in liste:
        if nombre > plus_grand:
            plus_grand = nombre  # Mettre à jour le plus grand nombre
    return plus_grand

# Exemple d'utilisation
liste_exemple = [3, 5, 2, 8, 1]
print(trouver_plus_grand_nombre(liste_exemple))  # Affiche 8