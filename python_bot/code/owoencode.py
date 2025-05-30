import bitarray

def encode(s):
    ba = bitarray.bitarray()
    ba.frombytes(s.encode())
    g = ''
    o = ''
    s = 0
    for b in ba:
        if s == 0:
            g = ('u' if b else 'o')
            s = 1
            continue
        if s == 1:
            o += (g.upper() if b else g)
            s = 2
            continue
        if s == 2:
            o += ('W' if b else 'w')
            s = 3
            continue
        if s == 3:
            o += (g.upper() if b else g)
            s = 0
            continue
    return o
