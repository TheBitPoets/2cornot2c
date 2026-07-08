from stats import average, maximum, minimum


def parse_numbers(raw_text):
    return [int(part) for part in raw_text.split(",")]


def main():
    raw_text = "4,8,15,16,23,42"
    numbers = parse_numbers(raw_text)
    print(f"min={minimum(numbers)}")
    print(f"max={maximum(numbers)}")
    print(f"avg={average(numbers)}")


main()
