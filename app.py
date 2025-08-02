import random
import pygame
# Não importe pgzrun aqui, ele deve ser usado apenas para executar o jogo
from pygame import Rect

WIDTH = 1024
HEIGHT = 768
TITLE = "Aventura do Esqueleto"

# States
game_running = False
sound_on = True
sounds_available = False  # Set to False since we don't have sound files yet

# Background - usando os fundos disponíveis
background_layers = [
    "sky",
    "jungle_bg",
    "trees_and_bushes",
    "grass_and_road",
    "grasses"
]

# Ajustar o chão para a nova altura
ground_y = 600  # Nova posição do chão

# Music
music_file = "bg_music.ogg"
music_available = True  # Set to False since we don't have the music file yet

# Game variables
player_lives = 5
score = 0

# Animation helper
def animate_sprite(sprite_list, index, speed=0.1):
    index += speed
    if index >= len(sprite_list):
        index = 0
    return index

# Função para carregar imagens
def load_animation_images(prefix, count):
    # For now, just return the first frame repeated
    # This is a temporary solution until we have all frames
    return [f"{prefix}_000" for i in range(count)]

# -------------------------
# Sprite Classes
# -------------------------

class Player:
    def __init__(self):
        # Carregando as imagens do herói (Skeleton Warrior)
        self.images_idle = load_animation_images("skeleton_idle", 18)
        self.images_run = load_animation_images("skeleton_run", 12)
        self.images_jump = load_animation_images("skeleton_jump", 6)
        self.images_hurt = load_animation_images("skeleton_hurt", 12)
        self.images_dying = load_animation_images("skeleton_dying", 15)
        self.images_kick = load_animation_images("skeleton_kick", 13)
        self.images_slash = load_animation_images("skeleton_slash", 12)
        self.index = 0
        self.actor = Actor(self.images_idle[0], (100, 460))
        self.actor.scale = 1.01  # Reduzindo o tamanho do personagem
        self.vel_y = 0
        self.on_ground = False
        self.rect = Rect(self.actor.x - 15, self.actor.y - 30, 30, 60)  # Retângulo de colisão normal
        self.attack_rect = Rect(0, 0, 0, 0)  # Retângulo de colisão para ataques (será atualizado)
        self.is_hurt = False
        self.hurt_timer = 0
        self.invincible = False
        self.invincible_timer = 0
        self.is_kicking = False
        self.kick_timer = 0
        self.is_slashing = False
        self.slash_timer = 0
        self.direction = 1  # 1 para direita, -1 para esquerda
        self.is_dying = False
        self.dying_timer = 0

    def update(self, keys):
        self.vel_y += 0.5
        self.actor.y += self.vel_y

        if self.is_dying:
            self.dying_timer += 1
            self.index = animate_sprite(self.images_dying, self.index, 0.2)
            self.actor.image = self.images_dying[int(self.index)]
            
            # Após 1 segundo (60 frames), resetar
            if self.dying_timer > 60:
                reset_game()
                globals()['game_running'] = False  # Modificar a variável global corretamente
            return  # Não atualizar mais nada se estiver morrendo

        # Verificar se o player passou do final da tela
        if self.actor.x > WIDTH:
            self.actor.x = 0  # volta para o início da tela
            
            # Resetar inimigos com posições aleatórias
            enemies.clear()
            for _ in range(3):
                x = random.randint(300, 900)
                min_x = max(100, x - 100)
                max_x = min(WIDTH - 100, x + 100)
                enemies.append(Enemy(x, (min_x, max_x)))

        elif self.actor.x < 0:
            
            # Resetar inimigos com posições aleatórias
            self.actor.x = WIDTH  # permite também voltar da esquerda para direita

        # Gravity
        if self.actor.y > 460:  # Nova posição do chão
            self.actor.y = 460
            self.vel_y = 0
            self.on_ground = True

        # Atualizar o retângulo de colisão normal
        self.rect.topleft = (self.actor.x - 15, self.actor.y - 30)
        
        # Resetar o retângulo de ataque (sem colisão por padrão)
        self.attack_rect = Rect(0, 0, 0, 0)

        # Verificar se está em estado de dano
        if self.is_hurt:
            self.hurt_timer += 1
            self.index = animate_sprite(self.images_hurt, self.index, 0.2)
            self.actor.image = self.images_hurt[int(self.index)]
            if self.hurt_timer > 30:  # Aproximadamente 0.5 segundos
                self.is_hurt = False
                self.hurt_timer = 0
        # Verificar se está chutando
        elif self.is_kicking:
            self.kick_timer += 1
            self.index = animate_sprite(self.images_kick, self.index, 0.2)
            self.actor.image = self.images_kick[int(self.index)]
            
            # Criar um retângulo de ataque maior para o chute
            # Usar a direção armazenada do jogador
            direction = self.direction  # -1 para esquerda, 1 para direita
            attack_width = 80  # Largura do ataque
            attack_x = self.actor.x + (20 * direction) if direction > 0 else self.actor.x - attack_width + 20
            self.attack_rect = Rect(attack_x, self.actor.y - 30, attack_width, 60)
            if self.kick_timer > 30:  # Aproximadamente 0.5 segundos
                self.is_kicking = False
                self.kick_timer = 0
        # Verificar se está atacando com espada
        elif self.is_slashing:
            self.slash_timer += 1
            self.index = animate_sprite(self.images_slash, self.index, 0.2)
            self.actor.image = self.images_slash[int(self.index)]
            
            # Criar um retângulo de ataque maior para o ataque com espada
            # Usar a direção armazenada do jogador
            direction = self.direction  # -1 para esquerda, 1 para direita
            attack_width = 100  # Largura do ataque (maior que o chute)
            attack_x = self.actor.x + (20 * direction) if direction > 0 else self.actor.x - attack_width + 20
            self.attack_rect = Rect(attack_x, self.actor.y - 30, attack_width, 60)
            
            if self.slash_timer > 30:  # Aproximadamente 0.5 segundos
                self.is_slashing = False
                self.slash_timer = 0
        else:
            if keys.left:
                self.actor.x -= 4
                self.index = animate_sprite(self.images_run, self.index, 0.2)
                self.actor.image = self.images_run[int(self.index)]
                # Atualizar a direção do jogador
                self.direction = -1
            elif keys.right:
                self.actor.x += 4
                self.index = animate_sprite(self.images_run, self.index, 0.2)
                self.actor.image = self.images_run[int(self.index)]
                # Atualizar a direção do jogador
                self.direction = 1
            else:
                self.index = animate_sprite(self.images_idle, self.index, 0.1)
                self.actor.image = self.images_idle[int(self.index)]

            # Se estiver no ar, mostrar animação de pulo
            if not self.on_ground:
                self.index = animate_sprite(self.images_jump, self.index, 0.1)
                self.actor.image = self.images_jump[int(self.index)]

            # Permitir pular com a tecla UP ou SPACE
            if (keys.up or keys.space) and self.on_ground:
                self.vel_y = -20
                self.on_ground = False
                if sound_on and sounds_available:
                    try:
                        sounds.jump.play()
                    except:
                        pass
                        
            # Ativar chute com a tecla K
            if keys.k and not self.is_kicking and not self.is_slashing:
                self.is_kicking = True
                self.kick_timer = 0
                if sound_on and sounds_available:
                    try:
                        sounds.hit.play()
                    except:
                        pass
                        
            # Ativar ataque com espada com a tecla S
            if keys.s and not self.is_slashing and not self.is_kicking:
                self.is_slashing = True
                self.slash_timer = 0
                if sound_on and sounds_available:
                    try:
                        sounds.hit.play()
                    except:
                        pass

        self.rect.topleft = (self.actor.x - 20, self.actor.y - 40)

    def draw(self):
        self.actor.draw()


class Enemy:
    def __init__(self, x, territory):
        # Carregando as imagens do inimigo (Orc)
        self.images_idle = load_animation_images("orc_idle", 18)
        self.images_run = load_animation_images("orc_run", 12)
        self.images_hurt = load_animation_images("orc_hurt", 12)
        self.index = 0
        self.actor = Actor(self.images_idle[0], (x, 460))  # Nova posição do chão
        # self.actor.scale = 0.7  # Reduzindo o tamanho do personagem
        self.actor.scale = 1.01  # Reduzindo o tamanho do personagem
        self.direction = 1  # 1 para direita, -1 para esquerda
        self.territory = territory
        self.speed = 2
        self.rect = Rect(self.actor.x - 15, self.actor.y - 30, 30, 60)  # Ajustando o retângulo de colisão

    def update(self):
        self.actor.x += self.direction * self.speed

        if self.actor.x < self.territory[0] or self.actor.x > self.territory[1]:
            self.direction *= -1

        self.index = animate_sprite(self.images_run, self.index, 0.2)
        self.actor.image = self.images_run[int(self.index)]
        
        # Virar o sprite na direção correta
        # Nota: Não podemos usar flip_x diretamente no Actor do pgzero
        # Em vez disso, precisaríamos ter imagens separadas para cada direção
            
        self.rect.topleft = (self.actor.x - 20, self.actor.y - 40)

    def draw(self):
        self.actor.draw()


# -------------------------
# Game Functions
# -------------------------

def reset_game():
    global player, enemies, player_lives, score
    player = Player()
    enemies = [
        Enemy(400, (350, 550)),
        Enemy(800, (700, 950))
    ]
    player_lives = 5
    score = 0


def check_collision():
    global player_lives, game_running, score, enemies
    
    enemies_to_remove = []
    
    for enemy in enemies:
        # Verificar colisão com o retângulo de ataque quando o jogador está atacando
        if (player.is_kicking or player.is_slashing) and player.attack_rect.colliderect(enemy.rect):
            # Marcar o inimigo para remoção
            enemies_to_remove.append(enemy)
                
            # Aumentar a pontuação
            score += 1
            
            if sound_on and sounds_available:
                try:
                    sounds.hit.play()
                except:
                    pass
        # Verificar colisão normal quando o jogador não está atacando
        elif player.rect.colliderect(enemy.rect) and not player.invincible:
            if sound_on and sounds_available:
                try:
                    sounds.hit.play()
                except:
                    pass
            player.is_hurt = True
            player.vel_y = -5  # Pequeno salto ao ser atingido
            # Afastar o jogador do inimigo
            if player.actor.x < enemy.actor.x:
                player.actor.x -= 20
            else:
                player.actor.x += 20
                
            # Tornar o jogador invencível por um curto período
            player.invincible = True
            player.invincible_timer = 0
            
            # Reduzir vidas
            player_lives -= 1
            
            # Verificar se o jogo acabou
            if player_lives <= 0:
                player.is_dying = True
                player.dying_timer = 0
    
    # Remover os inimigos atingidos
    for enemy in enemies_to_remove:
        enemies.remove(enemy)
        
    # Adicionar novos inimigos se todos forem eliminados
    if len(enemies) <= 1:
        enemies.append(Enemy(350, (250, 550)))
        enemies.append(Enemy(400, (350, 550)))
        enemies.append(Enemy(800, (700, 950)))


# -------------------------
# Menu Buttons
# -------------------------

menu_buttons = [
    {"label": "Iniciar Jogo", "y": 200},
    {"label": "Som: Ligado", "y": 260},
    {"label": "Sair", "y": 320}
]

# Atualizar o texto do botão de som
def update_sound_button():
    menu_buttons[1]["label"] = "Som: Ligado" if sound_on else "Som: Desligado"


# -------------------------
# PGZero Hooks
# -------------------------

def draw():
    screen.clear()
    
    # Desenhar camadas de fundo para criar profundidade
    for layer in background_layers:
        screen.blit(layer, (0, 0))
        
    # Desenhar linha do chão para referência visual
    screen.draw.line((0, ground_y), (WIDTH, ground_y), (100, 100, 100))

    if not game_running:
        screen.draw.text("AVENTURA DO ESQUELETO", center=(WIDTH//2, 100), fontsize=50, color="white", shadow=(1, 1), scolor="black")
        
        for btn in menu_buttons:
            # Criar efeito de hover nos botões
            mouse_pos = pygame.mouse.get_pos()
            btn_rect = Rect(WIDTH//2 - 100, btn["y"], 200, 40)
            btn_color = "orange" if btn_rect.collidepoint(mouse_pos) else "white"
            
            screen.draw.filled_rect(btn_rect, btn_color)
            screen.draw.rect(btn_rect, "black")
            screen.draw.text(
                btn["label"],
                center=(WIDTH//2, btn["y"] + 20),
                fontsize=20,
                color="black"
            )
            
        # Mostrar pontuação máxima se houver
        if score > 0:
            screen.draw.text(f"Pontuação Máxima: {int(score)}", center=(WIDTH//2, 400), fontsize=25, color="white")
    else:
        # Desenhar jogador com efeito de piscar quando invencível
        if not player.invincible or (player.invincible and player.invincible_timer % 10 < 5):
            player.draw()
            
        # Desenhar inimigos
        for enemy in enemies:
            enemy.draw()
            
        # Mostrar vidas e pontuação
        screen.draw.text(f"Vidas: {player_lives}", topleft=(20, 20), fontsize=30, color="white", shadow=(1, 1), scolor="black")
        screen.draw.text(f"Pontuacao: {int(score)}", topleft=(WIDTH - 200, 20), fontsize=30, color="white", shadow=(1, 1), scolor="black")


def update():
    global score
    
    if game_running:
        keys = keyboard
        player.update(keys)
        
        # Atualizar temporizador de invencibilidade
        if player.invincible:
            player.invincible_timer += 1
            if player.invincible_timer > 60:  # Aproximadamente 1 segundo
                player.invincible = False
        
        for enemy in enemies:
            enemy.update()
        
        check_collision()
        
        # A pontuação só aumenta quando acertar um inimigo (na função check_collision)



def on_mouse_down(pos):
    global game_running, sound_on
    if not game_running:
        for btn in menu_buttons:
            r = Rect(WIDTH//2 - 100, btn["y"], 200, 40)
            if r.collidepoint(pos):
                if btn["label"] == "Iniciar Jogo":
                    game_running = True
                    reset_game()
                    if sound_on and music_available:
                        try:
                            music.play(music_file)
                            music.set_volume(0.4)
                        except:
                            pass
                elif "Som:" in btn["label"]:
                    sound_on = not sound_on
                    update_sound_button()
                    if not sound_on:
                        music.stop()
                    else:
                        if game_running and music_available:
                            try:
                                music.play(music_file)
                            except:
                                pass
                elif btn["label"] == "Sair":
                    exit()


# Iniciar o jogo quando o script é executado diretamente
if __name__ == '__main__':
    music.set_volume(0.4)
    if music_available:
        music.play(music_file)
    print("=== INSTRUÇÕES PARA EXECUTAR O JOGO ===")
    print("O pgzero foi instalado com sucesso, mas este arquivo não deve ser executado diretamente com python.")
    print("\nPara executar o jogo, use um dos seguintes comandos no terminal:")
    print("1. pgzrun app.py")
    print("2. python -m pgzero app.py")
    print("=== BOA DIVERSÃO! ===")

