class UnicornException(Exception):
    def __init__(self, message: str, code: int = 404):
        self.message = message
        self.code = code


class AlgorithmCheckException(Exception):
    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code


class AlgorithmProcessException(Exception):
    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
