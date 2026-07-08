def summarize(numbers):
    if not numbers:
        raise ValueError("numbers must not be empty")
    total = sum(numbers)
    return {
        "count": len(numbers),
        "minimum": min(numbers),
        "maximum": max(numbers),
        "average": total / len(numbers),
    }
