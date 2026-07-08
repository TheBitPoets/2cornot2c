def prezzo_finale(prezzo, tessera):
    if tessera:
        return prezzo - 10
    return prezzo


print(prezzo_finale(100, True))
