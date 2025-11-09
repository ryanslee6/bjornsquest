class Item:
    def __init__(self, item_id, data):
        self.id = item_id
        self.name = data.get("name", item_id)
        self.type = data.get("type", "misc")
        self.description = data.get("description", "")
        self.rarity = data.get("rarity", "common")
        self.stackable = data.get("stackable", True)

    def use(self, player):
        #override in child classes
        print(f"{self.name} has no effect.")

    def tooltip_text(self):
        lines = [
            f"{self.name}",
            f"Type: {self.type.title()}",
        ]
        if self.description:
            lines.append(self.description)
        return lines

class ConsumableItem(Item):
    def __init__(self, item_id, data):
        super().__init__(item_id, data)
        self.heal_amount = data.get("heal_amount", 0)

    def use(self, player):
        #heal player

        if self.heal_amount > 0:
            player.stats.hp = min(player.stats.max_hp, player.stats.hp + self.heal_amount)
            print(f"{player.name} healed for {self.heal_amount} HP!")

            if hasattr(player.game, "player_draw_x"):
                px = player.game.player_draw_x + player.sprite.get_width() // 2
                py = player.game.player_draw_y + player.sprite.get_height() // 2 + 55
            else:    
                px = 200
                py = 240
            
            player.game.combat.spawn_heal_particles(px, py)

            player.game.combat.add_floating_text(
                f"+{self.heal_amount} HP",
                0, 0,
                target= "player",
                text_type = "heal"
            )

    def tooltip_text(self):
        base = super().tooltip_text()
        base.insert(2, f"Heals: {self.heal_amount} HP")
        return base
