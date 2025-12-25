import pygame

#centralized font management system to prevent redundant font creation
class FontManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    #initialize the font cache only once
    def __init__(self):
        #prevent re-initialization
        if self._initialized:
            return
        
        self.fonts = {}
        self._initialized = True
        print("[FONT MANAGER] Initialized font cache")

    #get a font of the specified size
    def get(self, size):
        if size not in self.fonts:
            self.fonts[size] = pygame.font.Font(None, size)
            print(f"[FONT MANAGER] Created new font: size {size}")

        return self.fonts[size]
    
    #get custom font from a file path
    def get_custom(self, font_path, size):
        cache_key = (font_path, size)

        if cache_key not in self.fonts:
            try:
                self.fonts[cache_key] = pygame.font.Font(font_path, size)
                print(f"[FONT MANAGER] Created custom font: {font_path} size {size}")
            except Exception as e:
                print(f"[FONT MANAGER] Error loading custom font {font_path}: {e}")
                #fallback to default font
                return self.get(size)
        
        return self.fonts[cache_key]
    
    #pre-create commonly used sizes to avoid delays
    def preload_common_sizes(self):
        common_sizes = [20, 22, 24, 26, 28, 30, 32, 35, 36, 40, 42, 70, 80]

        print("[FONT MANAGER] Preloading common font sizes...")
        for size in common_sizes:
            self.get(size)

        print(f"[FONT MANAGER] Preloading {len(common_sizes)} font sizes")

    #clear all cached fonts
    def clear_cache(self):
        self.fonts.clear()
        print("[FONT MANAGER] Font cache cleared")

    #get statistics about font cache usage
    def get_cache_stats(self):
        return {
            'total_fonts': len(self.fonts),
            'cached_sizes': sorted([k for k in self.fonts.keys() if isinstance(k, int)]),
            'cached_custom': [k for k in self.fonts.keys() if isinstance(k, tuple)]
        }
