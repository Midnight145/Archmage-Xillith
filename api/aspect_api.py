from typing import Union, List

from .Item import Item

# initialization
FILENAME = "api/aspects.csv"
file = open(FILENAME, "r")
headers = next(file).lower().rstrip().split(',')
items = []

for i in file.readlines():
    line = i.rstrip().split(",")
    aspects = {headers[x]: line[x] for x in range(len(headers))}
    items.append(Item(aspects))
file.close()


def search_aspects(mod: str = "", name: str = "", itemid: int = None, metadata: int = None, first: bool = False) -> List[Item]:
    print(locals())
    args = locals()
    del args["first"]
    terms = [term for term in args.keys() if args[term] != "" and args[term] is not None]
    matches = []
    if not terms:
        return matches
    for i in items:
        if all(getattr(i, x) == args[x] for x in terms):
            if first:
                return [i]
            matches.append(i)
    return matches


def search_aspect(*aspects: str) -> List[Item]:
    matches = []
    for i in items:
        if all(i.aspects[x] for x in aspects):
            matches.append(i)
    return matches
