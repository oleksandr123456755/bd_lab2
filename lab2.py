splits = 0
parent_splits = 0
fusions = 0
parent_fusions = 0


class Node(object):

    def __init__(self, parent=None):
        self.keys: list = []
        self.values: list[Node] = []
        self.parent: Node = parent

    def index(self, key):
        for i, item in enumerate(self.keys):
            if key < item:
                return i

        return len(self.keys)

    def __getitem__(self, item):
        return self.values[self.index(item)]

    def __setitem__(self, key, value):
        i = self.index(key)
        self.keys[i:i] = [key]
        self.values.pop(i)
        self.values[i:i] = value

    def split(self):
        global splits, parent_splits
        splits += 1
        parent_splits += 1

        left = Node(self.parent)

        mid = len(self.keys) // 2

        left.keys = self.keys[:mid]
        left.values = self.values[:mid + 1]
        for child in left.values:
            child.parent = left

        key = self.keys[mid]
        self.keys = self.keys[mid + 1:]
        self.values = self.values[mid + 1:]

        return key, [left, self]

    def __delitem__(self, key):
        i = self.index(key)
        del self.values[i]
        if i < len(self.keys):
            del self.keys[i]
        else:
            del self.keys[i - 1]

    def fusion(self):
        global fusions, parent_fusions
        fusions += 1
        parent_fusions += 1

        index = self.parent.index(self.keys[0])
        if index < len(self.parent.keys):
            next_node: Node = self.parent.values[index + 1]
            next_node.keys[0:0] = self.keys + [self.parent.keys[index]]
            for child in self.values:
                child.parent = next_node
            next_node.values[0:0] = self.values
        else:
            prev: Node = self.parent.values[-2]
            prev.keys += [self.parent.keys[-1]] + self.keys
            for child in self.values:
                child.parent = prev
            prev.values += self.values

    def borrow_key(self, minimum: int):
        index = self.parent.index(self.keys[0])
        if index < len(self.parent.keys):
            next_node: Node = self.parent.values[index + 1]
            if len(next_node.keys) > minimum:
                self.keys += [self.parent.keys[index]]

                borrow_node = next_node.values.pop(0)
                borrow_node.parent = self
                self.values += [borrow_node]
                self.parent.keys[index] = next_node.keys.pop(0)
                return True
        elif index != 0:
            prev: Node = self.parent.values[index - 1]
            if len(prev.keys) > minimum:
                self.keys[0:0] = [self.parent.keys[index - 1]]

                borrow_node = prev.values.pop()
                borrow_node.parent = self
                self.values[0:0] = [borrow_node]
                self.parent.keys[index - 1] = prev.keys.pop()
                return True

        return False


class Leaf(Node):
    def __init__(self, parent=None, prev_node=None, next_node=None):
        super(Leaf, self).__init__(parent)
        self.next: Leaf = next_node
        if next_node is not None:
            next_node.prev = self
        self.prev: Leaf = prev_node
        if prev_node is not None:
            prev_node.next = self

    def __getitem__(self, item):
        return self.values[self.keys.index(item)]

    def __setitem__(self, key, value):
        i = self.index(key)
        if key not in self.keys:
            self.keys[i:i] = [key]
            self.values[i:i] = [value]
        else:
            self.values[i - 1] = value

    def split(self):
        global splits
        splits += 1

        left = Leaf(self.parent, self.prev, self)
        mid = len(self.keys) // 2

        left.keys = self.keys[:mid]
        left.values = self.values[:mid]

        self.keys: list = self.keys[mid:]
        self.values: list = self.values[mid:]

        return self.keys[0], [left, self]

    def __delitem__(self, key):
        i = self.keys.index(key)
        del self.keys[i]
        del self.values[i]

    def fusion(self):
        global fusions
        fusions += 1

        if self.next is not None and self.next.parent == self.parent:
            self.next.keys[0:0] = self.keys
            self.next.values[0:0] = self.values
        else:
            self.prev.keys += self.keys
            self.prev.values += self.values

        if self.next is not None:
            self.next.prev = self.prev
        if self.prev is not None:
            self.prev.next = self.next

    def borrow_key(self, minimum: int):
        index = self.parent.index(self.keys[0])
        if index < len(self.parent.keys) and len(self.next.keys) > minimum:
            self.keys += [self.next.keys.pop(0)]
            self.values += [self.next.values.pop(0)]
            self.parent.keys[index] = self.next.keys[0]
            return True
        elif index != 0 and len(self.prev.keys) > minimum:
            self.keys[0:0] = [self.prev.keys.pop()]
            self.values[0:0] = [self.prev.values.pop()]
            self.parent.keys[index - 1] = self.keys[0]
            return True

        return False


class BPlusTree(object):
    root: Node

    def __init__(self, maximum=4):
        self.root = Leaf()
        self.maximum: int = maximum if maximum > 2 else 2
        self.minimum: int = 2
        self.depth = 0

    def find(self, key) -> Leaf:
        node = self.root

        while type(node) is not Leaf:
            node = node[key]
        return node

    def __getitem__(self, item):
        return self.find(item)[item]

    def query(self, key):
        leaf = self.find(key)
        return leaf[key] if key in leaf.keys else None

    def __setitem__(self, key, value, leaf=None):
        if leaf is None:
            leaf = self.find(key)
        leaf[key] = value
        if len(leaf.keys) > self.maximum:
            self.insert_index(*leaf.split())

    def insert_index(self, key, values: list[Node]):
        parent = values[1].parent
        if parent is None:
            values[0].parent = values[1].parent = self.root = Node()
            self.depth += 1
            self.root.keys = [key]
            self.root.values = values
            return

        parent[key] = values
        if len(parent.keys) > self.maximum:
            self.insert_index(*parent.split())


    def delete(self, key, node: Node = None):
        if node is None:
            node = self.find(key)
        del node[key]

        if len(node.keys) < self.minimum:
            if node == self.root:
                if len(self.root.keys) == 0 and len(self.root.values) > 0:
                    self.root = self.root.values[0]
                    self.root.parent = None
                    self.depth -= 1
                return

            elif not node.borrow_key(self.minimum):
                node.fusion()
                self.delete(key, node.parent)


    def show(self, node=None, file=None, _prefix="", _last=True):
        if node is None:
            node = self.root
        values = [self.query(key) for key in node.keys if self.query(key) is not None]
        print(_prefix, "|- " if _last else "|- ", values, sep="", file=file)
        _prefix += "   " if _last else "|  "

        if type(node) is Node:
            for i, child in enumerate(node.values):
                _last = (i == len(node.values) - 1)
                self.show(child, file, _prefix, _last)



    def leftmost_leaf(self) -> Leaf:
        node = self.root
        while type(node) is not Leaf:
            node = node.values[0]
        return node

    def query_more_than(self, key):
        results = []
        node = self.root
        while not isinstance(node, Leaf):
            found = False
            for i, node_key in enumerate(node.keys):
                if key < node_key:
                    node = node.values[i]
                    found = True
                    break
            if not found:
                node = node.values[-1]

        while node:
            for k, v in zip(node.keys, node.values):
                if k > key:
                    results.append(v)
            node = node.next
        return results


    def query_less_than(self, key):
      results = []
      leaf = self.leftmost_leaf()
      while leaf:
          for k in leaf.keys:
              if k < key:
                  results.append(leaf[k])
              else:
                  return results
          leaf = leaf.next
      return results


def get_name_hash(word, max_length=15):
    word = word.lower()

    groups = [
        "аб", "вгґд", "еєжзиі", "їйклмн", "опр", "сту", "фхцч", "шщью", "я"
    ]
    letter_to_number = {}
    for idx, group in enumerate(groups):
        for letter in group:
            letter_to_number[letter] = str(idx + 1)

    encoded = ''.join([letter_to_number.get(char, '0') for char in word])

    length_code = str(len(word)).zfill(2)

    padding_length = max_length - len(encoded) - len(length_code)
    if padding_length > 0:
        full_encoded = encoded + '0' * padding_length + length_code
    else:
        full_encoded = encoded[:max_length - len(length_code)] + length_code

    return int(full_encoded)

max_name_len = 15

ukrainian_names = [
    "Мельник", "Шевченко", "Бойко", "Коваленко", "Бондаренко", "Ткаченко", "Ковальчук",
    "Кравченко", "Олійник", "Ігнатьєв", "Шевчук", "Поліщук", "Лисенко", "Ткачук", "Коваль", "Савченко",
    "Марченко", "Литвиненко", "Гончаренко", "Андрієнко", "Петренко"
]

bplustree = BPlusTree(4)
for name in ukrainian_names:
  bplustree[get_name_hash(name)] = name
bplustree.show()

bplustree.query(get_name_hash("Гончаренко"))

bplustree.query_less_than(get_name_hash("Гончаренко"))

bplustree.query_more_than(get_name_hash("Ігнатьєв"))

bplustree.query_more_than(get_name_hash("яяяя"))

bplustree.query_less_than(get_name_hash("яяяя"))

bplustree.delete(get_name_hash("Бойко"))
bplustree.show()

