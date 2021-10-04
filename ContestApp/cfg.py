from enum import IntEnum

class UserType(IntEnum):
    PROFESSOR = 1
    STUDENT = 2

server = {
    'name': 'localhost',
    'port': 8080,
}

cli = {
    'exit': 'sair',
    'done': 'pronto', 
}
