import pygame
from typing import List, Optional, Callable

#base class for all UI windows
class Window:
    #initialize a window
    def __init__(self, name: str, priority: int = 0):
        self.name = name
        self.priority = priority
        self._visible = False

    @property
    def visible(self):
        return self._visible
    
    @visible.setter
    def visible(self, value):
        self._visible = value

    #handle a pygame event
    #returns: True if event was consumed (stop propagation).
    #false if event should continue to lower windows
    def handle_event(self, event):
        return False
    
    #update window state
    def update(self, dt: float):
        pass

    #draw the window
    def draw(self, surface: pygame.Surface):
        pass

    #check if a point is within the window bounds
    def is_point_inside(self, pos: tuple) -> bool:
        return False
    
#Manages multiple windows with priority-based event handling and z-ordering.

class WindowManager:    
    def __init__(self):
        self.windows = []
    
    #Register a window and maintain sorted order by priority (highest first).
    def register(self, window):
        self.windows.append(window)
        self.windows.sort(key=lambda w: w.priority, reverse=True)
    
    #Route event to windows in priority order.
    #Returns True if any window consumed the event.
    def handle_event(self, event):
        for window in self.windows:
            if not window.visible:
                continue
            
            # If this is a modal window and it's visible, only it can receive events
            if window.modal:
                return window.handle_event(event)
            
            # Try to handle event
            if window.handle_event(event):
                return True
            
            # If we hit a modal window (even if it didn't consume the event),
            # don't pass events to lower-priority windows
            if window.modal:
                return False
        
        return False

#adapter class to wrap exisiting game windows
class GameWindow(Window):
    def __init__(
            self,
            name: str,
            wrapped_window,
            priority: int = 0,
            modal: bool = False,
            get_visible: Optional[Callable] = None,
            set_visible: Optional[Callable] = None,
            handle_event_fn: Optional[Callable] = None
    ):
        
        self._get_visible = get_visible
        self._set_visible = set_visible
        self.wrapped_window = wrapped_window
        self.modal = modal
        self._handle_event_fn = handle_event_fn

        super().__init__(name, priority)
        if wrapped_window and hasattr(wrapped_window, 'visible'):
            self._visible = wrapped_window.visible
        elif get_visible:
            self._visible = get_visible()

    #get visibility from wrapped window if available, else internal state
    @property
    def visible(self):
        if self._get_visible:
            return self._get_visible()
        if self.wrapped_window and hasattr(self.wrapped_window, 'visible'):
            return self.wrapped_window.visible
        return self._visible
    
    @visible.setter
    def visible(self, value):
        self._visible = value

        if self._set_visible:
            self._set_visible(value)
        elif self.wrapped_window and hasattr(self.wrapped_window, 'visible'):
            self.wrapped_window.visible = value

    def handle_event(self, event):
        if not self.visible:
            return False
        
        if self._handle_event_fn:
            return self._handle_event_fn(event)
        
        if self.wrapped_window and hasattr(self.wrapped_window, 'handle_event'):
            return self.wrapped_window.handle_event(event)
        
        return False        