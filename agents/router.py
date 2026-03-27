ROUTING_RULES = {
    "training_technique": ["техніка", "як робити", "як правильно", "помилки", "біомеханіка"],
    "training_program": ["програма", "замінити", "додати вправу", "скільки підходів", "спліт"],
    "training_progress": ["прогрес", "стагнація", "вага не росте", "плато"],
    "pain_injury": ["болить", "біль", "травма", "дискомфорт", "не можу"],
    "nutrition": ["їжа", "калорії", "білок", "дієта", "що їсти", "meal"],
    "sleep_recovery": ["сон", "відновлення", "втома", "спати", "розтяжка"],
    "motivation": ["мотивація", "лінь", "не хочу", "складно", "пропустила"],
    "general": [],
}


def classify_message(message: str) -> str:
    message_lower = message.lower()
    for module, keywords in ROUTING_RULES.items():
        if module == "general":
            continue
        for keyword in keywords:
            if keyword in message_lower:
                return module
    return "general"
