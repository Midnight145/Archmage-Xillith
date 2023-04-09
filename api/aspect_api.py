from typing import Union, List

from .Item import Item

# initialization
FILENAME = "api/aspects.csv"
file = open(FILENAME, "r")
headers = next(file).lower().rstrip().split(',')
items = []

for i in file.readlines():
    line = i.rstrip().split(",")  # csv parsing
    aspects = {headers[x]: line[x] for x in range(len(headers))}  # converts csv line to dict, with headers as keys
    items.append(Item(aspects))
file.close()


def search_aspects(mod: str = "", name: str = "", itemid: int = None, metadata: int = None, first: bool = False) -> List[Item]:
    print(locals())
    args = locals()  # get all args
    del args["first"]  # remove first
    terms = [term for term in args.keys() if args[term] != "" and args[term] is not None]  # will find specific item(s) based on args
    matches = []
    if not terms:
        return matches
    for i in items:
        if all(getattr(i, x) == args[x] for x in terms):  # some magic, i dont remember how it works
            if first:
                return [i]  # return first match
            matches.append(i)
    return matches


def search_aspect(*aspects: str) -> List[Item]:
    # takes in a list of aspects, and returns a list of items that have all of them
    matches = []
    for i in items:
        if all(i.aspects[x] for x in aspects):  # if item has all given aspects
            matches.append(i)
    return matches
