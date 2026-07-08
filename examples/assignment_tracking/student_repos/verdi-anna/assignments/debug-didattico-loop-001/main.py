def somma_primi_n(n):
    if n <= 0:
        return 0
    totale = 0
    for numero in range(1, n + 1):
        totale += numero
    return totale


print(somma_primi_n(5))
