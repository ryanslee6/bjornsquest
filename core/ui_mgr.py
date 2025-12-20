import pygame
import os
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

        self.scroll_offset = 0
        self.max_scroll = 0
        self.scroll_speed = 32

        self.item_rects = []

        self.panel_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        bg_with_alpha = (*self.bg_color, 180)
        pygame.draw.rect(self.panel_surface, bg_with_alpha, (0, 0, self.width, self.height))
        pygame.draw.rect(self.panel_surface, self.border_color, (0, 0, self.width, self.height), 2)

        self.render_cache = None
        self.cached_inventory = None
        self.cached_items = {}

        self.needs_rebuild = True

        #drag-and-drop state
        self.dragging_item = None #(rect, entry, cache_key) tuple
        self.drag_start_index = None #original index in inventory
        self.drag_mouse_offset = (0, 0) #offset from mouse to item rect
        self.just_released_drag = False #prevent immediate re-drag

    def mark_dirty(self):
        #call this whenever inventory changes
        self.needs_rebuild = True
        self.render_cache = None
        self.cached_inventory = None

    def rebuild_item_list(self):

        #clear old item_rects
        self.item_rects = []

        #build cache - handle both stackable id and equipment
        self.cached_items = {}
        
        for entry in self.game.player.inventory:
            if "item" in entry:
                #equpment - already an Item object
                item = entry["item"]
                self.cached_items[id(item)] = item #use object ID as key
            else:
                #stackable - use item_id
                item_id = entry["id"]
                self.cached_items[item_id] = self.game.items.get(item_id)

        #build item rectangles (position only, no drawing)
        entry_height = 32
        y_offset = 40

        for entry in self.game.player.inventory:
            #get the item (handle both formats)
            if "item" in entry:
                item = entry["item"]
                cache_key = id(item)
            else:
                item = self.cached_items[entry["id"]]
                cache_key = entry["id"]

            #lock font + build name surface
            if item.name_font is None:
                item.name_font = self.font

            item.rebuild_name_surface(item.name_font)

            rect = pygame.Rect(10, y_offset, self.width - 40, 28)
            self.item_rects.append((rect, entry, cache_key))
            y_offset += entry_height

        #calculate max scroll
        total_height = len(self.game.player.inventory) * entry_height
        visible_height = self.height - 70 #space between header and footer
        self.max_scroll = max(0, total_height - visible_height)

    def _draw_dragged_item(self, screen, mouse_pos):
        #draw the item currently being dragged at the mouse position
        if not self.dragging_item:
            return
        
        rect, entry, cache_key = self.dragging_item
        item = self.cached_items[cache_key]

        #calculate draw position (mouse - offset)
        draw_x = mouse_pos[0] - self.drag_mouse_offset[0]
        draw_y = mouse_pos[1] - self.drag_mouse_offset[1]

        #draw semi-transparent version of the item
        drag_rect = pygame.Rect(draw_x, draw_y, rect.width, rect.height)

        #draw with slight transparency
        drag_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(drag_surface, (60, 60, 60, 200), (0, 0, rect.width, rect.height))
        pygame.draw.rect(drag_surface, (120, 120, 255, 200), (0, 0, rect.width, rect.height), 2)
        
        #Draw icon
        if item.icon_small:
            drag_surface.blit(item.icon_small, (5, 2))
            text_x = 34
        else:
            text_x = 5

        #draw name
        drag_surface.blit(item.name_surface, (text_x, 5))

        #draw quantity if stackable
        if item.stackable:
            qty = entry["qty"]
            rarity_color = RARITY_COLORS.get(item.rarity, (255, 255, 255))
            if qty not in item.qty_surfaces:
                item.qty_surfaces[qty] = self.font.render(f"x{qty}", True, rarity_color)
            qty_surf = item.qty_surfaces[qty]
            drag_surface.blit(qty_surf, (text_x + item.name_surface.get_width() + 5, 5))

        screen.blit(drag_surface, drag_rect)

    def draw(self, screen):
        if self.needs_rebuild:
            self.cached_inventory = [entry.copy() for entry in self.game.player.inventory]
            self.rebuild_item_list()
            self.needs_rebuild = False

        offset_x = 150
        x = SCREEN_WIDTH // 2 - self.width // 2 + offset_x
        y = SCREEN_HEIGHT // 2 - self.height // 2

        #draw panel background
        screen.blit(self.panel_surface, (x, y))

        #draw fixed header (title, bounty points and gold) - not scrolled
        title = self.font.render("Inventory", True, self.text_color)
        screen.blit(title, (x + 10, y + 10))

        #gold text (so bounty points has width)
        gold_text = self.font.render(f"Gold: {self.game.player.gold}", True, (255, 215, 0))

        #bounty points (left of gold)
        if not hasattr(self.game.player, 'bounty_points'):
            self.game.player.bounty_points = 0
        bounty_text = self.font.render(f"Bounty Points: {self.game.player.bounty_points}", True, (200, 100, 255))
        bounty_x = x + self.width - gold_text.get_width() - bounty_text.get_width() - 40
        screen.blit(bounty_text, (bounty_x, y+ 10))

        #draw gold (right of bounty)
        screen.blit(gold_text, (x + self.width - gold_text.get_width() - 20, y + 10))
        
        #set up clipping area for scrollable content
        content_area = pygame.Rect(x, y + 40, self.width - 20, self.height - 70)
        screen.set_clip(content_area)

        #draw scrollable items
        self._draw_scrollable_items(screen, x, y)

        screen.set_clip(None)

        #draw fixed foot (close text) - not scrolled
        close_text = self.font.render("Click outside to close", True, (160, 160, 160))
        screen.blit(close_text, (x + 10, y + self.height - 25))

        #draw scrollbar if needed
        if self.max_scroll > 0:
            self._draw_scrollbar(screen, x, y)

        #handle tooltip
        mouse_pos = pygame.mouse.get_pos()
        for item_rect_data in self.item_rects:
            #handle both old and new format
            if len(item_rect_data) == 3:
                rect, entry, cache_key = item_rect_data
            else:
                #old format - force rebuild
                self.mark_dirty()
                return
            
            #adjust rect for scroll offset
            adjusted_rect = rect.move(x, y - self.scroll_offset)
            
            #only show tooltip if item is visible in the clipped area
            if content_area.colliderect(adjusted_rect) and adjusted_rect.collidepoint(mouse_pos):
                item = self.cached_items[cache_key]
                self.draw_tooltip(screen, item, mouse_pos)
                break

        if self.dragging_item:
            mouse_pos = pygame.mouse.get_pos()
            self._draw_dragged_item(screen, mouse_pos)

    def draw_tooltip(self, screen, item, mouse_pos):        
        if not hasattr(item, "tooltip_surfaces"):
            return

        padding = 6
        x, y = mouse_pos
        x += 16
        y += 16

        #calculate tooltip size
        lines = item.tooltip_text()
        font = self.font

        rendered_lines = []

        # ---------------------------------
        # Normalize ALL tooltip lines
        # ---------------------------------
        for i, line in enumerate(lines):
            #dict-based line (new system)
            if isinstance(line, dict):
                text = line.get("text", "")
                color_key = line.get("color", "normal")

                if color_key == "enhanced":
                    color = (80, 220, 80)
                elif color_key == "warning":
                    color = (255, 100, 100)
                else:
                    color = (255, 255, 255)

            else:
                text = line
                color = (255, 255, 255)

            # ---------------------------------
            # Special handling by CONTENT
            # ---------------------------------
            if text.startswith("Level Required:"):
                req_level = int(text.split(":")[1])
                player_level = self.game.player.level
                color = (100, 255, 100) if player_level >= req_level else (255, 100, 100)
                text = f"Requires Level: {req_level}"

            rendered_lines.append((text, color, i))   

        #calculate width and height
        max_width = 0
        total_height = 0

        for text, color, _ in rendered_lines:
            surf = font.render(text, True, color)
            max_width = max(max_width, surf.get_width())
            total_height += surf.get_height()

        width = max_width + padding * 2
        height = total_height + padding * 2

        if x + width > SCREEN_WIDTH:
            x = SCREEN_WIDTH - width - 5
        if y + height > SCREEN_HEIGHT:
            y = SCREEN_HEIGHT - height - 5

        #draw background
        pygame.draw.rect(screen, (20, 20, 20), (x, y, width, height))
        pygame.draw.rect(screen, (180, 180, 180), (x, y, width, height), 1)
        
        # ---------------------------------
        # Draw lines
        # ---------------------------------
        ry = y + padding
        for text, color, index in rendered_lines:
            # first line = item name (rarity color)
            if index == 0:
                color = RARITY_COLORS.get(item.rarity, color)

            surf = font.render(text, True, color)
            screen.blit(surf, (x + padding, ry))
            ry += surf.get_height()

    def click(self, pos, button):
        #prevent starting drag immediate after releasing one
        if self.just_released_drag and button == 1:
            self.just_released_drag = False
            return True

        offset_x = SCREEN_WIDTH // 2 - self.width // 2 + 150
        offset_y = SCREEN_HEIGHT //2 - self.height // 2

        for i, item_rect_data in enumerate(self.item_rects):
            #handle both old and new format
            if len(item_rect_data) == 3:
                rect, entry, cache_key = item_rect_data
            else:
                #old format - force rebuild
                self.mark_dirty()
                return False
            
            #adjust rect for window position and scroll offset
            adjusted_rect = rect.move(offset_x, offset_y - self.scroll_offset)
                
            if adjusted_rect.collidepoint(pos):

                #get the item
                item = self.cached_items[cache_key]

                #for equipping/using, we need the item_id
                if "item" in entry:
                    item_id = item.id
                else:
                    item_id = entry["id"]

                # ----------------------------------------------
                # RIGHT-CLICK → Equip OR Use
                # ----------------------------------------------
                if button == 3:

                    #consumable use
                    if item.type == "consumable":
                        #t4 = time.perf_counter()
                        self.game.player.use_item(item_id, self.game.items)
                        #print(f"[PERF] click - use_item: {(time.perf_counter() - t4) * 1000:.2f}ms")

                        #t5 = time.perf_counter()
                        print(f"[ITEM] Used {item.name}")
                        self.mark_dirty()
                        #print(f"[PERF] click - mark_dirty: {(time.perf_counter() - t5) * 1000:.2f}ms")

                        #print(f"[PERF] click - TOTAL: {(time.perf_counter() - t_start) * 1000:.2f}ms")
                        return True
                    
                    #equipment equipping
                    if item.type in ("Armor", "Weapon"):
                        equipped = self.game.player.equip_item(item)

                        if equipped:
                            print(f"[EQUIP] Equipped {item.name}")
                            self.mark_dirty()
                            return True
                # ----------------------------------------------
                # LEFT-CLICK → Start drag or apply scroll
                # ----------------------------------------------
                if button == 1:

                    #check if player has a scroll selected (enhancement mode)
                    if self.game.player.enhancement_scroll:
                        scroll = self.game.player.enhancement_scroll

                        print(f"[DEBUG] In enhancement mode, clicked on: {item.name}")

                        #check if this item can be enhanced
                        can_enhance, error_msg = self.game.player.can_enhance_item(item, scroll)

                        print(f"[DEBUG] Can enhance? {can_enhance}, Error: {error_msg}")

                        if can_enhance:
                            #show confirmation dialog
                            print("[DEBUG] Showing confirmation dialog")
                            self.game.show_enhancement_confirmation(scroll, item)
                            return True
                        else:
                            #show error message
                            print(f"[ENHANCE] {error_msg}")
                            return True
                        
                    #normal drag behavior
                    self.dragging_item = (rect, entry, cache_key)
                    self.drag_start_index = i
                    #calculate offset from mouse to rect top-left
                    self.drag_mouse_offset = (pos[0] - adjusted_rect.x, pos[1] - adjusted_rect.y)
                    #print(f"[DRAG]Started dragging {item.name}")
                    
                
                    # CRITICAL DEBUG: Show what's ACTUALLY in the inventory at this index
                    actual_item_at_index = self.game.player.inventory[i]
                    print(f"[DRAG START] Visual item: {item.name}, Index: {i}")
                    print(f"[DRAG START] Actual inventory[{i}]: {actual_item_at_index}")
                    print(f"[DRAG START] Match? {actual_item_at_index == entry}")
                    return True
                
        #clicked outside any item - clear enhancement mode if active
        if self.game.player.enhancement_scroll:
            print("[ENHANCE] Cancelled - clicked outside items")
            self.game.player.enhancement_scroll = None
            self.mark_dirty()

                    
        return False


    def click_outside(self, pos):
        x = SCREEN_WIDTH // 2 - self.width // 2
        y = SCREEN_HEIGHT // 2 - self.height // 2
        rect = pygame.Rect(x, y, self.width, self.height)
        return not rect.collidepoint(pos)
    
    def release_drag(self, pos):
        #handle mouse release - complete drag-and-drop or cancel
        if not self.dragging_item:
            return False

        offset_x = SCREEN_WIDTH // 2 - self.width // 2 + 150
        offset_y = SCREEN_HEIGHT // 2 - self.height // 2

        #check if released over another item
        drop_index = None
        for i, item_rect_data in enumerate(self.item_rects):
            #skip item currently being dragged
            if i == self.drag_start_index:
                continue
            
            if len(item_rect_data) != 3:
                continue

            rect, entry, cache_key = item_rect_data
            adjusted_rect = rect.move(offset_x, offset_y - self.scroll_offset)
            expanded_rect = adjusted_rect.inflate(0, 32)

            if expanded_rect.collidepoint(pos):
                drop_index = i
                break
        
        #perform swap if dropped on different item
        if drop_index is not None and drop_index != self.drag_start_index:
            #swap items in player inventory
            inventory = self.game.player.inventory
            
            print(f"[DRAG SWAP] Swapping inventory[{self.drag_start_index}] ↔ inventory[{drop_index}]")
            print(f"  BEFORE: [{self.drag_start_index}]={inventory[self.drag_start_index]}")
            print(f"  BEFORE: [{drop_index}]={inventory[drop_index]}")
            
            inventory[self.drag_start_index], inventory[drop_index] = inventory[drop_index], inventory[self.drag_start_index]
            
            print(f"  AFTER: [{self.drag_start_index}]={inventory[self.drag_start_index]}")
            print(f"  AFTER: [{drop_index}]={inventory[drop_index]}")
            
            self.mark_dirty()

        #clear drag state
        self.dragging_item = None
        self.drag_start_index = None
        self.drag_mouse_offset = (0, 0)

        #set flag to prevent immediate re-drag
        self.just_released_drag = True

        return True

    def _draw_scrollbar(self, screen, window_x, window_y):
        #Draw scrollbar on the right side of the inventory
        track_x = window_x + self.width - 14
        track_y = window_y + 40
        track_height = self.height - 70
        track_rect = pygame.Rect(track_x, track_y, 8, track_height)

        pygame.draw.rect(screen, (50, 50, 50), track_rect)

        #calculate thumb size and position
        visible_height = self.height - 70
        entry_height = 32
        total_height = len(self.game.player.inventory) * entry_height

        thumb_height = max(20, int((visible_height / total_height) * track_height))

        if self.max_scroll > 0:
            scroll_ratio = self.scroll_offset / self.max_scroll
        else:
            scroll_ratio = 0

        thumb_y = track_y + int(scroll_ratio * (track_height - thumb_height))
        thumb_rect = pygame.Rect(track_x, thumb_y, 8, thumb_height)

        pygame.draw.rect(screen, (160, 160, 160), thumb_rect)

    def _draw_scrollable_items(self, screen, window_x, window_y):
        #draw just the scrollable item list
        y_start = 40 #start after the header

        for i, item_rect_data in enumerate(self.item_rects):
            if len(item_rect_data) != 3:
                continue

            rect, entry, cache_key = item_rect_data
            item = self.cached_items[cache_key]

            #apply scroll offset
            draw_y = window_y + rect.y - self.scroll_offset

            #skip if outside visible area
            if draw_y + rect.height < window_y + 40: #above visible
                continue
            if draw_y > window_y + self.height - 30: #below visible
                continue

            #check if this item is eligible for enhancement
            is_eligible = False
            if self.game.player.enhancement_scroll:
                can_enhance, _ = self.game.player.can_enhance_item(item, self.game.player.enhancement_scroll)
                is_eligible = can_enhance

            #draw item background
            draw_rect = pygame.Rect(window_x + rect.x, draw_y, rect.width, rect.height)
            
            if is_eligible:
                #green background for eligible items
                pygame.draw.rect(screen, (40, 80, 40), draw_rect)
                pygame.draw.rect(screen, (80, 200, 80), draw_rect, 2)
            else:
                #normal background
                pygame.draw.rect(screen, (60, 60, 60), draw_rect)
                pygame.draw.rect(screen, (120, 120, 120), draw_rect, 1)

            #draw icon
            if item.icon_small:
                screen.blit(item.icon_small, (draw_rect.x + 5, draw_rect.y + 2))
                text_x = draw_rect.x +34
            else:
                text_x = draw_rect.x + 5

            #draw name
            screen.blit(item.name_surface, (text_x, draw_rect.y + 5))

            #draw quantity if stackable
            if item.stackable:
                qty = entry["qty"]
                rarity_color = RARITY_COLORS.get(item.rarity, (255, 255, 255))

                if qty not in item.qty_surfaces:
                    item.qty_surfaces[qty] = self.font.render(f"x{qty}", True, rarity_color)

                qty_surf = item.qty_surfaces[qty]
                screen.blit(qty_surf, (text_x + item.name_surface.get_width() + 5, draw_rect.y + 5))

            # DEBUG: Draw index number in top-right corner
            #index_font = pygame.font.Font(None, 20)
            #index_surf = index_font.render(f"[{i}]", True, (255, 255, 0))  # Yellow
            #screen.blit(index_surf, (draw_rect.right - 30, draw_rect.y + 2))
    
class VendorWindow:
    def __init__(self, game):
        self.game = game
        self.width = 500
        self.height = 500
        self.bg_color = (35, 35, 45)
        self.border_color = (200, 200, 200)
        self.text_color = (255, 255, 255)
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)

        #position (centered)
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT // 2 - self.height // 2

        #current mode
        self.mode = "buy"

        #scrolling
        self.item_rects = []
        self.scroll_offset = 0
        self.max_scroll = 0
        self.scroll_speed = 20

        #tab buttons
        self.buy_tab_rect = None
        self.sell_tab_rect = None

        #item list for buying
        self.items_for_sale = [
            {"id": "health_potion_small", "price": 1},
            {"id": "mana_potion_small", "price": 1},
            {"id": "anti_poison_potion", "price": 1},
            {"id": "Auto Attack", "price": 1},
            {"id": "weapon_attack_scroll_100", "price": 1},
            {"id": "weapon_strength_scroll_100", "price": 1},
            {"id": "weapon_constitution_scroll_100", "price": 1},
            {"id": "armor_defense_scroll_100", "price": 1},
            {"id": "armor_strength_scroll_100", "price": 1},
            {"id": "armor_constitution_scroll_100", "price": 1},
            {"id": "armor_hp_scroll_100", "price": 1},

            # ----- Training Equipment -----
            {"id": "basic_training_helmet", "price": 1},
            {"id": "basic_training_shirt", "price": 1},
            {"id": "basic_training_pants", "price": 1},
            {"id": "basic_training_boots", "price": 1},
            {"id": "basic_training_shield", "price": 1},
            #{"id": "basic_training_axe", "price": 1},
            {"id": "basic_training_sword", "price": 1}
        ]

        #cache for item data
        self.cached_item_data = {}

        #panel surface (for consistent background)
        self._rebuild_panel_surface()

    def _rebuild_panel_surface(self):
        #rebuild the background panel surface
        self.panel_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(self.panel_surface, self.bg_color, (0, 0, self.width, self.height))
        pygame.draw.rect(self.panel_surface, self.border_color, (0, 0, self.width, self.height), 2)      

    #cache item data for performance
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
    
    #switch between buy and sell modes
    def switch_mode(self, new_mode):
        if new_mode in ("buy", "sell"):
            self.mode = new_mode
            self.scroll_offset = 0
            print(f"[VENDOR] Switched to {new_mode.upper()} mode")

    #calculate how much the vendor will pay for an item
    def calculate_sell_price(self, item):
        #get base price
        base_price = self._get_base_item_price(item)

        #base sell price (for now 50% of buy price)
        sell_price = max(1, base_price // 2)

        #bonus for enhanced items
        if hasattr(item, "enhancements") and item.enhancements:
            enhancement_bonus = len(item.enhancements) * 5
            sell_price += enhancement_bonus

        #bonus for rolled stats
        if hasattr(item, "rolled_armor") and item.rolled_armor:
            armor_bonus = item.rolled_armor * 2
            sell_price += armor_bonus

        return sell_price
    
    #get base prices, checks shop first, then estimates
    def _get_base_item_price(self, item):
        #check if item is sold in shop
        for sale_item in self.items_for_sale:
            if sale_item["id"] == item.id:
                return sale_item["price"]
            
        #not in shop - estimate from item stats
        return self._estimate_item_price(item)
    
    #estimate price for items not in shop
    def _estimate_item_price(self, item):
        base_value = 10

        #rarity multiplier
        rarity_multipliers = {
            "common": 1.0,
            "uncommon": 2.0,
            "rare": 4.0,
            "epic": 8.0,
            "legendary": 16.0
        }
        rarity_mult = rarity_multipliers.get(item.rarity, 1.0)

        #type specific pricing
        if item.type == "Weapon":
            #weapons valued by damage
            avg_damage = (item.min_dmg + item.max_dmg) / 2
            base_value = avg_damage * 3

            #two handed weapons worth more
            if hasattr(item, 'hands') and item.hands == 2:
                base_value *= 1.5

        #armor valued by armor value
        elif item.type == "Armor":
            if hasattr(item, 'armor_min') and hasattr(item, 'armor_max'):
                avg_armor = (item.armor_min + item.armor_max) / 2
                base_value = avg_armor * 4

            #shields worth more
            if hasattr(item, 'armor_type') and item.armor_type == "Shield":
                base_value *= 1.3

        #consumables valued by effect
        elif item.type == "consumable":
            if hasattr(item, 'heal_amount') and item.heal_amount:
                base_value = item.heal_amount / 3

            if hasattr(item, 'mana_amount') and item.mana_amount:
                base_value += item.mana_amount / 2

            #enhancement scrolls
            if hasattr(item, 'subtype') and item.subtype == "enhancement_scroll":
                base_value = 30
                if hasattr(item, 'success_chance'):
                    base_value *= item.success_chance

        #level requirement bonus
        if hasattr(item, 'required_level') and item.required_level > 1:
            level_bonus = (item.required_level - 1) * 5
            base_value += level_bonus

        #apply rarity multiplier
        final_price = int(base_value * rarity_mult)

        return max(5, final_price)

    #calculate bonus gold from rolled stats
    def _calculate_stat_bonus(self, rolled_stats):
        stat_values = {
            "strength": 3,
            "dexterity": 3,
            "constitution": 3,
            "intelligence": 3,
            "max_hp": 0.5,
            "max_mp": 0.5,
            "armor": 4,
            "crit_chance": 10,
            "dodge_chance": 10,
            "attack_speed": 15,
        }

        total_bonus = 0

        for stat, value in rolled_stats.items():
            multiplier = stat_values.get(stat, 2)
            total_bonus += int(value * multiplier)

        return total_bonus
    
    def get_sellable_items(self):
        #get list of items from player inventory that can be sold
        sellable = []

        for entry in self.game.player.inventory:
            #handle stackable items
            if "id" in entry and entry.get("stackable", True):
                item = self.game.items.get(entry["id"])
                if item:
                    sell_price = self.calculate_sell_price(item)
                    sellable.append((item, sell_price, entry))

            #handle equipment (and non-stackables)
            elif "item" in entry:
                item = entry["item"]
                sell_price = self.calculate_sell_price(item)
                sellable.append((item, sell_price, entry))

        return sellable

    #main draw method
    def draw(self, surface):
        surface.blit(self.panel_surface, (self.x, self.y))

        self._draw_tabs(surface)
        self._draw_header(surface)

        if self.mode == "buy":
            self._draw_buy_items(surface)
        else:
            self._draw_sell_items(surface)

        if self.max_scroll > 0:
            self._draw_scrollbar(surface)

        self._draw_tooltips(surface)

        close_text = self.font.render("Click outside to close", True, (160, 160, 160))
        surface.blit(close_text, (self.x + 10, self.y + self.height - 25))

    #draw buy/sell tabs
    def _draw_tabs(self, surface):
        tab_width = 100
        tab_height = 35
        tab_y = self.y + 10

        #buy tab
        buy_x = self.x + 20
        self.buy_tab_rect = pygame.Rect(buy_x, tab_y, tab_width, tab_height)

        buy_color = (70, 140, 70) if self.mode == "buy" else (50, 50, 60)
        buy_border = (120, 200, 120) if self.mode == "buy" else (100, 100, 110)

        pygame.draw.rect(surface, buy_color, self.buy_tab_rect, border_radius = 5)
        pygame.draw.rect(surface, buy_border, self.buy_tab_rect, width = 2, border_radius = 5)

        buy_text = self.font.render("Buy", True, (255, 255, 255))
        buy_text_rect = buy_text.get_rect(center = self.buy_tab_rect.center)
        surface.blit(buy_text, buy_text_rect)

        #sell tab
        sell_x = buy_x + tab_width + 10
        self.sell_tab_rect = pygame.Rect(sell_x, tab_y, tab_width, tab_height)

        sell_color = (140, 70, 70) if self.mode == "sell" else (50, 50, 60)
        sell_border = (200, 120, 120) if self.mode == "sell" else (100, 100, 110)

        pygame.draw.rect(surface, sell_color, self.sell_tab_rect, border_radius = 5)
        pygame.draw.rect(surface, sell_border, self.sell_tab_rect, width = 2, border_radius = 5)

        sell_text = self.font.render("Sell", True, (255, 255, 255))
        sell_text_rect = sell_text.get_rect(center = self.sell_tab_rect.center)
        surface.blit(sell_text, sell_text_rect)

    #draw title and gold
    def _draw_header(self, surface):
        title_text = "Buy Items" if self.mode == "buy" else "Sell Items"
        title = self.font.render(title_text, True, self.text_color)
        surface.blit(title, (self.x + 240, self.y + 20))

        total_gold = self.game.player.get_total_gold()
        gold_text = self.font.render(f"Gold: {total_gold}", True, (255, 220, 100))
        surface.blit(gold_text, (self.x + self.width - 140, self.y + 55))

    #draw buy mode item list
    def _draw_buy_items(self, surface):
        content_area = pygame.Rect(self.x, self.y + 90, self.width, self.height - 140)
        surface.set_clip(content_area)

        entry_height = 38
        self.item_rects.clear()

        visible_top = 90
        visible_bottom = self.height - 50
        y_offset = visible_top - self.scroll_offset

        total_height = len(self.items_for_sale) * entry_height

        for entry in self.items_for_sale:
            item_id = entry["id"]
            price = entry["price"]

            cached = self._ensure_item_cached(item_id, price)

            item_top = y_offset
            item_bottom = y_offset + entry_height

            if item_bottom < visible_top:
                y_offset += entry_height
                continue

            if item_top > visible_bottom:
                break

            ITEM_RIGHT_PADDING = 32
            rect = pygame.Rect(
                self.x + 10,
                self.y + y_offset,
                self.width - ITEM_RIGHT_PADDING,
                entry_height - 8
            )

            can_afford = self.game.player.gold >= price
            bg_color = (60, 60, 60) if can_afford else (40, 40, 40)

            pygame.draw.rect(surface, bg_color, rect)
            pygame.draw.rect(surface, (100, 100, 100), rect, 1)

            if cached["icon_small"]:
                surface.blit(cached["icon_small"], (rect.x + 5, rect.y + 5))
                text_x = rect.x + 36
            else:
                text_x = rect.x + 8

            surface.blit(cached["name_surface"], (text_x, rect.y + 5))

            price_x = rect.right - cached["price_surface"].get_width() - 10
            surface.blit(cached["price_surface"], (price_x, rect.y + 5))

            self.item_rects.append((rect, cached))
            y_offset += entry_height

        self.max_scroll = max(0, total_height - (visible_bottom - visible_top))
        surface.set_clip(None)

    #draw sell mode item list
    def _draw_sell_items(self, surface):
        content_area = pygame.Rect(self.x, self.y + 90, self.width, self.height - 140)
        surface.set_clip(content_area)

        entry_height = 38
        self.item_rects.clear()

        visible_top = 90
        visible_bottom = self.height - 50
        y_offset = visible_top - self.scroll_offset

        sellable_items = self.get_sellable_items()

        if not sellable_items:
            no_items_text = self.font.render("No items to sell", True, (150, 150, 150))
            text_rect = no_items_text.get_rect(center = (self.x + self.width // 2, self.y + 200))
            surface.blit(no_items_text, text_rect)
            surface.set_clip(None)
            return
        
        total_height = len(sellable_items) * entry_height

        for item, sell_price, inventory_entry in sellable_items:
            item_top = y_offset
            item_bottom = y_offset + entry_height

            if item_bottom < visible_top:
                y_offset += entry_height
                continue

            if item_top > visible_bottom:
                break

            ITEM_RIGHT_PADDING = 32
            rect = pygame.Rect(
                self.x + 10,
                self.y + y_offset,
                self.width - ITEM_RIGHT_PADDING,
                entry_height - 8
            )

            pygame.draw.rect(surface, (60, 60, 60), rect)
            pygame.draw.rect(surface, (100, 100, 100), rect, 1)

            if hasattr(item, 'icon_small') and item.icon_small:
                surface.blit(item.icon_small, (rect.x + 5, rect.y + 5))
                text_x = rect.x + 36
            else:
                text_x = rect.x + 8

            rarity_color = RARITY_COLORS.get(item.rarity, (255, 255, 255))

            if "qty" in inventory_entry:
                name_text = f"{item.name} x{inventory_entry['qty']}"
            else:
                name_text = item.name

            name_surface = self.font.render(name_text, True, rarity_color)
            surface.blit(name_surface, (text_x, rect.y + 5))

            price_surface = self.font.render(f"{sell_price}g", True, (255, 220, 100))
            price_x = rect.right - price_surface.get_width() - 10
            surface.blit(price_surface, (price_x, rect.y + 5))

            self.item_rects.append((rect, {
                "item": item,
                "sell_price": sell_price,
                "inventory_entry": inventory_entry
            }))

            y_offset += entry_height

        self.max_scroll = max(0, total_height - (visible_bottom - visible_top))
        surface.set_clip(None)

    #draw scrollbar
    def _draw_scrollbar(self, surface):
        track_x = self.x + self.width - 14
        track_y = self.y + 90
        track_height = self.height - 140
        track_rect = pygame.Rect(track_x, track_y, 8, track_height)

        pygame.draw.rect(surface, (50, 50, 50), track_rect)

        visible_height = self.height - 140

        if self.mode == "buy":
            total_height = len(self.items_for_sale) * 38
        else:
            total_height = len(self.get_sellable_items()) * 38

        if total_height == 0:
            return
        
        thumb_height = max(20, int((visible_height / total_height) * track_height))

        if self.max_scroll > 0:
            scroll_ratio = self.scroll_offset / self.max_scroll
        else:
            scroll_ratio = 0

        thumb_y = track_y + int(scroll_ratio * (track_height - thumb_height))
        thumb_rect = pygame.Rect(track_x, thumb_y, 8, thumb_height)

        pygame.draw.rect(surface, (160, 160, 160), thumb_rect)

    #draw tooltips on hover
    def _draw_tooltips(self, surface):
        mouse_pos = pygame.mouse.get_pos()

        for rect, cached in self.item_rects:
            if rect.collidepoint(mouse_pos):
                item = cached["item"]
                if item:
                    self.draw_tooltip(surface, item, mouse_pos)
                break

    def draw_tooltip(self, surface, item, mouse_pos):
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

        pygame.draw.rect(surface, (20, 20, 20), (x, y, width + padding * 2, height + padding * 2))
        pygame.draw.rect(surface, (180, 180, 180), (x, y, width + padding * 2, height + padding * 2), 1)

        rarity_color = RARITY_COLORS.get(item.rarity, (255, 255, 255))

        name_surf = self.font.render(item.name, True, rarity_color)
        surface.blit(name_surf, (x + padding, y + padding))

        ry = y + padding + name_surf.get_height()

        for surf in item.tooltip_surfaces[1:]:
            surface.blit(surf, (x + padding, ry))
            ry += surf.get_height()

    def handle_click(self, pos):
        #handle mouse clicks
        if self.buy_tab_rect and self.buy_tab_rect.collidepoint(pos):
            self.switch_mode("buy")
            return True
        
        if self.sell_tab_rect and self.sell_tab_rect.collidepoint(pos):
            self.switch_mode("sell")
            return True
        
        if self.mode == "buy":
            return self._handle_buy_click(pos)
        else:
            return self._handle_sell_click(pos)
        
    #handle buying an item
    def _handle_buy_click(self, pos):
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
    
    #handle selling an item
    def _handle_sell_click(self, pos):
        for rect, data in self.item_rects:
            if rect.collidepoint(pos):
                item = data["item"]
                sell_price = data["sell_price"]
                inventory_entry = data["inventory_entry"]

                self.game.player.gold += sell_price

                if "qty" in inventory_entry:
                    inventory_entry["qty"] -= 1
                    if inventory_entry["qty"] <= 0:
                        self.game.player.inventory.remove(inventory_entry)
                else:
                    self.game.player.inventory.remove(inventory_entry)

                print(f"[VENDOR] Sold {item.name} for {sell_price} gold.")

                if hasattr(self.game, 'inventory_window'):
                    self.game.inventory_window.mark_dirty()

                return True
        
        return False
    
    def is_click_outside(self, pos):
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        return not rect.collidepoint(pos)
    
class SpellbookWindow:
    def __init__(self, player, spellbook, on_assign_callback):
        self.player = player
        self.spellbook = spellbook
        self.on_assign_callback = on_assign_callback
        self.visible = False

        #window dimensions
        self.width = 500
        self.height = 565
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT // 2 - self.height // 2
        
        #colors
        self.bg_color = (30, 30, 40)
        self.border_color = (150, 150, 150)
        self.header_color = (200, 150, 50)
        self.spell_bg_color = (45, 45, 55)
        self.spell_hover_color = (80, 120, 180)
        self.spell_selected_color = (80, 120, 180)

        #fonts
        self.title_font = pygame.font.Font(None, 32)
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)

        #Pagination
        self.current_page = 0
        self.spells_per_page = 5

        #selection state
        self.selected_slot = None

        #icon placeholder surface (spells without icons)
        self.placeholder_icon = self.create_placeholder_icon()

        #pre-scaled spell icons
        self.icon_size = 44
        self.scaled_spell_icons = {}
        for spell in spellbook:
            if hasattr(spell, 'icon') and spell.icon:
                self.scaled_spell_icons[spell.name] = pygame.transform.smoothscale(
                    spell.icon,
                    (self.icon_size, self.icon_size)
                )

        #store spell rects for click detection
        self.spell_rects = []
        self.prev_button_rect = None
        self.next_button_rect = None  

    #create placeholder icon for spells without custom icons
    def create_placeholder_icon(self):
        size = 44
        surface = pygame.Surface((size, size), pygame.SRCALPHA)

        #draw a simple circle as placeholder
        pygame.draw.circle(surface, (100, 100, 200), (size // 2, size // 2), size // 2 - 2, 2)
        pygame.draw.circle(surface, (150, 150, 255), (size // 2, size // 2), size // 3, 1)

        #draw star in center
        center_x, center_y = size // 2, size // 2
        points = []
        for i in range(5):
            angle = i * 144 - 90 #144 degrees between points, starts at top
            import math
            x = center_x + int(size // 4 * math.cos(math.radians(angle)))
            y = center_y + int(size // 4 * math.sin(math.radians(angle)))
            points.append((x, y))

        pygame.draw.polygon(surface, (200, 200, 255), points, 0)

        return surface
    
    #calculate total number of pages needed
    def get_total_pages(self):
        import math
        return max(1, math.ceil(len(self.spellbook) / self.spells_per_page))
    
    #get the spells for the current page
    def get_current_page_spells(self):
        start_idx = self.current_page * self.spells_per_page
        end_idx = start_idx + self.spells_per_page
        return self.spellbook[start_idx:end_idx]

    #toggle spellbook visibility and manage selection state
    def toggle(self, slot_index = None):
        was_visible = self.visible
        self.visible = not self.visible
        
        if self.visible:
            if slot_index is not None:
                self.selected_slot = slot_index
                print(f"📖 Spellbook opened for slot assignment (slot={slot_index})")
            else:
                self.selected_slot = None
                print(f"📖 Spellbook opened (browsing mode)")   
        else:
            self.selected_slot = None
            if hasattr(self.player, 'game') and hasattr(self.player.game, "selected_spell_slot"):
                self.player.game.selected_spell_slot = None
            print(f"📖 Spellbook closed (selection cleared)")
        
    def draw(self, surface):
        if not self.visible:
            return

        #draw background panel
        panel_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.bg_color, panel_rect, border_radius = 8)
        pygame.draw.rect(surface, self.border_color, panel_rect, 2, border_radius = 8)

        #draw title
        title_text = self.title_font.render("Spellbook", True, self.header_color)
        title_rect = title_text.get_rect(centerx = self.x + self.width // 2, top = self.y + 15)
        surface.blit(title_text, title_rect)

        #Draw slot assignement instruction if a slot is selected
        if self.selected_slot is not None:
            instruction = self.small_font.render(
                f"Select a spell to assign to Slot {self.selected_slot}",
                True,
                (200, 200, 200)
            )
            instruction_rect = instruction.get_rect(centerx = self.x + self.width // 2, top = self.y + 55)
            surface.blit(instruction, instruction_rect)
            content_start_y = self.y + 90
        else:
            content_start_y = self.y + 60

        #draw spells for current page
        self.spell_rects = []
        current_spells = self.get_current_page_spells()

        spell_height = 65
        spell_spacing = 8
        spell_width = self.width - 40

        for i, spell in enumerate(current_spells):
            spell_y = content_start_y + i * (spell_height + spell_spacing)
            spell_rect = pygame.Rect(self.x + 20, spell_y, spell_width, spell_height)

            #check if mouse is hovering
            mouse_pos = pygame.mouse.get_pos()
            is_hovering = spell_rect.collidepoint(mouse_pos)

            #check if spell is already equipped
            is_equipped = self.is_spell_equipped(spell)

            #determine background color
            if is_equipped:
                bg_color = self.spell_selected_color
            elif is_hovering:
                bg_color = self.spell_hover_color
            else:
                bg_color = self.spell_bg_color

            #draw spell background
            pygame.draw.rect(surface, bg_color, spell_rect, border_radius = 6)
            pygame.draw.rect(surface, self.border_color, spell_rect, 2, border_radius = 6)

            #draw spell icon
            icon_x = spell_rect.x + 10
            icon_y = spell_rect.y + (spell_rect.height - self.icon_size) // 2

            #use prescaled icon if available
            if spell.name in self.scaled_spell_icons:
                surface.blit(self.scaled_spell_icons[spell.name], (icon_x, icon_y))
            else:
                surface.blit(self.placeholder_icon, (icon_x, icon_y))

            #draw spell name
            name_text = self.font.render(spell.name, True, (255, 255, 255))
            name_x = icon_x + 58
            name_y = spell_rect.y + 10
            surface.blit(name_text, (name_x, name_y))

            #draw spell info
            info_lines = [
                f"MP: {spell.mana_cost}  |  CD: {spell.cooldown}s",
                f"Damage: {spell.power}"
            ]

            info_y = name_y + 20
            for info_line in info_lines:
                info_text = self.small_font.render(info_line, True, (180, 180, 180))
                surface.blit(info_text, (name_x, info_y))
                info_y += 18

            #store rect for click detection
            self.spell_rects.append((spell_rect, spell))

        #draw pagination buttons
        self.draw_pagination_buttons(surface)

        #draw close instructions
        close_text = self.small_font.render("Click outside to close", True, (160, 160, 160))
        surface.blit(close_text, (self.x + 10, self.y + self.height - 25))

        #draw tooltip if hovering over a spell
        mouse_pos = pygame.mouse.get_pos()
        for spell_rect, spell in self.spell_rects:
            if spell_rect.collidepoint(mouse_pos):
                self.draw_spell_tooltip(surface, spell, mouse_pos)
                break

    #draw previous/next page buttons
    def draw_pagination_buttons(self, surface):
        total_pages = self.get_total_pages()

        if total_pages <= 1:
            return #no pagination needed
        
        button_width = 100
        button_height = 35
        button_y = self.y + self.height - 65

        #previous button (only show if not on first page)
        if self.current_page > 0:
            prev_x = self.x + 20
            self.prev_button_rect = pygame.Rect(prev_x, button_y, button_width, button_height)

            pygame.draw.rect(surface, (50, 80, 150), self.prev_button_rect, border_radius = 5)
            pygame.draw.rect(surface, (100, 140, 200), self.prev_button_rect, 2, border_radius = 5)

            prev_text = self.font.render("Previous", True, (255, 255, 255))
            prev_text_rect = prev_text.get_rect(center = self.prev_button_rect.center)
            surface.blit(prev_text, prev_text_rect)
        else:
            self.prev_button_rect = None

        #page indicator
        page_text = self.small_font.render(
            f"Page {self.current_page + 1} / {total_pages}",
            True,
            (200, 200, 200)
        )
        page_text_rect = page_text.get_rect(centerx = self.x + self.width // 2, centery = button_y + button_height // 2)
        surface.blit(page_text, page_text_rect)

        #next button (only show if not on last page)
        if self.current_page < total_pages - 1:
            next_x = self.x + self.width - button_width - 20
            self.next_button_rect = pygame.Rect(next_x, button_y, button_width, button_height)

            pygame.draw.rect(surface, (50, 80, 150), self.next_button_rect, border_radius = 5)
            pygame.draw.rect(surface, (100, 140, 200), self.next_button_rect, 2, border_radius = 5)

            next_text = self.font.render("Next →", True, (255, 255, 255))
            next_text_rect = next_text.get_rect(center = self.next_button_rect.center)
            surface.blit(next_text, next_text_rect)
        else:
            self.next_button_rect = None

    #check if a spell is currently equipped in any slot
    def is_spell_equipped(self, spell):
        if hasattr(self.player.game, "spell_slots"):
            for slot, equipped_spell in self.player.game.spell_slots.items():
                if equipped_spell.name == spell.name:
                    return True
        return False
    
    def handle_click(self, pos):
        if not self.visible:
            return False
        
        #check if click is outside the window - close and clear selection
        window_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        if not window_rect.collidepoint(pos):
            self.toggle()
            return True
        
        #check pagination buttons
        if self.prev_button_rect and self.prev_button_rect.collidepoint(pos):
            self.current_page = max(0, self.current_page - 1)
            return True
        
        if self.next_button_rect and self.next_button_rect.collidepoint(pos):
            self.current_page = min(self.get_total_pages() - 1, self.current_page + 1)
            return True

        #check spell selections
        for spell_rect, spell in self.spell_rects:
            if spell_rect.collidepoint(pos):
                if self.selected_slot is None:
                    print(f"[INFO] Clicked {spell.name}, but no slot is selected.")
                    return True
                
                print(f"🪄 Selected {spell.name} for Slot {self.selected_slot}")
                if self.on_assign_callback:
                    self.on_assign_callback(self.selected_slot, spell)

                self.toggle(None)
                return True
            
        #click was inside window buyt on on any interactive element 
        return True
    
    #draw detailed tooltip for a spell
    def draw_spell_tooltip(self, surface, spell, mouse_pos):
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
            f"Element: {spell.element}"
        ]

        if equipped_slot:
            lines.append(f"Equipped to Slot {equipped_slot}")
        else:
            lines.append("Not equipped")

        font = self.small_font
        padding = 8

        #calculate size
        max_width = 0
        total_height = 0
        for line in lines:
            surf = font.render(line, True, (255, 255, 255))
            max_width = max(max_width, surf.get_width())
            total_height += surf.get_height() + 2

        width = max_width + padding * 2
        height = total_height + padding * 2
        
        #position tooltip
        x, y = mouse_pos
        x += 15
        y += 15

        #keep on screen
        if x + width > SCREEN_WIDTH:
            x = SCREEN_WIDTH - width - 5
        if y + height > SCREEN_HEIGHT:
            y = SCREEN_HEIGHT - height - 5

        rect = pygame.Rect(x, y, width, height)

        #draw background
        pygame.draw.rect(surface, (30, 30, 30), rect, border_radius = 5)
        pygame.draw.rect(surface, (150, 150, 150), rect, 2, border_radius = 5)

        #draw text
        text_y = y + padding
        for i, line in enumerate(lines):
            #color the first line (spell name) specially
            if i == 0:
                color = (255, 215, 0) #Gold
            elif "Equipped" in line:
                color = (100, 255, 100) #Green
            elif "Not equipped" in line:
                color = (180, 180, 180) #Gray
            else:
                color = (255, 255, 255) #White

            surf = font.render(line, True, color)
            surface.blit(surf, (x + padding, text_y))
            text_y += surf.get_height() + 2

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

        #calculate tooltip size
        lines = item.tooltip_text()
        font = self.small_font

        #calculate width and height
        max_width = 0
        total_height = 0
        for line in lines:
            # -------------------------------
            # Normalize tooltip line
            # -------------------------------
            if isinstance(line, dict):
                text = line.get("text", "")
            else:
                text = line
            
            #strip markers for width calculation
            display_line = (
                text.replace("ROLLED:", "")
                    .replace("ENHANCED:", "")
                    .replace("SLOTS:", "")
            )

            #special-case level requirements
            if text.startswith("Level Required:"):
                req_level = int(text.split(":")[1])
                render_text = f"Requires Level: {req_level}"
            else:
                render_text = display_line

            surf = font.render(render_text, True, (255, 255, 255))
            max_width = max(max_width, surf.get_width())
            total_height += surf.get_height()
        
        width = max_width + padding * 2
        height = total_height + padding * 2

        #screen boundary checks
        if x + width > SCREEN_WIDTH:
            x = SCREEN_WIDTH - width - 5
        if y + height > SCREEN_HEIGHT:
            y = SCREEN_HEIGHT - height - 5

        #Background
        pygame.draw.rect(surface, (20, 20, 20), (x, y, width, height))
        pygame.draw.rect(surface, (180, 180, 180), (x, y, width, height), 1)

        ry = y + padding
        
        for i, line in enumerate(lines):

            # -------------------------------
            # Normalize tooltip line
            # -------------------------------
            if isinstance(line, dict):
                text = line.get("text", "")
                color_key = line.get("color", "normal")
            else:
                text = line
                color_key = "normal"

            # -------------------------------
            # Determine color
            # -------------------------------
            color = (255, 255, 255)

            if color_key == "enhanced":
                color = (80, 220, 80)
            
            #first line is name (rarirty colored)
            if i == 0:
                color = RARITY_COLORS.get(item.rarity, (255, 255, 255))
                surf = font.render(text, True, color)

            #level requirement (color based on player level)
            elif text.startswith("Level Required:"):
                req_level = int(text.split(":")[1])
                player_level = self.game.player.level
                
                if player_level >= req_level:
                    color = (100, 255, 100) #green
                else:
                    color = (255, 100, 100) #red
                
                text = f"Requires Level: {req_level}"
                surf = font.render(text, True, color)

            #rolled stats
            elif text.startswith("ROLLED:"):
                display_text = text.replace("ROLLED:", "")
                surf = font.render(display_text, True, (100, 255, 100)) #green

            #enhancement slots
            elif text.startswith("SLOTS:"):
                display_text = text.replace("SLOTS:", "Slots: ")
                surf = font.render(display_text, True, (255, 215, 0)) #gold

            #normal lines
            else:
                surf = font.render(text, True, color)

            surface.blit(surf, (x + padding, ry))
            ry += surf.get_height()


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

        self.pending_points = {
            "strength": 0,
            "dexterity": 0,
            "constitution": 0,
            "intelligence": 0
        }

    def open(self):
        self.visible = True

    def close(self):
        self.visible = False
    
    def draw(self, screen):
        if not self.visible:
            return

        #Draw background panel
        panel = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (30, 30, 30, 230), (0, 0, self.width, self.height))
        pygame.draw.rect(panel, (200, 200, 200), (0, 0, self.width, self.height), 2)
        screen.blit(panel, (self.x, self.y))

        #Title
        title = self.font.render("Level Up!", True, (255, 255, 255))
        screen.blit(title, (self.x + 110, self.y + 10))

        #show available points (total - pending)
        p = self.game.player
        available = self.get_available_points()
        pts_text = self.font.render(f"Points: {available}", True, (255, 255, 100))
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
            #current stat value
            current_val = getattr(p.stats, attr)
            pending = self.pending_points[attr]

            #show stat: "Strength: 10 → 13" if pending, or just "Strength: 10"
            if pending > 0:
                text = self.small_font.render(f"{label}: {current_val} to {current_val + pending}", True, (100, 255, 100))
            else:
                text = self.small_font.render(f"{label}: {current_val}", True, (255, 255, 255))
            
            screen.blit(text, (self.x + 20, start_y))

            #minus button (only show if there are pending points for this stat)
            if pending > 0:
                minus_rect = pygame.Rect(self.x + 220, start_y - 5, 30, 30)
                pygame.draw.rect(screen, (80, 40, 40), minus_rect) #dark red
                pygame.draw.rect(screen, (160, 80, 80), minus_rect, 2)
                minus_text = self.small_font.render("-", True, (255, 255, 255))
                screen.blit(minus_text, (minus_rect.x + 10, minus_rect.y + 2))
                self.buttons.append((minus_rect, f"minus_{attr}"))

            #plus button (only show if we have available points)
            if available > 0:          
                plus_rect = pygame.Rect(self.x + 260, start_y - 5, 30, 30)
                pygame.draw.rect(screen, (40, 80, 40), plus_rect)
                pygame.draw.rect(screen, (80, 160, 80), plus_rect, 2)
                plus_text = self.small_font.render("+", True, (255, 255, 255))
                screen.blit(plus_text, (plus_rect.x + 8, plus_rect.y + 4))
                self.buttons.append((plus_rect, f"plus_{attr}"))

            start_y += 40

        #confirm button
        confirm_rect = pygame.Rect(self.x + 90, self.y + 250, 180, 30)

        #gray out if no changes were made
        total_pending = sum(self.pending_points.values())
        if total_pending > 0:
            pygame.draw.rect(screen, (50, 120, 50), confirm_rect) #green
        else:
            pygame.draw.rect(screen, (60, 60, 60), confirm_rect) #gray

        pygame.draw.rect(screen, (200, 200, 200), confirm_rect, 2)
        confirm_text = self.small_font.render("Confirm", True, (255, 255, 255))
        screen.blit(confirm_text, (confirm_rect.x + 50, confirm_rect.y + 5))
        self.buttons.append((confirm_rect, "confirm"))

    def handle_click(self, pos):
        p = self.game.player

        for rect, action in self.buttons:
            if rect.collidepoint(pos):

                #confirm button
                if action == "confirm":
                    #only close if ther eare pending changes to apply
                    if sum(self.pending_points.values()) > 0:
                        self.apply_pending_points()
                        self.close()
                    return
                
                #plus button
                if action.startswith("plus_"):
                    stat = action.replace("plus_", "")
                    available = self.get_available_points()

                    if available > 0:
                        self.pending_points[stat] += 1
                    return
                
                #minus button
                if action.startswith("minus_"):
                    stat = action.replace("minus_", "")

                    if self.pending_points[stat] > 0:
                        self.pending_points[stat] -= 1
                    return
                
    def get_available_points(self):
        #calculate how many poitns are still unallocated
        total_pending = sum(self.pending_points.values())
        return self.game.player.stat_points - total_pending
    
    def reset_pending_points(self):
        #clear all pending allocations
        for key in self.pending_points:
            self.pending_points[key] = 0

    def apply_pending_points(self):
        #actually apply the pending points to player stats
        p = self.game.player
        for stat, amount in self.pending_points.items():
            if amount > 0:
                current_val = getattr(p.stats, stat)
                setattr(p.stats, stat, current_val + amount)
                p.stat_points -= amount

                #update base value so gear bonsues work correctly
                base_stat_name = f"base_{stat}"
                if hasattr(p.stats, base_stat_name):
                    current_base = getattr(p.stats, base_stat_name)
                    setattr(p.stats, base_stat_name, current_base + amount)

        #recalculate derived stats
        p.stats.recalc_stats()

        #clear pending after applying
        self.reset_pending_points()

class EnhancementConfirmationWindow:
    def __init__(self, game):
        self.game = game
        self.visible = False
        self.scroll = None
        self.target_item = None

        self.width = 400
        self.height = 280
        self.bg_color = (30, 30, 30)
        self.border_color = (150, 150, 150)

        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 30)

        self.confirm_button = None
        self.cancel_button = None

    def show(self, scroll, target_item):
        #show confirmation dialog for enhancement
        #print(f"[DEBUG DIALOG] show() called with scroll={scroll.name}, item={target_item.name}")
        self.visible = True
        self.scroll = scroll
        self.target_item = target_item
        #print(f"[DEBUG DIALOG] After setting: visible={self.visible}, scroll={self.scroll}, target={self.target_item}")

    def hide(self):
        #hide confirmation dialog
        self.visible = False
        self.scroll = None
        self.target_item = None

    def draw(self, screen):
        if not self.visible or not self.scroll or not self.target_item:
            return
        
        #print(f"[DEBUG DIALOG] Drawing confirmation dialog at visible={self.visible}")

        x = SCREEN_WIDTH // 2 - self.width // 2
        y = SCREEN_HEIGHT // 2 - self.height // 2

        #background
        panel = pygame.Rect(x, y, self.width, self.height)
        pygame.draw.rect(screen, self.bg_color, panel)
        pygame.draw.rect(screen, self.border_color, panel, 2)

        #title
        title = self.title_font.render("Enhance Item?", True, (255, 255, 255))
        screen.blit(title, (x + self.width // 2 - title.get_width() // 2, y + 15))

        #item info
        y_offset = y + 60

        item_text = self.font.render(f"Item: {self.target_item.name}", True, (255, 255, 255))
        screen.blit(item_text, (x + 20, y_offset))
        y_offset += 30

        scroll_text = self.font.render(f"Scroll: {self.scroll.name}", True, (200, 200, 255))
        screen.blit(scroll_text, (x + 20, y_offset))
        y_offset += 30

        bonus_text = self.font.render(f"Bonus: +{self.scroll.stat_bonus} {self.scroll.stat_to_enhance.replace('_', ' ').title()}", True, (100, 255, 100))
        screen.blit(bonus_text, (x + 20, y_offset))
        y_offset += 30

        success_text = self.font.render(f"Success Rate: {int(self.scroll.success_chance * 100)}%", True, (255, 255, 100))
        screen.blit(success_text, (x + 20, y_offset))
        y_offset += 30

        slots_remaining = self.target_item.enhancement_slots - self.target_item.used_slots
        slots_text = self.font.render(f"Slots Remaining: {slots_remaining}/{self.target_item.enhancement_slots}", True, (200, 200, 200))
        screen.blit(slots_text, (x + 20, y_offset))
        y_offset += 35

        #warning for boom scrolls
        if not self.scroll.is_safe_scroll:
            warning = self.font.render("WARNING: Item may be destroyed on failure!", True, (255, 100, 100))
            screen.blit(warning, (x + self.width // 2 - warning.get_width() // 2, y_offset))
            y_offset += 30

        #buttons
        button_y = y + self.height - 60

        self.confirm_button = pygame.Rect(x + 50, button_y, 130, 40)
        self.cancel_button = pygame.Rect(x + self.width - 180, button_y, 130, 40)

        #confirm button
        pygame.draw.rect(screen, (50, 150, 50), self.confirm_button)
        pygame.draw.rect(screen, (100, 255, 100), self.confirm_button, 2)
        confirm_text = self.font.render("Confirm", True, (255, 255, 255))
        screen.blit(confirm_text, (self.confirm_button.x + self.confirm_button.width // 2 - confirm_text.get_width() // 2,
                                   self.confirm_button.y + self.confirm_button.height // 2 - confirm_text.get_height() // 2))


        #cancel button
        pygame.draw.rect(screen, (150, 50, 50), self.cancel_button)
        pygame.draw.rect(screen, (255, 100, 100), self.cancel_button, 2)
        cancel_text = self.font.render("Cancel", True, (255, 255, 255))
        screen.blit(cancel_text, (self.cancel_button.x + self.cancel_button.width // 2 - cancel_text.get_width() // 2,
                                   self.cancel_button.y + self.cancel_button.height // 2 - cancel_text.get_height() // 2))
        


    def click(self, pos):
        #handle clicks on the confirmation dialog
        #print(f"[DEBUG DIALOG] Click at {pos}, visible={self.visible}")
        if not self.visible:
            return False
        
        #print(f"[DEBUG DIALOG] Checking buttons: confirm={self.confirm_button}, cancel={self.cancel_button}")

        if self.confirm_button and self.confirm_button.collidepoint(pos):
            #apply enhancement
            #print("[DEBUG DIALOG] CONFIRM clicked!")
            result = self.game.player.apply_enhancement(self.scroll, self.target_item)

            #clear enhancement mode
            self.game.player.enhancment_scroll = None

            #show result
            self.game.show_enhancement_result(result)

            #refresh invenetory
            self.game.inventory_window.mark_dirty()

            self.hide()
            return True
        
        if self.cancel_button and self.cancel_button.collidepoint(pos):
            #cancel - clear enhancement mode
            self.game.player.enhancement_scroll = None
            self.hide()
            return True
        
        return True #consume click even if not on button (prevent clicking through)


