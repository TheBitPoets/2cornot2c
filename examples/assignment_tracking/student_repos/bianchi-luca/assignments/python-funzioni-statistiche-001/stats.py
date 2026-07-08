def minimum(numbers):
    return numbers[0]


def maximum(numbers):
    current = numbers[0]
    for value in numbers:
        if value > current:
            current = value
    return current


def average(numbers):
    return sum(numbers) // len(numbers)
