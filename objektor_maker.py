import cv2
import mediapipe as mp
import numpy as np
import pygame
import time
import os

# Inicializace mediapipe ruky
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Inicializace pygame pro zvuk a fullscreen
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
width, height = screen.get_size()

# Načtení zvuku zásahu
sound_path = os.path.join(os.path.dirname(__file__), 'beep.wav')
hit_sound = pygame.mixer.Sound(sound_path)

# Nastavení hry
score = 0
best_score_file = os.path.join(os.path.dirname(__file__), 'best_score.txt')
best_score = 0

if os.path.exists(best_score_file):
    with open(best_score_file, 'r') as f:
        try:
            best_score = int(f.read())
        except:
            best_score = 0

font = pygame.font.SysFont("Arial", 40)

# Výběr obtížnosti
def select_difficulty():
    selecting = True
    while selecting:
        screen.fill((0, 0, 0))
        text1 = font.render("Stiskni A pro Snadnou obtížnost (30s)", True, (255, 255, 255))
        text2 = font.render("Stiskni S pro Střední obtížnost (45s)", True, (255, 255, 255))
        text3 = font.render("Stiskni D pro Těžkou obtížnost (60s)", True, (255, 255, 255))
        screen.blit(text1, (50, height//3))
        screen.blit(text2, (50, height//3 + 60))
        screen.blit(text3, (50, height//3 + 120))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    return 30
                elif event.key == pygame.K_s:
                    return 45
                elif event.key == pygame.K_d:
                    return 60
            elif event.type == pygame.QUIT:
                pygame.quit()
                exit()


# Hlavní hra
def game_loop(duration_sec):
    global score, best_score
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)

    start_time = time.time()
    running = True

    target_radius = 50
    target_x = np.random.randint(target_radius, width - target_radius)
    target_y = np.random.randint(target_radius, height - target_radius)

    while running:
        elapsed = time.time() - start_time
        if elapsed > duration_sec:
            running = False

        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)

        screen.fill((30, 30, 30))  # pozadí

        # Malý náhled kamery vlevo nahoře
        small_frame = cv2.resize(frame, (350, 230))
        small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        small_surf = pygame.surfarray.make_surface(small_frame.swapaxes(0, 1))
        screen.blit(small_surf, (10, 10))

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        hand_x, hand_y = None, None

        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                lm = handLms.landmark[8]  # ukazováček
                hand_x = int(lm.x * width)
                hand_y = int(lm.y * height)
                # mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)  # pokud chceš zobrazit kostru ruky

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                    break

        # Vykresli cíl
        pygame.draw.circle(screen, (255, 0, 0), (target_x, target_y), target_radius)

        # Vykresli ukazatel ruky
        if hand_x is not None and hand_y is not None:
            pygame.draw.circle(screen, (0, 255, 0), (hand_x, hand_y), 20)

            # Zkontroluj zásah
            dist = np.hypot(hand_x - target_x, hand_y - target_y)
            if dist < target_radius + 20:
                score += 1
                hit_sound.play()
                target_x = np.random.randint(target_radius, width - target_radius)
                target_y = np.random.randint(target_radius, height - target_radius)
                time.sleep(0.2)

        # Vykresli skóre a čas
        score_text = font.render(f"Skóre: {score}", True, (255, 255, 255))
        screen.blit(score_text, (20, 20))

        time_left = max(0, int(duration_sec - elapsed))
        time_text = font.render(f"Čas: {time_left}s", True, (255, 255, 255))
        screen.blit(time_text, (width - 180, 20))

        best_text = font.render(f"Nejlepší skóre: {best_score}", True, (255, 255, 255))
        screen.blit(best_text, (20, height - 60))

        pygame.display.flip()

    cap.release()
    cv2.destroyAllWindows()

    if score > best_score:
        with open(best_score_file, 'w') as f:
            f.write(str(score))
        best_score = score

# Hlavní program
def main():
    global score
    while True:
        duration = select_difficulty()
        score = 0
        game_loop(duration)

        # Po skončení hry ukázat výsledky
        showing = True
        while showing:
            screen.fill((0, 0, 0))
            msg = font.render(f"Konec hry! Skóre: {score}", True, (255, 255, 255))
            msg2 = font.render("Stiskni R pro restart, Q pro ukončení", True, (255, 255, 255))
            screen.blit(msg, (width//3, height//3))
            screen.blit(msg2, (width//3, height//3 + 50))
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        showing = False
                    elif event.key == pygame.K_q:
                        pygame.quit()
                        return

if __name__ == "__main__":
    main()
