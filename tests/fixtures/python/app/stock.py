LIMIT = 10
counter = 0


class Item:
    # Its weight, in tonnes.
    weight: float = 0.0

    def heavy(self) -> bool:
        return self.weight > LIMIT


class Crate(Item):
    def fill(self, item: Item) -> None:
        global counter
        counter += 1
        item.weight = 2.0
        item.heavy()
