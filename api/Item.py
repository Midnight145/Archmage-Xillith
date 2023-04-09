class Item:
    def __init__(self, args: dict):
        self.mod: str = ""
        self.name: str = ""
        self.itemid: int = 0
        self.metadata: int = 0
        self.aspects: dict[str:int] = {}
        for key, value in args.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                self.aspects[key] = int(value if value else 0)

    def __str__(self) -> str:
        aspect_str = ""
        for key, val in self.aspects.items():
            if val == 0: continue
            aspect_str += f"{key}:{val}, "
        return f"{self.mod}:{self.name}:{self.itemid}:{self.metadata}\n{aspect_str.rstrip().rstrip(',')}\n"
