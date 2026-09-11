import pygame
import os

# Colores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
ORANGE = (255, 165, 0)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
CYAN = (0, 255, 255)

class FrameButton:
    """Botón transparente con esquinas redondeadas y borde blanco"""
    def __init__(self, x, y, w, h, text, action_code, use_image=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action = action_code
        self.hover = False
        self.scale = 1.0
        self.target_scale = 1.0
        self.image = None
        
        # Cargar imagen si se especifica
        if use_image:
            try:
                path = f"assets/ui/buttons/{use_image}"
                if os.path.exists(path):
                    raw = pygame.image.load(path).convert_alpha()
                    self.image = pygame.transform.scale(raw, (w, h))
            except Exception as e:
                print(f"Button image load error: {e}")
        
    def draw(self, screen, font):
        # Animación de escala suave
        self.scale += (self.target_scale - self.scale) * 0.3

        # Calcular el rectángulo escalado
        scaled_w = int(self.rect.w * self.scale)
        scaled_h = int(self.rect.h * self.scale)
        scaled_rect = pygame.Rect(
            self.rect.centerx - scaled_w // 2,
            self.rect.centery - scaled_h // 2,
            scaled_w,
            scaled_h
        )
        
        if self.image:
            # Usar el asset de imagen
            if self.scale != 1.0:
                scaled_img = pygame.transform.scale(self.image, (scaled_w, scaled_h))
                screen.blit(scaled_img, scaled_rect)
            else:
                screen.blit(self.image, scaled_rect)
        else:
            # Botón transparente con borde blanco y esquinas redondeadas
            if self.hover:
                # Brillo sutil
                glow_surf = pygame.Surface((scaled_w + 10, scaled_h + 10), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*WHITE, 30), glow_surf.get_rect(), border_radius=10)
                screen.blit(glow_surf, (scaled_rect.x - 5, scaled_rect.y - 5))

            # Dibujar solo el borde (fondo transparente)
            pygame.draw.rect(screen, WHITE, scaled_rect, 2, border_radius=10)

            # Texto
            txt_surf = font.render(self.text, True, WHITE)
            text_rect = txt_surf.get_rect(center=scaled_rect.center)
            screen.blit(txt_surf, text_rect)
    
    def check_hover(self, mx, my):
        self.hover = self.rect.collidepoint(mx, my)
        self.target_scale = 1.05 if self.hover else 1.0
        return self.hover
    
    def check_click(self, mx, my, click):
        if self.rect.collidepoint(mx, my) and click:
            self.target_scale = 0.95  # Retroalimentación visual del clic
            return self.action
        return None

class SceneManager:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.current_scene = "MENU"
        self.scene_stack = []  # Para navegación
        self.is_paused = False
        
        self.font_big = pygame.font.Font(None, 80)
        self.font_med = pygame.font.Font(None, 50)
        self.font_small = pygame.font.Font(None, 30)
        
        cy = height // 2

        # Menú
        # Nota: antes se usaba un asset "btn_play.png" con "PLAY" incrustado en la
        # imagen, lo que ignoraba self.text por completo. Renderizarlo como un
        # botón normal con borde en su lugar lo mantiene sincronizado con la etiqueta (y con
        # cualquier futuro cambio de idioma) y coincide con el estilo de los demás botones.
        self.btn_play = self._single_button(cy + 50, 80, self.font_med, "JUGAR", "GOTO_MODE")

        # Selección de modo - el ancho se ajusta a cada etiqueta, para que las palabras largas en español no se superpongan
        self.btn_classic, self.btn_survival = self._button_row(
            cy + 20, 60, self.font_med,
            [("CLÁSICO", "MODE_CLASSIC"), ("SUPERVIVENCIA", "MODE_SURVIVAL")]
        )
        self.btn_back_mode = self._single_button(cy + 120, 50, self.font_small, "ATRÁS", "BACK")

        # Selección de control
        self.btn_mouse, self.btn_hand = self._button_row(
            cy + 20, 60, self.font_med,
            [("RATÓN", "INPUT_MOUSE"), ("CÁMARA", "INPUT_HAND")]
        )
        self.btn_back_input = self._single_button(cy + 120, 50, self.font_small, "ATRÁS", "BACK")

        # Menú de pausa (estilo marco)
        self.btn_resume = self._single_button(cy - 40, 60, self.font_med, "REANUDAR", "RESUME")
        self.btn_back_pause = self._single_button(cy + 40, 60, self.font_med, "ATRÁS", "BACK")

        # Fin del juego (estilo marco)
        self.btn_replay, self.btn_home = self._button_row(
            cy + 100, 60, self.font_med,
            [("REINTENTAR", "RESTART"), ("INICIO", "GOTO_MENU")]
        )

    def _button_width(self, font, text, padding=50, min_width=170):
        """Ajusta el tamaño de un botón a su etiqueta en lugar de un valor fijo,
        para que el texto traducido de cualquier longitud nunca desborde su caja."""
        return max(min_width, font.size(text)[0] + padding)

    def _single_button(self, y, height, font, text, action, padding=50, min_width=170):
        w = self._button_width(font, text, padding, min_width)
        x = self.width // 2 - w // 2
        return FrameButton(x, y, w, height, text, action)

    def _button_row(self, y, height, font, items, gap=24, padding=50, min_width=170):
        """Coloca varios botones lado a lado, cada uno ajustado a su propia etiqueta,
        centrados como grupo para que la fila quede equilibrada sin importar la longitud."""
        widths = [self._button_width(font, text, padding, min_width) for text, _ in items]
        total_width = sum(widths) + gap * (len(items) - 1)
        x = self.width // 2 - total_width // 2

        buttons = []
        for (text, action), w in zip(items, widths):
            buttons.append(FrameButton(x, y, w, height, text, action))
            x += w + gap
        return buttons
    
    def push_scene(self, scene):
        """Apila la escena actual antes de cambiarla"""
        if self.current_scene not in self.scene_stack:
            self.scene_stack.append(self.current_scene)
        self.current_scene = scene
    
    def pop_scene(self):
        """Vuelve a la escena anterior"""
        if self.scene_stack:
            self.current_scene = self.scene_stack.pop()
            return True
        return False

    def draw_menu(self, screen):
        # Título
        title = self.font_big.render("FRUIT NINJA V3", True, ORANGE)
        screen.blit(title, (self.width//2 - title.get_width()//2, 100))

        sub = self.font_small.render("¡Corta frutas con tu mano o el ratón!", True, WHITE)
        screen.blit(sub, (self.width//2 - sub.get_width()//2, 180))

        # Botón dibujado al final (encima)
        self.btn_play.draw(screen, self.font_med)

    def draw_mode_select(self, screen):
        # Título primero
        title = self.font_med.render("SELECCIONA UN MODO", True, WHITE)
        screen.blit(title, (self.width//2 - title.get_width()//2, 100))

        # Botones dibujados al final (encima de todo)
        self.btn_classic.draw(screen, self.font_med)
        self.btn_survival.draw(screen, self.font_med)
        self.btn_back_mode.draw(screen, self.font_small)

    def draw_input_select(self, screen):
        # Título primero
        title = self.font_med.render("SELECCIONA EL CONTROL", True, WHITE)
        screen.blit(title, (self.width//2 - title.get_width()//2, 100))

        # Botones dibujados al final (encima)
        self.btn_mouse.draw(screen, self.font_med)
        self.btn_hand.draw(screen, self.font_med)
        self.btn_back_input.draw(screen, self.font_small)


    def draw_pause(self, screen):
        # Superposición oscura
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        title = self.font_big.render("PAUSA", True, ORANGE)
        screen.blit(title, (self.width//2 - title.get_width()//2, 150))

        self.btn_resume.draw(screen, self.font_med)
        self.btn_back_pause.draw(screen, self.font_med)

    def draw_game_over(self, screen, score):
        # Superposición oscura
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        title = self.font_big.render("FIN DEL JUEGO", True, RED)
        screen.blit(title, (self.width//2 - title.get_width()//2, 150))

        score_text = self.font_med.render(f"Puntos: {score}", True, WHITE)
        screen.blit(score_text, (self.width//2 - score_text.get_width()//2, 250))
        
        self.btn_replay.draw(screen, self.font_med)
        self.btn_home.draw(screen, self.font_med)

    def handle_input(self, scene, mx, my, click):
        if scene == "MENU":
            self.btn_play.check_hover(mx, my)
            return self.btn_play.check_click(mx, my, click)
        
        elif scene == "MODE_SEL":
            self.btn_classic.check_hover(mx, my)
            self.btn_survival.check_hover(mx, my)
            self.btn_back_mode.check_hover(mx, my)
            
            a1 = self.btn_classic.check_click(mx, my, click)
            a2 = self.btn_survival.check_click(mx, my, click)
            a3 = self.btn_back_mode.check_click(mx, my, click)
            return a1 or a2 or a3
        
        elif scene == "INPUT_SEL":
            self.btn_mouse.check_hover(mx, my)
            self.btn_hand.check_hover(mx, my)
            self.btn_back_input.check_hover(mx, my)
            
            a1 = self.btn_mouse.check_click(mx, my, click)
            a2 = self.btn_hand.check_click(mx, my, click)
            a3 = self.btn_back_input.check_click(mx, my, click)
            return a1 or a2 or a3
        
        elif scene == "PAUSE":
            self.btn_resume.check_hover(mx, my)
            self.btn_back_pause.check_hover(mx, my)
            
            a1 = self.btn_resume.check_click(mx, my, click)
            a2 = self.btn_back_pause.check_click(mx, my, click)
            return a1 or a2
        
        elif scene == "OVER":
            self.btn_replay.check_hover(mx, my)
            self.btn_home.check_hover(mx, my)
            
            a1 = self.btn_replay.check_click(mx, my, click)
            a2 = self.btn_home.check_click(mx, my, click)
            return a1 or a2
        
        return None
