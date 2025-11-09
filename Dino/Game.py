import pygame
import random
import sys
import builtins
    
pygame.init()

WIDTH, HEIGHT = 900, 300
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dino Game")

CLOCK = pygame.time.Clock()
GROUND_Y = HEIGHT - 50

class Dino:
    def __init__(self):
        self.x = 60
        self.width = 40
        self.height = 50
        self.duck_width = 60
        self.duck_height = 35
        self.y = GROUND_Y - self.height
        self.vel_y = 0
        self.gravity = 1800
        self.jump_vel = -650
        self.is_ducking = False
        self.grounded = True

    def get_rect(self):
        if self.is_ducking and self.grounded:
            return pygame.Rect(self.x, GROUND_Y - self.duck_height, self.duck_width, self.duck_height)
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def jump(self):
        if self.grounded:
            self.vel_y = self.jump_vel
            self.grounded = False

    def duck(self, on):
        if self.grounded:
            self.is_ducking = on

    def update(self, dt):
        if not self.grounded:
            self.vel_y += self.gravity * dt
            self.y += self.vel_y * dt
            if self.y >= GROUND_Y - self.height:
                self.y = GROUND_Y - self.height
                self.vel_y = 0
                self.grounded = True

    def draw(self, win):
        rect = self.get_rect()
        pygame.draw.rect(win, (40, 40, 40), rect, border_radius=5)
        pygame.draw.rect(win, (255, 255, 255), (rect.x + rect.width - 12, rect.y + 12, 7, 7))


class Obstacle:
    def __init__(self, speed):
        self.speed = speed
        self.type = random.choice(["cactus", "bird_low"])

        if self.type == "cactus":
            self.w = 40
            self.h = 50
            self.x = WIDTH + 50
            self.y = GROUND_Y - self.h
            self.color = (0, 120, 0)

        elif self.type == "bird_low":
            self.w = 40
            self.h = 28
            self.x = WIDTH + 50
            self.y = GROUND_Y - 90  
            self.w = 40
            self.h = 28
            self.x = WIDTH + 50
            self.y = GROUND_Y - 70  
            self.color = (120, 0, 0)

        

    def update(self, dt):
        self.x -= self.speed * dt

    def draw(self, win):
        pygame.draw.rect(win, self.color, (self.x, self.y, self.w, self.h), border_radius=4)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)


def main():
    dino = Dino()
    obstacles = []

    speed = 350
    spawn_timer = 0
    score = 0

    font = pygame.font.SysFont(None, 32)
    game_over = False

    def cv_jump():
        dino.jump()

    def cv_duck(on=True):
        dino.duck(on)

    builtins.cv_jump = cv_jump
    builtins.cv_duck = cv_duck

    while True:
        dt = CLOCK.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        keys = pygame.key.get_pressed()

        if not game_over:
            if keys[pygame.K_SPACE]:
                dino.jump()
            if keys[pygame.K_s]:
                dino.duck(True)
            else:
                dino.duck(False)
        else:
            if keys[pygame.K_r]:
                return main()

        if not game_over:
            spawn_timer += dt
            if spawn_timer > random.uniform(1.0, 1.8):
                spawn_timer = 0
                obstacles.append(Obstacle(speed))

        if not game_over:
            dino.update(dt)
            for obs in obstacles:
                obs.update(dt)

            obstacles = [o for o in obstacles if o.x > -100]

            d_rect = dino.get_rect()
            for obs in obstacles:
                if d_rect.colliderect(obs.get_rect()):
                    game_over = True

            score += dt * 10
            speed = min(800, 350 + score * 0.8)

        WIN.fill((240, 240, 240))
        pygame.draw.line(WIN, (60, 60, 60), (0, GROUND_Y), (WIDTH, GROUND_Y), 2)

        dino.draw(WIN)
        for obs in obstacles:
            obs.draw(WIN)

        WIN.blit(font.render(f"SCORE: {int(score)}", True, (0, 0, 0)), (10, 10))

        if game_over:
            go_text = font.render("RESTART - R", True, (180, 0, 0))
            WIN.blit(go_text, (WIDTH//2 - go_text.get_width()//2, HEIGHT//2 - 20))

        pygame.display.update()


if __name__ == "__main__":
    main()
