def prezzo_finale(prezzo, tessera):
    if tessera:
        prezzo *= 0.9
    return round(prezzo, 2)


print(prezzo_finale(100, True))
