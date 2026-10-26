TRANSITIONS = {
    "em_revisao": {"validada", "publicada"},
    "validada": {"em_revisao"},
    "publicada": {"validada"},
    "arquivada": {"em_revisao", "validada", "publicada"},
}


def can_transition(current: str, target: str) -> bool:
    return current in TRANSITIONS.get(target, set())
