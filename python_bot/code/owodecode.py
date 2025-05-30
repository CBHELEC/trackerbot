import bitarray


def decode(s):
    letterMapping = {'u': '1', 'o': '0'}
    ba = bitarray.bitarray()
    encoded = s
    s = 0
    try:
        for c in encoded:
            if s == 0:
                ba.extend(letterMapping[c.lower()])
                ba.extend('1' if c.isupper() else '0')
                s = 1
                continue
            if s == 1:
                ba.extend('1' if c.isupper() else '0')
                s = 2
                continue
            if s == 2:
                ba.extend('1' if c.isupper() else '0')
                s = 0
                continue
        return ba.tobytes().decode()
    except KeyError:
        return "Improper OwO encoded input >:3"
