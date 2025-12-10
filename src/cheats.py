# cheats.py
"""
Motor de cheats independente da lógica do jogo.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class CheatState:
    progress: int = 0   # progresso na sequência
    active: bool = False


class CheatEngine:
    def __init__(self, codes: List[str] | None = None) -> None:
        if codes is None:
            codes = ["GOD", "TIME", "SPJ", "GRN", "TTT"]

        self._cheats: Dict[str, CheatState] = {
            code.upper(): CheatState() for code in codes
        }

    def reset_all(self) -> None:
        for state in self._cheats.values():
            state.progress = 0
            state.active = False

    def is_active(self, code: str) -> bool:
        code = code.upper()
        state = self._cheats.get(code)
        return bool(state and state.active)

    def get_active_codes(self) -> List[str]:
        return [code for code, st in self._cheats.items() if st.active]

    def process_char(self, char: str) -> Tuple[bool, List[Tuple[str, bool]]]:
        """
        Processa UM caracter.

        devolve:
          consumed: se alguma sequência aproveitou a letra
          activations: [(code, active), ...] para códigos que mudaram de estado
        """
        if not char:
            return False, []

        char = char.upper()
        consumed = False
        activations: List[Tuple[str, bool]] = []

        for code, state in self._cheats.items():
            idx = state.progress
            expected = code[idx] if idx < len(code) else None

            if char == expected:
                state.progress += 1
                consumed = True

                if state.progress == len(code):
                    state.active = not state.active
                    state.progress = 0
                    activations.append((code, state.active))
            else:
                state.progress = 1 if char == code[0] else 0

        return consumed, activations
