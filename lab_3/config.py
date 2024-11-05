PATTERNS = {
    "telephone": "^\\+7-\\(\\d{3}\\)-\\d{3}-\\d{2}-\\d{2}$",
    "height": "^[0-2]\\.\\d{2}$",
    "inn": "^\\d{12}$",
    "identifier": "^\\d{2}\\-\\d{2}/\\d{2}$",
    "occupation": "^[a-zA-Zа-яА-ЯёЁ\\s-]+$",
    "latitude": "^[+-]?(([1-8]?[0-9])(\\.[0-9]{1,6})?|90(\\.0{1,6})?)$",
    "blood_type": "^(A|B|AB|O)[+−]$",
    "issn": "^\\d{4}-\\d{4}$",
    "uuid": "^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$",
    "date": "^\\d{4}-\\d{2}-\\d{2}$",
}

CSV_PATH = "80.csv"
RESULT_PATH = "result.json"
