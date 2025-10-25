import yaml
import random

class DialogNode:
    def __init__(self, node_id, data):
        self.id = node_id
        self.text = data.get("text", "")
        self.options = data.get("options", [])
        self.event = data.get("event")
        self.next = data.get("next")

class Dialog:
    def __init__(self, npc: str, start: str, nodes: dict):
        self.npc = npc
        self.start = start
        self.nodes = nodes

    @classmethod
    def from_yaml(cls, path: str):
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        nodes = {nid: DialogNode(nid, nd) for nid, nd in data["nodes"].items()}
        return cls(npc=data["npc"], start=data["start"], nodes=nodes)

    def run(self, player):
        current = self.nodes[self.start]
        while True:
            print(f"\n[{self.npc}] {current.text}")

            # Trigger event if any
            if current.event:
                print(f"** Event triggered: {current.event} **")

            # Handle terminal node
            if not current.options and not current.next:
                print("\n[End of dialog]")
                break

            # If automatic next node
            if current.next and not current.options:
                current = self.nodes.get(current.next)
                continue

            # Show options
            for i, opt in enumerate(current.options):
                print(f"  {i+1}. {opt['text']}")

            # Get user choice
            try:
                choice = int(input("\nYour choice: ")) - 1
            except ValueError:
                print("Invalid choice.")
                continue

            if choice < 0 or choice >= len(current.options):
                print("Invalid choice.")
                continue

            option = current.options[choice]

            # Handle rolls
            if "roll" in option:
                roll_attr = option["roll"]
                roll_value = random.randint(1, 20) + player.attributes.get(roll_attr, 0)
                print(f"You roll {roll_value} ({roll_attr})!")
                if roll_value >= 12:
                    next_id = option.get("success")
                else:
                    next_id = option.get("failure")
            else:
                next_id = option.get("next")

            if not next_id or next_id == "end":
                print("\n[End of dialog]")
                break

            current = self.nodes.get(next_id)
