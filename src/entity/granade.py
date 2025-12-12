# granade.py
#
# Lógica da granada (Granade):
#  - movimento em arco (velocidade inicial + gravidade)
#  - explode após um certo tempo (fuse_time, em segundos) OU por impacto
#  - dano em área (explosion_radius)
#  - NÃO depende de pygame nem de pg_engine.

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
        flight_radius=8,        # raio da bola em voo
        explosion_radius=80,    # raio da explosão (dano em área)
        fuse_time=0.8,          # segundos até explodir (se NÃO for só impacto)
        gravity=1800.0,         # px/s^2
        explosion_duration=0.2  # segundos visíveis da explosão
    ):
        # posição contínua
        self.x = float(x)
        self.y = float(y)

        # velocidade inicial
        self.vx = float(speed_x) * (1 if direction >= 0 else -1)
        self.vy = float(speed_y)

        self.owner = owner
        self.damage = int(damage)

        # Granadas do boss → só por impacto (sem fuse temporizado)
        self.impact_only = (owner == "boss")

        # tamanhos
        self.flight_radius = int(flight_radius)
        self.explosion_radius = int(explosion_radius)

        # física / tempo
        self.gravity = float(gravity)
        self.fuse_time = float(fuse_time)
        self.explosion_duration = float(explosion_duration)

        # estado interno
        self.state = self.STATE_FLYING
        self.alive = True

        self._elapsed = 0.0             # tempo total desde o lançamento
        self._explosion_elapsed = 0.0   # tempo desde que começou a explosão

        # para garantir que o dano em área só é aplicado uma vez
        self.damage_applied = False

    # ------------------------------------------------------------------ #
    # API principal
    # ------------------------------------------------------------------ #

    def update(self, dt):
        """
        Atualiza a lógica da granada.
        dt em segundos (ex: 0.016 para ~60 FPS).
        """
        if not self.alive:
            return

        self._elapsed += dt

        if self.state == self.STATE_FLYING:
            # aplica gravidade
            self.vy += self.gravity * dt

            # atualiza posição
            self.x += self.vx * dt
            self.y += self.vy * dt

            # --- impacto com o "chão" (fundo do ecrã) ---
            try:
                ground_y = float(getattr(config, "HEIGHT", 0))
            except Exception:
                ground_y = 0.0

            if ground_y > 0:
                # quando o centro da granada passa do chão → explode por impacto
                if self.y >= ground_y - self.flight_radius:
                    self.y = ground_y - self.flight_radius
                    self.explode()
                    # não queremos fuse nesse frame depois de já ter explodido
                    return

            # --- fuse temporizado (apenas se NÃO for granada de boss) ---
            if not getattr(self, "impact_only", False):
                if self._elapsed >= self.fuse_time:
                    self.explode()

        elif self.state == self.STATE_EXPLODING:
            self._explosion_elapsed += dt
            if self._explosion_elapsed >= self.explosion_duration:
                # já acabou a animação da explosão
                self.state = self.STATE_DEAD
                self.alive = False

    def explode(self):
        """
        Passa para o estado de explosão.
        O dano em área é tratado fora (no game_state) usando
        explosion_radius e damage.
        """
        if self.state != self.STATE_FLYING:
            return

        self.state = self.STATE_EXPLODING
        self._explosion_elapsed = 0.0

    def mark_for_removal(self):
        """
        Marca explicitamente como morta, caso precises.
        """
        self.state = self.STATE_DEAD
        self.alive = False

    # ------------------------------------------------------------------ #
    # Helpers para o resto do jogo
    # ------------------------------------------------------------------ #

    def is_flying(self):
        return self.state == self.STATE_FLYING

    def is_exploding(self):
        return self.state == self.STATE_EXPLODING

    def is_dead(self):
        return (not self.alive) or self.state == self.STATE_DEAD

    def get_center(self):
        """
        Devolve as coordenadas (x, y) atuais (em floats).
        Para desenhar, fazes cast para int.
        """
        return self.x, self.y

    def get_draw_data(self):
        """
        Devolve info mínima para o desenho.

        Retorna:
          - None se estiver morta
          - dict com:
              {
                "x": float,
                "y": float,
                "radius": int,
                "exploding": bool
              }
        """
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
