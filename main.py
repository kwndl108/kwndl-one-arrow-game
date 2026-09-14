import pygame
import sys
import math

pygame.init()

WIDTH, HEIGHT = 900, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("一箭又一箭 - 小白版")
clock = pygame.time.Clock()

# 颜色
BG = (245, 245, 245)
BOARD_BG = (255, 255, 255)
GRID_LINE = (200, 200, 200)
ARROW = (40, 80, 160)
ARROW_BLOCKED = (220, 60, 60)
TEXT = (30, 30, 30)
BUTTON = (70, 130, 180)
BUTTON_HOVER = (100, 160, 210)
WHITE = (255, 255, 255)

# 字体：如果中文显示成方框，把 simhei 换成 microsoftyahei
# 假设你粘贴的是 msyh.ttc
font_small = pygame.font.Font("simhei.ttf", 20)
font_mid = pygame.font.Font("simhei.ttf", 28)
font_big = pygame.font.Font("simhei.ttf", 48)

ROWS, COLS = 5, 5
CELL = 90
BOARD_X, BOARD_Y = 50, 80
BOARD_W = COLS * CELL
BOARD_H = ROWS * CELL

# 三个关卡，坐标(row, col, 方向)
# 方向：U上 D下 L左 R右
levels = [
    [
        (0, 0, 'U'), (1, 0, 'U'), (2, 0, 'U'),
        (4, 4, 'D'), (3, 4, 'D'), (2, 4, 'D'),
        (4, 0, 'L'), (4, 1, 'L'), (4, 2, 'L'),
        (0, 4, 'R'), (0, 3, 'R'), (0, 2, 'R'),
    ],
    [
        (0, 1, 'U'), (2, 1, 'U'), (4, 1, 'U'),
        (4, 3, 'D'), (2, 3, 'D'), (0, 3, 'D'),
        (0, 0, 'R'), (0, 2, 'R'), (0, 4, 'R'),
        (4, 4, 'L'), (4, 2, 'L'), (4, 0, 'L'),
    ],
    [
        (0, 0, 'R'), (0, 1, 'R'), (0, 2, 'R'), (0, 3, 'R'), (0, 4, 'R'),
        (4, 0, 'L'), (4, 1, 'L'), (4, 2, 'L'), (4, 3, 'L'), (4, 4, 'L'),
        (1, 1, 'U'), (2, 1, 'U'), (3, 1, 'U'),
        (1, 3, 'D'), (2, 3, 'D'), (3, 3, 'D'),
    ],
]


class Arrow:
    def __init__(self, row, col, direction):
        self.row = row
        self.col = col
        self.direction = direction
        self.alive = True
        self.x = BOARD_X + col * CELL + CELL // 2
        self.y = BOARD_Y + row * CELL + CELL // 2
        self.shake = 0.0
        self.blocked_flash = 0.0


state = "START"
current_level = 0
arrows = []
flying_arrows = []
mistakes = 5
MAX_MISTAKES = 5

start_btn = pygame.Rect(WIDTH // 2 - 100, 380, 200, 60)
restart_btn = pygame.Rect(600, 520, 180, 50)
next_btn = pygame.Rect(WIDTH // 2 - 100, 400, 200, 60)
retry_btn = pygame.Rect(WIDTH // 2 - 220, 400, 200, 60)
menu_btn = pygame.Rect(WIDTH // 2 + 20, 400, 200, 60)


def load_level(index):
    global current_level, arrows, flying_arrows, mistakes
    current_level = index
    mistakes = MAX_MISTAKES
    arrows = []
    flying_arrows = []
    for r, c, d in levels[index]:
        arrows.append(Arrow(r, c, d))


def draw_button(rect, text):
    mouse = pygame.mouse.get_pos()
    color = BUTTON_HOVER if rect.collidepoint(mouse) else BUTTON
    pygame.draw.rect(screen, color, rect, border_radius=10)
    label = font_mid.render(text, True, WHITE)
    screen.blit(label, (rect.centerx - label.get_width() // 2,
                        rect.centery - label.get_height() // 2))


def draw_arrow(surface, center, direction, color, offset=(0, 0)):
    cx = center[0] + offset[0]
    cy = center[1] + offset[1]
    size = 28

    if direction == 'U':
        start = (cx, cy + size)
        end = (cx, cy - size)
        left = (cx - 10, cy - size + 14)
        right = (cx + 10, cy - size + 14)
    elif direction == 'D':
        start = (cx, cy - size)
        end = (cx, cy + size)
        left = (cx - 10, cy + size - 14)
        right = (cx + 10, cy + size - 14)
    elif direction == 'L':
        start = (cx + size, cy)
        end = (cx - size, cy)
        left = (cx - size + 14, cy - 10)
        right = (cx - size + 14, cy + 10)
    else:  # R
        start = (cx - size, cy)
        end = (cx + size, cy)
        left = (cx + size - 14, cy - 10)
        right = (cx + size - 14, cy + 10)

    pygame.draw.line(surface, color, start, end, 6)
    pygame.draw.polygon(surface, color, [end, left, right])


def draw_board():
    pygame.draw.rect(screen, BOARD_BG, (BOARD_X, BOARD_Y, BOARD_W, BOARD_H), border_radius=10)
    for r in range(ROWS + 1):
        y = BOARD_Y + r * CELL
        pygame.draw.line(screen, GRID_LINE, (BOARD_X, y), (BOARD_X + BOARD_W, y), 2)
    for c in range(COLS + 1):
        x = BOARD_X + c * CELL
        pygame.draw.line(screen, GRID_LINE, (x, BOARD_Y), (x, BOARD_Y + BOARD_H), 2)


def get_arrow_at(pos):
    for a in arrows:
        if a.alive:
            if abs(pos[0] - a.x) <= CELL // 2 - 5 and abs(pos[1] - a.y) <= CELL // 2 - 5:
                return a
    return None


def is_blocked(arrow):
    r, c, d = arrow.row, arrow.col, arrow.direction

    if d == 'U':
        for rr in range(r - 1, -1, -1):
            if any(a.alive and a.row == rr and a.col == c for a in arrows):
                return True
    elif d == 'D':
        for rr in range(r + 1, ROWS):
            if any(a.alive and a.row == rr and a.col == c for a in arrows):
                return True
    elif d == 'L':
        for cc in range(c - 1, -1, -1):
            if any(a.alive and a.row == r and a.col == cc for a in arrows):
                return True
    elif d == 'R':
        for cc in range(c + 1, COLS):
            if any(a.alive and a.row == r and a.col == cc for a in arrows):
                return True

    return False


def try_click_arrow(a):
    global mistakes, state

    if is_blocked(a):
        a.shake = 0.4
        a.blocked_flash = 0.4
        mistakes -= 1
        if mistakes <= 0:
            mistakes = 0
            state = "GAME_OVER"
    else:
        a.alive = False
        flying_arrows.append(a)


def update_flying(dt):
    for a in flying_arrows[:]:
        speed = 800
        if a.direction == 'U':
            a.y -= speed * dt
        elif a.direction == 'D':
            a.y += speed * dt
        elif a.direction == 'L':
            a.x -= speed * dt
        elif a.direction == 'R':
            a.x += speed * dt

        if a.x < -CELL or a.x > WIDTH + CELL or a.y < -CELL or a.y > HEIGHT + CELL:
            flying_arrows.remove(a)


def draw_start():
    screen.fill(BG)
    title = font_big.render("一箭又一箭", True, TEXT)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))

    desc = font_small.render("点击箭头，让它朝自己的方向飞出；被挡住会扣失误。", True, TEXT)
    screen.blit(desc, (WIDTH // 2 - desc.get_width() // 2, 240))

    draw_button(start_btn, "开始游戏")


def draw_game():
    screen.fill(BG)
    draw_board()

    for a in arrows:
        if a.alive:
            color = ARROW_BLOCKED if a.blocked_flash > 0 else ARROW
            offset = (0, 0)
            if a.shake > 0:
                offset = (math.sin(pygame.time.get_ticks() * 0.05) * 8, 0)
            draw_arrow(screen, (a.x, a.y), a.direction, color, offset)

    for a in flying_arrows:
        draw_arrow(screen, (a.x, a.y), a.direction, ARROW)

    alive_count = sum(1 for a in arrows if a.alive)
    t1 = font_mid.render(f"关卡：{current_level + 1}/{len(levels)}", True, TEXT)
    t2 = font_small.render(f"剩余箭头：{alive_count}", True, TEXT)
    t3 = font_small.render(f"失误次数：{mistakes}/{MAX_MISTAKES}", True, TEXT)

    screen.blit(t1, (600, 100))
    screen.blit(t2, (600, 160))
    screen.blit(t3, (600, 200))

    draw_button(restart_btn, "重新开始")


def draw_overlay(title, buttons):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))

    t = font_big.render(title, True, WHITE)
    screen.blit(t, (WIDTH // 2 - t.get_width() // 2, 250))

    for rect, text in buttons:
        draw_button(rect, text)


def main():
    global state, current_level
    running = True

    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == "START":
                    if start_btn.collidepoint(event.pos):
                        load_level(0)
                        state = "PLAY"

                elif state == "PLAY":
                    if restart_btn.collidepoint(event.pos):
                        load_level(current_level)
                    else:
                        a = get_arrow_at(event.pos)
                        if a:
                            try_click_arrow(a)

                elif state == "LEVEL_CLEAR":
                    if next_btn.collidepoint(event.pos):
                        if current_level + 1 < len(levels):
                            load_level(current_level + 1)
                            state = "PLAY"
                        else:
                            state = "START"

                elif state == "GAME_OVER":
                    if retry_btn.collidepoint(event.pos):
                        load_level(current_level)
                        state = "PLAY"
                    elif menu_btn.collidepoint(event.pos):
                        state = "START"

        if state == "PLAY":
            update_flying(dt)

            for a in arrows:
                if a.shake > 0:
                    a.shake -= dt
                if a.blocked_flash > 0:
                    a.blocked_flash -= dt

            alive_count = sum(1 for a in arrows if a.alive)
            if alive_count == 0 and len(flying_arrows) == 0:
                state = "LEVEL_CLEAR"

        if state == "START":
            draw_start()
        elif state in ("PLAY", "LEVEL_CLEAR", "GAME_OVER"):
            draw_game()

            if state == "LEVEL_CLEAR":
                if current_level + 1 < len(levels):
                    draw_overlay(f"第 {current_level + 1} 关完成！", [(next_btn, "下一关")])
                else:
                    draw_overlay("全部通关！", [(next_btn, "回到开始")])

            elif state == "GAME_OVER":
                draw_overlay("失败！失误次数用完了", [
                    (retry_btn, "重玩本关"),
                    (menu_btn, "回到开始")
                ])

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()