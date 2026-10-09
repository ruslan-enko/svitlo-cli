"""Address and street to group mapping helper for Lviv."""


# Known common street/district mappings to group numbers in Lviv
LVIV_STREET_MAPPINGS: list[dict[str, str]] = [
    {"street": "вул. Франка", "district": "Галицький", "group": "1.1"},
    {"street": "вул. Дорошенка", "district": "Галицький", "group": "1.2"},
    {"street": "вул. Городоцька", "district": "Залізничний", "group": "2.1"},
    {"street": "вул. Шевченка", "district": "Шевченківський", "group": "2.2"},
    {"street": "просп. Червоної Калини", "district": "Сихівський", "group": "3.1"},
    {"street": "вул. Стрийська", "district": "Сихівський", "group": "3.2"},
    {"street": "вул. Зелена", "district": "Личаківський", "group": "4.1"},
    {"street": "вул. Личаківська", "district": "Личаківський", "group": "4.2"},
    {"street": "вул. Кульпарківська", "district": "Франківський", "group": "5.1"},
    {"street": "вул. Наукова", "district": "Франківський", "group": "5.2"},
    {"street": "вул. Чорновола", "district": "Шевченківський", "group": "6.1"},
    {"street": "вул. Мазепи", "district": "Шевченківський", "group": "6.2"},
]


def search_address(query: str) -> list[dict[str, str]]:
    """Search for street or district matching query."""
    if not query or len(query.strip()) < 2:
        return []

    q = query.lower().strip()
    results = []
    for item in LVIV_STREET_MAPPINGS:
        if q in item["street"].lower() or q in item["district"].lower() or q in item["group"].lower():
            results.append(item)

    return results
