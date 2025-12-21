# entity/granade.py

import config


class Granade:
    STATE_FLYING = "flying"
    STATE_EXPLODING = "exploding"
    STATE_DEAD = "dead"

    def __init__(
        self,
        x,
        y,
        direction=1,            # -1 esquerda, 1 direita
        owner="player",
        speed_x=450.0,
        speed_y=-700.0,
        damage=3500,
        flight_radius=8,        
        explosion_radius=80,    
        fuse_time=0.8,          
        gravity=1800.0,         
        explosion_duration=0.2  
    ):
        # Posição
        self.x = float(x)
        self.y = float(y)

        # Velocidade inicial
        self.vx = float(speed_x) * (1 if direction >= 0 else -1)
        self.vy = float(speed_y)

        self.owner = owner
        self.damage = int(damage)

        # Granadas boss
        self.impact_only = (owner == "boss")

        # Tamanhos
        self.flight_radius = int(flight_radius)
        self.explosion_radius = int(explosion_radius)

        # Física
        self.gravity = float(gravity)
        self.fuse_time = float(fuse_time)
        self.explosion_duration = float(explosion_duration)

        # Estado
        self.state = self.STATE_FLYING
        self.alive = True

        self._elapsed = 0.0             
        self._explosion_elapsed = 0.0   
        self.damage_applied = False

    # ------------------------------------------------------------------ #
    # Lógica
    # ------------------------------------------------------------------ #

    def update(self, dt):

        if not self.alive:
            return

        self._elapsed += dt

        if self.state == self.STATE_FLYING:
            # Gravidade
            self.vy += self.gravity * dt
            self.x += self.vx * dt
            self.y += self.vy * dt

            # Impacto com o chão
            try:
                ground_y = float(getattr(config, "HEIGHT", 0))
            except Exception:
                ground_y = 0.0

            if ground_y > 0:
                if self.y >= ground_y - self.flight_radius:
                    self.y = ground_y - self.flight_radius
                    self.explode()
                    return

            # Timer
            if not getattr(self, "impact_only", False):
                if self._elapsed >= self.fuse_time:
                    self.explode()

        elif self.state == self.STATE_EXPLODING:
            self._explosion_elapsed += dt
            if self._explosion_elapsed >= self.explosion_duration:
                self.state = self.STATE_DEAD
                self.alive = False

    def explode(self):
        if self.state != self.STATE_FLYING:
            return

        self.state = self.STATE_EXPLODING
        self._explosion_elapsed = 0.0

    def mark_for_removal(self):
        self.state = self.STATE_DEAD
        self.alive = False

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def is_flying(self):
        return self.state == self.STATE_FLYING

    def is_exploding(self):
        return self.state == self.STATE_EXPLODING

    def is_dead(self):
        return (not self.alive) or self.state == self.STATE_DEAD

    def get_center(self):
        return self.x, self.y

    def get_draw_data(self):
        if self.is_dead():
            return None

        if self.state == self.STATE_FLYING:
            radius = self.flight_radius
        else:
            radius = self.explosion_radius

        return {
            "x": self.x,
            "y": self.y,
            "radius": radius,
            "exploding": self.state == self.STATE_EXPLODING,
        }
