from formatters import format_summary
from stats import summarize


def parse_numbers(raw_text):
    values = []
    for part in raw_text.split():
        values.append(float(part))
    return values


def main():
    raw_text = "4 8 15 16 23 42"
    numbers = parse_numbers(raw_text)
    summary = summarize(numbers)
    print(format_summary(summary))


if __name__ == "__main__":
    main()
