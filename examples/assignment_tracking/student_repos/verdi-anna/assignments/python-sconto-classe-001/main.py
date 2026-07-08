def prezzo_finale(prezzo, tessera):
    sconto = 0.1 if tessera else 0
    return round(prezzo * (1 - sconto), 2)


print(prezzo_finale(19.99, True))
