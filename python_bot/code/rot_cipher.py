def rot_alpha(text: str, n: int) -> str:
    result = []
    for c in text:
        if c.isalpha():
            base = ord('A') if c.isupper() else ord('a')
            result.append(chr((ord(c) - base + n) % 26 + base))
        else:
            result.append(c)
    return ''.join(result)

def rot_digit(text: str, n: int) -> str:
    result = []
    for c in text:
        if c.isdigit():
            result.append(chr((ord(c) - ord('0') + n) % 10 + ord('0')))
        else:
            result.append(c)
    return ''.join(result)

def rot_combo(text: str, alpha_n: int, digit_n: int) -> str:
    result = []
    for c in text:
        if c.isalpha():
            base = ord('A') if c.isupper() else ord('a')
            result.append(chr((ord(c) - base + alpha_n) % 26 + base))
        elif c.isdigit():
            result.append(chr((ord(c) - ord('0') + digit_n) % 10 + ord('0')))
        else:
            result.append(c)
    return ''.join(result)
