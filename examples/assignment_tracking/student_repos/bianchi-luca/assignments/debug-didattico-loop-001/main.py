def somma_primi_n(n):
    totale = 0
    for numero in range(1, n):
        totale += numero
    return totale


print(somma_primi_n(5))
