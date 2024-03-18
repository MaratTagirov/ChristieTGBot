from dataclasses import dataclass

@dataclass
class Player:
    turn: str
    user_turnes: list[tuple[int, ...]]