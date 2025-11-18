import pygame
from settings import *
from settings import RARITY_COLORS

#spell_slots = {}

class InventoryWindow:
    def __init__(self, game):
        self.game = game
        self.width = 350
        self.height = 280
        self.bg_color = (40, 40, 40)
        self.border_color = (200, 200, 200)
        self.text_color = (255, 255, 255)
        self.font = pygame.font.Font(None, 22)

        self.item_rects = []

        self.panel_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        bg_with_alpha = (*self.bg_color, 180)
        pygame.draw.rect(self.panel_surface, bg_with_alpha, (0, 0, self.width, self.height))
        pygame.draw.rect(self.panel_surface, self.border_color, (0, 0, self.width, self.height), 2)

        self.render_cache = None
        self.cached_inventory = None
        self.cached_items = {}

    def rebuild_item_list(self):
        #create a surface for the inventory content (not panel)
        content = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        offset_x = 0
        x = 0
        y = 0

        title = self.font.render("Inventory", True, self.text_color)
        content.blit(title, (10, 10))

        gold_text = self.font.render(f"Gold: {self.game.player.gold}", True, (255, 215, 0))
        content.blit(gold_text, (self.width - gold_text.get_width() - 20, 10))

        self.item_rects = []
        y_offset = 40

        self.cached_items = { entry["id"]: self.game.items.get(entry["id"])
                          for entry in self.game.player.inventory }
        
        for entry in self.game.player.inventory:
            item = self.cached_items[entry["id"]]

            rect = pygame.Rect(10, y_offset, self.width - 20, 28)

            pygame.draw.rect(content, (60, 60, 60), rect)
            pygame.draw.rect(content, (120, 120, 120), rect, 1)

            if item.icon_small:
                content.blit(item.icon_small, (rect.x + 5, rect.y + 2))
                text_x = rect.x + 34
            else:
                text_x = rect.x + 5

            content.blit(item.name_surface, (text_x, rect.y + 5))

            if item.stackable:
                qty = entry["qty"]

                rarity_color = RARITY_COLORS.get(item.rarity, (255, 255, 255))
                
                if qty not in item.qty_surfaces:
                    item.qty_surfaces[qty] = self.font.render(f"x{qty}", True, rarity_color)

                qty_surf = item.qty_surfaces[qty]                             
                content.blit(qty_surf, (text_x + item.name_surface.get_width() + 5, rect.y + 5))

            self.item_rects.append((rect, entry))
            y_offset += 32

        close_text = self.font.render("Click outside to close", True, (160, 160, 160))
        content.blit(close_text, (10, self.height - 25))

        self.render_cache = content


    def draw(self, screen):

        # --- SAFETY GUARD ---
        # If render_cache somehow failed to build or was never built,
        # rebuild it so we never try to blit a None surface.
        if self.render_cache is None:
            self.rebuild_item_list()
        # ---------------------

        offset_x = 150
        x = SCREEN_WIDTH // 2 - self.width // 2 + offset_x
        y = SCREEN_HEIGHT // 2 - self.height // 2

        screen.blit(self.panel_surface, (x, y))

        if self.cached_inventory is None or self.cached_inventory != self.game.player.inventory:
            self.cached_inventory = [entry.copy() for entry in self.game.player.inventory]
            self.rebuild_item_list()

        screen.blit(self.render_cache, (x, y))

        mouse_pos = pygame.mouse.get_pos()
        for rect, entry in self.item_rects:
            if rect.move(x, y).collidepoint(mouse_pos):
                item = self.cached_items[entry["id"]]
                self.draw_tooltip(screen, item, mouse_pos)
                break

    def draw_tooltip(self, screen, item, mouse_pos):
        

        if not hasattr(item, "tooltip_surfaces"):
            return

        padding = 6
        x, y = mouse_pos
        x += 16
        y += 16

        width = item.tooltip_width + padding * 2
        height = item.tooltip_height + padding * 2

        if x + width > SCREEN_WIDTH:
            x = SCREEN_WIDTH - width - 5
        if y + height > SCREEN_HEIGHT:
            y = SCREEN_HEIGHT - height - 5      

        pygame.draw.rect(screen, (20, 20, 20), (x, y, width + padding * 2, height + padding * 2))
        pygame.draw.rect(screen, (180, 180, 180), (x, y, width + padding * 2, height + padding * 2), 1)

        rarity_color = RARITY_COLORS.get(item.rarity, (255, 255, 255)) #fallback

        name_surf = self.font.render(item.name, True, rarity_color)
        screen.blit(name_surf, (x + padding, y + padding))
        
        ry = y + padding + name_surf.get_height()

        for surf in item.tooltip_surfaces[1:]:
            screen.blit(surf, (x + padding, ry))
            ry += surf.get_height()

    def click(self, pos, button):
        offset_x = SCREEN_WIDTH // 2 - self.width // 2 + 150
        offset_y = SCREEN_HEIGHT //2 - self.height // 2

        for rect, entry in self.item_rects:
            adjusted_rect = rect.move(offset_x, offset_y)
                
            if adjusted_rect.collidepoint(pos):
                item_id = entry["id"]
                item = self.game.items.get(item_id)

                # ----------------------------------------------
                # RIGHT-CLICK → Equip OR Use
                # ----------------------------------------------
                if button == 3:

                    #consumable use
                    if item.type == "consumable":
                        self.game.player.use_item(item_id, self.game.items)
                        print(f"[ITEM] Used {item.name}")
                        return True
                    
                    #equipment equipping
                    if item.type in ("Armor", "Weapon"):
                        equipped = self.game.player.equip_item(item)

                        if equipped:
                            print(f"[EQUIP] Equipped {item.name}")

                            #inventory has changed → rebuild the cache
                            self.render_cache = None
                            self.cached_inventory = None
                            return True
                # ----------------------------------------------
                # LEFT-CLICK → nothing for now (keeps UI open)
                # ----------------------------------------------
                if button == 1:
                    return True  # prevents closing inventory

                    
        return False


    def click_outside(self, pos):
        x = SCREEN_WIDTH // 2 - self.width // 2
        y = SCREEN_HEIGHT // 2 - self.height // 2
        rect = pygame.Rect(x, y, self.width, self.height)
        return not rect.collidepoint(pos)
    
class VendorWindow:
    def __init__(self, game):
        self.game = game
        self.width = 400
        self.height = 360
        self.bg_color = (35, 35, 45)
        self.border_color = (200, 200, 200)
        self.text_color = (255, 255, 255)
        self.font = pygame.font.Font(None, 24)
        self.item_rects = []
        self.scroll_offset = 0
        self.max_scroll = 0
        self.scroll_speed = 20
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT // 2 - self.height // 2

        self.items_for_sale = [
            {"id": "health_potion_small", "price": 10},
            {"id": "mana_potion_small", "price": 12},
            #{"id": "vial_of_water", "price": 5},
            {"id": "Auto Attack", "price": 5},

            # ----- Training Equipment -----
            {"id": "basic_training_helmet", "price": 1},
            {"id": "basic_training_shirt", "price": 1},
            {"id": "basic_training_pants", "price": 1},
            {"id": "basic_training_boots", "price": 1},
            {"id": "basic_training_shield", "price": 1},
            {"id": "basic_training_axe", "price": 1},
            {"id": "basic_training_sword", "price": 1}
        ]

        self.panel_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(self.panel_surface, self.bg_color, (0, 0, self.width, self.height))
        pygame.draw.rect(self.panel_surface, self.border_color, (0, 0, self.width, self.height), 2)

        self.cached_item_data = {}

    def _ensure_item_cached(self, item_id, price):
        #build per item surfaces once
        if item_id in self.cached_item_data:
            return self.cached_item_data[item_id]
        
        item = self.game.items.get(item_id)

        if item and hasattr(item, "rarity"):
            rarity_color = RARITY_COLORS.get(item.rarity, (255, 255, 255))
            name_text = item.name
        else:
            rarity_color = (255, 255, 255)
            name_text = item_id
        
        name_surface = self.font.render(name_text, True, rarity_color)
        price_surface = self.font.render(f"{price}g", True, (255, 220, 100))

        entry = {
            "item": item,
            "id": item_id,
            "price": price,
            "name_surface": name_surface,
            "price_surface": price_surface,
            "icon_small": getattr(item, "icon_small", None)
        }

        self.cached_item_data[item_id] = entry
        return entry

    def draw(self, screen):
        #self.x = SCREEN_WIDTH // 2 - self.width // 2
        #self.y = SCREEN_HEIGHT // 2 - self.height // 2

        # Rebuild panel surface if size changed
        if self.panel_surface.get_width() != self.width or self.panel_surface.get_height() != self.height:
            self.panel_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.rect(self.panel_surface, self.bg_color, (0, 0, self.width, self.height))
            pygame.draw.rect(self.panel_surface, self.border_color, (0, 0, self.width, self.height), 2)


        content_area = pygame.Rect(self.x, self.y, self.width, self.height)
        screen.set_clip(content_area)

        screen.blit(self.panel_surface, (self.x, self.y))

        title = self.font.render("Vendor", True, self.text_color)
        screen.blit(title, (self.x + 10, self.y + 10))


        total_gold = self.game.player.get_total_gold()
        gold_text = self.font.render(f"Gold: {total_gold}", True, (255, 220, 100))
        screen.blit(gold_text, (self.x + self.width - 140, self.y+ 10))

        entry_height = 38
        self.item_rects.clear()

        visible_top = 50
        visible_bottom = self.height - 40

        #panel_top = self.y + 40
        #panel_bottom = self.y + self.height - 40

        y_offset = visible_top - self.scroll_offset

        total_height = len(self.items_for_sale) * entry_height
                
        for entry in self.items_for_sale:
            item_id = entry["id"]
            price = entry["price"]

            cached = self._ensure_item_cached(item_id, price)
            
            item_top = y_offset
            item_bottom = y_offset + entry_height

            #skip items above the window
            if item_bottom < visible_top:
                y_offset += entry_height
                continue

            #stop drawing if below window
            if item_top > visible_bottom:
                break

            #draw visible entry
            ITEM_RIGHT_PADDING = 32
            rect = pygame.Rect(
                self.x + 10,
                self.y + y_offset,
                self.width - ITEM_RIGHT_PADDING,
                entry_height - 8
            )
            
            #rect = pygame.Rect(x + 10, y + y_offset, self.width - 20, 30)
            pygame.draw.rect(screen, (60, 60, 60), rect)
            pygame.draw.rect(screen, (100, 100, 100), rect, 1)

            if cached["icon_small"]:
                screen.blit(cached["icon_small"], (rect.x + 5, rect.y + 5))
                text_x = rect.x + 36
            else:
                text_x = rect.x + 8

            screen.blit(cached["name_surface"], (text_x, rect.y + 5))

            price_x = rect.right - cached["price_surface"].get_width() - 10
            screen.blit(cached["price_surface"], (price_x, rect.y + 5))

            self.item_rects.append((rect, cached))
            
            y_offset += entry_height

        self.max_scroll = max(0, total_height - (visible_bottom - visible_top))

        mouse_pos = pygame.mouse.get_pos()

        for rect, cached in self.item_rects:
            if rect.collidepoint(mouse_pos):
                item = cached["item"]
                if item:
                    self.draw_tooltip(screen, item, mouse_pos)
                break

        # Close text
        close_text = self.font.render("Click outside to close", True, (160, 160, 160))
        screen.blit(close_text, (self.x + 10, self.y + self.height - 25))

        if self.max_scroll > 0:
            #scrollbar track area (inside the panel)
            track_x = self.x + self.width - 14
            track_y = self.y + 40
            track_height = self.height - 80
            track_rect = pygame.Rect(track_x, track_y, 8, track_height)

            pygame.draw.rect(screen, (50, 50, 50), track_rect)

            #thumb size based on visible portion
            visible_height = self.height - 60
            thumb_height = max(20, int((visible_height / total_height) * track_height))

            #thumb position based on scroll offset
            if self.max_scroll > 0:
                scroll_ratio = self.scroll_offset / self.max_scroll
            else:
                scroll_ratio = 0

            thumb_y = track_y + int(scroll_ratio * (track_height - thumb_height))
            thumb_rect = pygame.Rect(track_x, thumb_y, 8, thumb_height)

            pygame.draw.rect(screen, (160, 160, 160), thumb_rect)

        screen.set_clip(None)

    def draw_tooltip(self, screen, item, mouse_pos):
        if not hasattr(item, "tooltip_surfaces"):
            return

        padding = 6
        x, y = mouse_pos
        x += 16
        y += 16

        width = item.tooltip_width + padding * 2
        height = item.tooltip_height + padding * 2

        if x + width > SCREEN_WIDTH:
            x = SCREEN_WIDTH - width - 5
        if y + height > SCREEN_HEIGHT:
            y = SCREEN_HEIGHT - height - 5      

        pygame.draw.rect(screen, (20, 20, 20), (x, y, width + padding * 2, height + padding * 2))
        pygame.draw.rect(screen, (180, 180, 180), (x, y, width + padding * 2, height + padding * 2), 1)

        rarity_color = RARITY_COLORS.get(item.rarity, (255, 255, 255))

        name_surf = self.font.render(item.name, True, rarity_color)
        screen.blit(name_surf, (x + padding, y + padding))

        ry = y + padding + name_surf.get_height()

        for surf in item.tooltip_surfaces[1:]:
            screen.blit(surf, (x + padding, ry))
            ry += surf.get_height()

    def handle_click(self, pos):
        for rect, cached in self.item_rects:
            if rect.collidepoint(pos):                
                
                price = cached["price"]
                item_id = cached["id"]
                
                if self.game.player.get_total_gold() < price:
                    print("[VENDOR] Not enough gold!")
                    return True
                
                self.game.player.spend_gold(price)

                if item_id.lower() == "auto attack":
                    if not self.game.player.auto_combat_unlocked:
                        self.game.player.auto_combat_unlocked = True
                        print("[VENDOR] Auto Combat unlocked!")
                    else:
                        print("[VENDOR] Auto Combat already unlocked.")
                    return True
                
                self.game.player.add_item(item_id, 1)
                print(f"[VENDOR] Purchased {item_id} for {price} gold.")
                return True
        return False
    
    def is_click_outside(self, pos):
        x = SCREEN_WIDTH // 2 - self.width // 2
        y = SCREEN_HEIGHT // 2 - self.height // 2
        rect = pygame.Rect(x, y, self.width, self.height)
        return not rect.collidepoint(pos)
    
class SpellbookWindow:
    def __init__(self, player, spellbook, on_assign_callback):
        self.player = player
        self.spellbook = spellbook
        self.on_assign_callback = on_assign_callback
        self.visible = False

        self.width = 360
        self.height = 300
        self.x = 220
        self.y = 150
        self.bg_color = (20, 20, 20)
        self.border_color = (100, 100, 100)

        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 30)

        self.selected_slot = None
    

    def toggle(self, slot_index = None):
        was_visible = self.visible
        self.visible = not self.visible
        #self.selected_slot = slot_index if self.visible else None
        
        if self.visible and slot_index is not None:
            self.selected_slot = slot_index
        else:
            self.selected_slot = None
        
        print(f"📖 Spellbook {'opened' if self.visible else 'closed'} (slot={slot_index})")
        
        if not self.visible and hasattr(self.player.game, "selected_spell_slot"):
            self.player.game.selected_spell_slot = None

    def draw(self, surface):
        if not self.visible:
            return
        
        panel = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.bg_color, panel)
        pygame.draw.rect(surface, self.border_color, panel, 2)

        title = self.title_font.render("Spellbook", True, (255, 255, 255))
        surface.blit(title, (self.x + 10, self.y + 10))

        start_y = self.y + 50

        for i, spell in enumerate(self.spellbook):
            text = f"{spell.name}"
            color = (200, 200, 255)
            surf = self.font.render(text, True, color)
            rect = surf.get_rect(topleft = (self.x + 20, start_y + i * 32))
            surface.blit(surf, rect)

            pygame.draw.rect(surface, (60, 60, 60), rect.inflate(8, 4), 1)
            spell.click_rect = rect.inflate(8, 4)

        mouse_pos = pygame.mouse.get_pos()
        for spell in self.spellbook:
            if hasattr(spell, "click_rect") and spell.click_rect.collidepoint(mouse_pos):
                self.draw_spell_tooltip(surface, spell, mouse_pos)
                break

    def handle_click(self, pos):
        if not self.visible:
            return False
        
        for i, spell in enumerate(self.spellbook):
            if hasattr(spell, "click_rect") and spell.click_rect.collidepoint(pos):
                if self.selected_slot is None:
                    print(f"[INFO] Clicked {spell.name}, but no slot is selected.")
                    return True   
                
                print(f"🪄 Selected {spell.name} for Slot {self.selected_slot}")
                if self.on_assign_callback:
                    self.on_assign_callback(self.selected_slot, spell)
                             
                self.toggle(None)
                return True
        return False
    
    def draw_spell_tooltip(self, surface, spell, mouse_pos):
        #print(f"[UI DEBUG] Tooltip surface id={id(surface)}")
        equipped_slot = None
        #find which slot spell is assigned to (if any)
        if hasattr(self.player.game, "spell_slots"):
            for slot, s in self.player.game.spell_slots.items():
                if s.name == spell.name:
                    equipped_slot = slot
                    break
        lines = [
            f"{spell.name}",
            f"MP Cost: {spell.mana_cost}",
            f"Cooldown: {spell.cooldown // 1000}s",
            f"Damage: {getattr(spell, 'power', '?')}",
        ]
        if equipped_slot:
            lines.append(f"Equipped to Slot {equipped_slot}")
        else:
            lines.append("Not equipped")

        font = pygame.font.Font(None, 22)
        padding = 8
        width = max(font.size(line)[0] for line in lines) + padding * 2
        height = len(lines) * 22 + padding * 2
        x, y = mouse_pos
        
        screen_w, screen_h = surface.get_size()
        x = min(x, screen_w - width - 15)
        y = min(y, screen_h - height - 15)
        rect = pygame.Rect(x + 15, y+ 15, width, height)

        pygame.draw.rect(surface, (30, 30, 30), rect)
        pygame.draw.rect(surface, (150, 150, 150), rect, 2)

        for i, line in enumerate(lines):
            surf = font.render(line, True, (255, 255, 255))
            surface.blit(surf, (rect.x + padding, rect.y + padding + i * 22))

class CharacterWindow:
    def __init__(self, game):
        self.game = game
        self.visible = False

        self.width = 300
        self.height = 665
        
        self.x = 50
        self.y = 50

        self.font = pygame.font.Font(None, 26)
        self.small_font = pygame.font.Font(None, 22)

        self.equip_rects = {} # slot_name → rect

    def toggle(self):
        self.visible = not self.visible

    def draw(self, surface):
        if not self.visible:
            return
        
        pygame.draw.rect(surface, (25, 25, 25), (self.x, self.y, self.width, self.height), border_radius = 8)
        pygame.draw.rect(surface, (150, 150, 150), (self.x, self.y, self.width, self.height), width = 2, border_radius = 8)

        title = self.font.render("Character Stats", True, (255, 255, 200))
        surface.blit(title, (self.x + 20, self.y + 15))

        player = self.game.player
        stats = player.stats

        min_dmg, max_dmg = stats.get_damage_range()

        lines = [
            f"Damage: {min_dmg} - {max_dmg}",
            f"STR: {stats.strength}",
            f"DEX: {stats.dexterity}",
            f"CON: {stats.constitution}",
            f"INT: {stats.intelligence}",
            "",
            f"Crit: {stats.crit_chance*100:.2f}%",
            f"Dodge: {stats.dodge_chance*100:.2f}%",
            f"Armor: {stats.armor}",
            f"Atk Speed: {stats.attack_speed:.2f}",
        ]

        y_offset = 55
        for line in lines:
            text_surf = self.small_font.render(line, True, (255, 255, 255))
            surface.blit(text_surf, (self.x + 20, self.y + y_offset))
            y_offset += 28

        # ------------------------------
        # Equipped Gear Header
        # ------------------------------
        y_offset += 10
        eq_header = self.small_font.render("Equipped Gear:", True, (255, 255, 200))
        surface.blit(eq_header, (self.x + 20, self.y + y_offset))
        y_offset += 30

        self.equip_rects.clear()

        slot_labels = {
            "head": "Helmet",
            "neck": "Necklace",
            "back": "Cape",
            "chest": "Chest",
            "legs": "Legs",
            "feet": "Boots",
            "weapon": "Weapon",
            "offhand": "Offhand",
            "ring1": "Ring 1",
            "ring2": "Ring 2"
        }

        #player = self.game.player
        items = player.equipment

        for slot, label in slot_labels.items():
            item = items.get(slot)

            #slot label
            slot_text = self.small_font.render(f"{label}:", True, (200, 200, 200))
            surface.blit(slot_text, (self.x + 20, self.y + y_offset))

            local_x = 126
            local_y = y_offset - 4

            #clickable background box
            box_rect = pygame.Rect(self.x + local_x, self.y + local_y, 165, 24)
            pygame.draw.rect(surface, (45, 45, 45), box_rect)
            pygame.draw.rect(surface, (90, 90, 90), box_rect, 1)

            self.equip_rects[slot] = pygame.Rect(local_x, local_y, 165, 24)

            #item or "None"
            if item:
                rarity_color = RARITY_COLORS.get(item.rarity, (255, 255, 255))
                item_text = self.small_font.render(item.name, True, rarity_color)
                surface.blit(item_text, (self.x + 130, self.y + y_offset))

                rect = pygame.Rect(local_x, local_y, item_text.get_width(), item_text.get_height())
                self.equip_rects[slot] = rect
            else:
                none_text = self.small_font.render("None", True, (120, 120, 120))
                surface.blit(none_text, (self.x + 130, self.y + y_offset))

            y_offset += 28

        mouse_x, mouse_y = pygame.mouse.get_pos()

        for slot, rect in self.equip_rects.items():
            #convert rect into absolute screen space
            abs_rect = rect.move(self.x, self.y)

            if abs_rect.collidepoint((mouse_x, mouse_y)):
                item = self.game.player.equipment.get(slot)
                if item:
                    self.draw_equipped_tooltip(surface, item, (mouse_x, mouse_y))
                    break

    def draw_equipped_tooltip(self, surface, item, mouse_pos):
        if not hasattr(item, "tooltip_surfaces"):
            return

        padding = 6
        x, y = mouse_pos
        x += 16
        y += 16

        width = item.tooltip_width + padding * 2
        height = item.tooltip_height + padding * 2

        #screen boundary checks
        if x + width > SCREEN_WIDTH:
            x = SCREEN_WIDTH - width - 5
        if y + height > SCREEN_HEIGHT:
            y = SCREEN_HEIGHT - height - 5

        #Background
        pygame.draw.rect(surface, (20, 20, 20), (x, y, width, height))
        pygame.draw.rect(surface, (180, 180, 180), (x, y, width, height), 1)

        #Name
        rarity_color = RARITY_COLORS.get(item.rarity, (255, 255, 255))
        name_surf = self.small_font.render(item.name, True, rarity_color)
        surface.blit(name_surf, (x + padding, y + padding))

        #other tooltip lines
        yy = y + padding + name_surf.get_height()
        for surf in item.tooltip_surfaces[1:]:
            surface.blit(surf, (x + padding, yy))
            yy += surf.get_height()


    def handle_click(self, pos):
        mouse_x, mouse_y = pos

        for slot, rect in self.equip_rects.items():
            # Convert local rect → absolute screen rect
            abs_rect = rect.move(self.x, self.y)

            if abs_rect.collidepoint(mouse_x, mouse_y):
                item = self.game.player.equipment.get(slot)
                if item:
                    print(f"[UNEQUIP] {item.name} removed from {slot}.")
                    self.game.player.unequip_slot(slot)

                    #refresh ui
                    self.equip_rects = {}
                    return True
        return False                  
        
class LevelUpWindow:
    def __init__(self, game):
        self.game = game
        self.visible = False

        self.width = 360
        self.height = 300
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT // 2 - self.height // 2

        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 24)

        self.buttons = []

    def open(self):
        self.visible = True

    def close(self):
        self.visible = False
    
    def draw(self, screen):
        if not self.visible:
            return

        panel = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (30, 30, 30, 230), (0, 0, self.width, self.height))
        pygame.draw.rect(panel, (200, 200, 200), (0, 0, self.width, self.height), 2)

        screen.blit(panel, (self.x, self.y))

        title = self.font.render("Level Up!", True, (255, 255, 255))
        screen.blit(title, (self.x + 110, self.y + 10))

        p = self.game.player

        pts_text = self.font.render(f"Points: {p.stat_points}", True, (255, 255, 100))
        screen.blit(pts_text, (self.x + 20, self.y + 50))

        labels = [
            ("Strength",      "strength"),
            ("Dexterity",     "dexterity"),
            ("Constitution",  "constitution"),
            ("Intelligence",  "intelligence"),
        ]

        self.buttons.clear()
        start_y = self.y + 100

        for label, attr in labels:
            val = getattr(p.stats, attr)

            text = self.small_font.render(f"{label}: {val}", True, (255, 255, 255))
            screen.blit(text, (self.x + 20, start_y))

            plus_rect = pygame.Rect(self.x + 260, start_y - 5, 30, 30)
            pygame.draw.rect(screen, (80, 80, 80), plus_rect)
            pygame.draw.rect(screen, (160, 160, 160), plus_rect, 2)

            plus_text = self.small_font.render("+", True, (255, 255, 255))
            screen.blit(plus_text, (plus_rect.x + 8, plus_rect.y + 4))

            self.buttons.append((plus_rect, attr))

            start_y += 40

        if p.stat_points == 0:
            confirm_rect = pygame.Rect(self.x + 90, self.y + 250, 180, 30)
            pygame.draw.rect(screen, (50, 120, 50), confirm_rect)
            pygame.draw.rect(screen, (200, 200, 200), confirm_rect, 2)
            confirm_text = self.small_font.render("Confirm", True, (255, 255, 255))
            screen.blit(confirm_text, (confirm_rect.x + 50, confirm_rect.y + 5))

            self.buttons.append((confirm_rect, "confirm"))

    def handle_click(self, pos):
        p = self.game.player

        for rect, action in self.buttons:
            if rect.collidepoint(pos):

                if action == "confirm":
                    p.stats.recalc_stats()
                    self.close()
                    return
                
                if p.stat_points > 0:
                    setattr(p.stats, action, getattr(p.stats, action) + 1)
                    p.stat_points -= 1
                    return