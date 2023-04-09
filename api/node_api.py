import json
from .node import Type, Modifier

class Node:
    def __init__(self):
        self.pos = {}
        self.modifier = -1
        self.type = 0
        self.aspects = [{}]

    def __str__(self) -> str:
        ret = f"Location: {self.pos['x']}, {self.pos['y']}, {self.pos['z']}\nModifier: {self.modifier}\nType: {self.type}\nAspects:\n"
        for aspect in self.aspects:
            for name, amount in aspect.items():
                ret += f"{name}: {amount}\n"
        return ret


aspects = "aer,alienis,aqua,arbor,auram,bestia,cognitio,corpus,desidia,exanimis,fabrico,fames,gelum,gula,herba," \
          "humanus,ignis,infernus,instrumentum,invidia,ira,iter,limus,lucrum,lux,luxuria,machina,messis,metallum," \
          "meto,mortuus,motus,ordo,pannus,perditio,perfodio,permutatio,potentia,praecantatio,sano,sensus,spiritus," \
          "superbia,telum,tempestas,tenebrae,terra,tutamen,vacuos,venenum,victus,vinculum,vitium,vitreus,volatus"

aspect_map = {aspect: [] for aspect in aspects.split(",")}
modifier_map = {Modifier.name: [] for Modifier in Modifier}
type_map = {Type.name: [] for Type in Type}

file = open("api/nodes.json", "r")
nodes = json.load(file)
file.close()
for node in nodes:
    node_obj = Node()
    node_obj.pos = node["pos"]
    node_obj.modifier = Modifier(node["modifier"]).name
    modifier_map[node_obj.modifier].append(node_obj)
    node_obj.type = Type(node["type"]).name
    type_map[node_obj.type].append(node_obj)
    node_obj.aspects = []
    for aspect in node["aspects"]:
        node_obj.aspects.append({aspect["aspect"]: aspect["max"]})
        aspect_map[aspect["aspect"]].append(node_obj)


def search_nodes(aspects=None, modifier=None, type=None):
    nodes = None
    if aspects:
        aspect_list = aspects.split(",")
        nodes = set(node_aspects(aspect_list))
    if modifier:
        if nodes:
            nodes &= set(node_modifier(modifier))
        else:
            nodes = set(node_modifier(modifier))
    if type:
        if nodes:
            nodes &= set(node_type(type))
        else:
            nodes = set(node_type(type))

    return list(nodes)


def node_aspects(aspects: list[str]):
    nodes = set(aspect_map[aspects[0]])
    for aspect in aspects[1:]:
        nodes &= set(aspect_map[aspect])

    return list(nodes)


def node_modifier(modifier: str):
    return modifier_map[modifier.lower()]


def node_type(type: str):
    return type_map[type.lower()]
