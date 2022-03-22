from dataclasses import dataclass

@dataclass
class Volunteer():
    id: int
    name: str
    surname: str
    username: str
    position: (float, float)
    skills: str
    chat_id: int
    ukranian: bool
    russian: bool

@dataclass
class Group():
    id: int
    name: str
    platform: str
    language: str