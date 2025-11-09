import pygame
import random
import sys
import cv2
import mediapipe as mp
import threading
import queue
import math

WIDTH, HEIGHT = 900, 300
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game")

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
            self.y = GROUND_Y - 70
            self.color = (120, 0, 0)

    def update(self, dt):
        self.x -= self.speed * dt

    def draw(self, win):
        pygame.draw.rect(win, self.color, (self.x, self.y, self.w, self.h), border_radius=4)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)


def detect_gestures(data_queue, stop_event):
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.5)
    mp_draw = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Kamera yok.")
        cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            print("HATA")
            return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

    pinch_state = False
    fist_state = False

    while not stop_event.is_set():
        success, image = cap.read()
        if not success:
            continue

        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)

        current_pinch = False
        current_fist = False
        display_text = "NORMAL"
        gesture_command = None 

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            landmarks = hand_landmarks.landmark

            try:
                index_tip_y = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP].y
                index_pip_y = landmarks[mp_hands.HandLandmark.INDEX_FINGER_PIP].y
                middle_tip_y = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y
                middle_pip_y = landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].y
                ring_tip_y = landmarks[mp_hands.HandLandmark.RING_FINGER_TIP].y
                ring_pip_y = landmarks[mp_hands.HandLandmark.RING_FINGER_PIP].y
                pinky_tip_y = landmarks[mp_hands.HandLandmark.PINKY_TIP].y
                pinky_pip_y = landmarks[mp_hands.HandLandmark.PINKY_PIP].y

                if (index_tip_y > index_pip_y and middle_tip_y > middle_pip_y and
                    ring_tip_y > ring_pip_y and pinky_tip_y > pinky_pip_y):
                    current_fist = True
                    display_text = "YUMRUK (EGIL)"
            except: pass

            try: 
                thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
                index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                distance = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
                if distance < 0.05:
                    current_pinch = True
                    display_text = "CIMDIK (ZIPLA)"
            except: pass
            
            mp_draw.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        if current_pinch and not pinch_state:
            gesture_command = "JUMP"
        pinch_state = current_pinch

        if current_fist and not fist_state:
            gesture_command = "DUCK"
        elif not current_fist and fist_state:
            gesture_command = "STAND"
        fist_state = current_fist

        if not results.multi_hand_landmarks and fist_state:
            gesture_command = "STAND"
            fist_state = False

        try:
            data_queue.put_nowait((image, display_text, gesture_command))
        except queue.Full:
            pass

    cap.release()

def main():
    pygame.init()
    WIN = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Game")
    CLOCK = pygame.time.Clock()
    GROUND_Y = HEIGHT - 50

    dino = Dino()
    obstacles = []
    speed = 350
    spawn_timer = 0
    score = 0
    font = pygame.font.SysFont(None, 32)
    game_over = False

    data_queue = queue.Queue(maxsize=2) 
    cv_is_ducking = False

    stop_event = threading.Event()

    cv_thread = threading.Thread(
        target=detect_gestures, 
        args=(data_queue, stop_event), 
        daemon=True 
    )
    cv_thread.start()

    running = True
    while running:
        dt = CLOCK.tick(60) / 1000
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        try:
            frame, gesture_text, gesture_command = data_queue.get_nowait()
            
            if not game_over:
                if gesture_command == "JUMP":
                    dino.jump()
                elif gesture_command == "DUCK":
                    cv_is_ducking = True
                elif gesture_command == "STAND":
                    cv_is_ducking = False
            
            cv2.putText(frame, gesture_text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.imshow("Kontrol", frame)

        except queue.Empty:
            pass 
        if cv2.waitKey(1) & 0xFF == 27:
            running = False
        if not game_over:
            if keys[pygame.K_SPACE]:
                dino.jump()
            
            if keys[pygame.K_s] or cv_is_ducking:
                dino.duck(True)
            else:
                dino.duck(False)
        else:
            if keys[pygame.K_r]:
                dino = Dino()
                obstacles = []
                speed = 350
                spawn_timer = 0
                score = 0
                game_over = False
                cv_is_ducking = False

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

    stop_event.set() 
    pygame.quit()
    cv2.destroyAllWindows()
    sys.exit()

if __name__ == "__main__":
    main()