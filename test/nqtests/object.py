class Dummy:
    _cubictemp_unescaped = 1
    def __repr__(self):
        return "<foo>"

mdict = {
    "object":   Dummy()
}
