TRANSITIONS = {
    "em_revisao": {"rascunho"},
    "validada": {"em_revisao"},
    "publicada": {"validada"},
    "arquivada": {"rascunho", "em_revisao", "validada", "publicada"},
}


def can_transition(current: str, target: str) -> bool:
    return current in TRANSITIONS.get(target, set())
