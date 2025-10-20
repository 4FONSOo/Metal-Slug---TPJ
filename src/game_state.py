class BaseState:
    def __init__(self, manager):
        self.manager = manager
    def enter(self):
        pass
    def exit(self):
        pass
    def handle_event(self, event):
        pass
    def update(self, dt):
        pass
    def render(self):
        pass

class GameStateManager:
    def __init__(self, screen):
        self.screen = screen
        self.states = {}
        self.current = None

    def register(self, name, state):
        self.states[name] = state

    def change_state(self, name):
        if self.current:
            self.current.exit()
        self.current = self.states.get(name)
        if self.current:
            self.current.enter()

    def handle_event(self, event):
        if self.current:
            self.current.handle_event(event)

    def update(self, dt):
        if self.current:
            self.current.update(dt)

    def render(self):
        if self.current:
            self.current.render()