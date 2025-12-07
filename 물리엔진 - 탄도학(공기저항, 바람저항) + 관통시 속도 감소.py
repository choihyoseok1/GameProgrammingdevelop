import pygame
import math

# --- 설정값 (Configuration) ---
WIDTH, HEIGHT = 1200, 800
FPS = 60

# [물리 환경 변수]
GRAVITY = pygame.math.Vector2(0, 300) # 중력 가속도 (아래 방향)
WIND_FORCE = pygame.math.Vector2(150, 0)  # 바람의 힘 (오른쪽으로)

# 색상
BLACK = (20, 20, 30)
WHITE = (255, 255, 255)
RED = (255, 100, 100)
YELLOW = (255, 255, 0)
BLUE = (100, 100, 255)
WALL_COLOR = (180, 180, 180) # 벽 색상

class Projectile:
    def __init__(self, x, y, angle, speed, radius, color, mass, drag_coefficient=0.005):
        self.pos = pygame.math.Vector2(x, y)
        self.radius = radius
        self.color = color
        self.mass = mass
        self.drag_coefficient = drag_coefficient
        self.alive = True
        self.path = [] # 궤적 점들을 저장할 리스트
        self.penetrated_walls = [] # 관통한 벽을 기록하는 리스트

        # 초기 속도
        rad = math.radians(angle)
        self.vel = pygame.math.Vector2(math.cos(rad), math.sin(rad)) * speed
        
    def update(self, dt, walls): # walls 인자 추가
        # 공기 저항 계산 (F_drag = -k * v^2)
        speed = self.vel.length()
        drag_force = pygame.math.Vector2(0, 0)
        if speed > 0:
            drag_force = -self.vel.normalize() * self.drag_coefficient * speed**2
        
        drag_acceleration = drag_force / self.mass if self.mass > 0 else pygame.math.Vector2(0, 0)
        wind_acceleration = WIND_FORCE / self.mass if self.mass > 0 else pygame.math.Vector2(0, 0)
        total_acceleration = GRAVITY + drag_acceleration + wind_acceleration
        
        self.vel += total_acceleration * dt
        self.pos += self.vel * dt
        self.path.append(self.pos.copy())
            
        # 벽 충돌 처리
        for wall in walls:
            proj_rect = self.get_rect()
            if proj_rect.colliderect(wall):
                if self.mass <= 5.0:  # 가벼운 총알: 튕기기
                    overlap = proj_rect.clip(wall)
                    
                    if overlap.width < overlap.height: # 수평 충돌 (좌/우)
                        self.vel.x *= -0.85
                        if proj_rect.centerx < wall.centerx: self.pos.x -= overlap.width
                        else: self.pos.x += overlap.width
                    else: # 수직 충돌 (상/하)
                        self.vel.y *= -0.85
                        if proj_rect.centery < wall.centery: self.pos.y -= overlap.height
                        else: self.pos.y += overlap.height
                    
                    break # 한 프레임에 한 벽만 충돌 처리
                else:
                    # 무거운 총알: 관통 시 속도 저하
                    if wall not in self.penetrated_walls:
                        self.vel *= 0.6 # 속도를 60%로 줄임 (40% 감소)
                        self.penetrated_walls.append(wall)

        # 화면 밖으로 아주 멀리 나간 총알은 삭제 (메모리 관리)
        if not (-WIDTH/2 <= self.pos.x <= WIDTH * 1.5 and -HEIGHT/2 <= self.pos.y <= HEIGHT * 1.5):
            self.alive = False

    def draw(self, screen):
        bullet_length = self.radius * 3
        if self.vel.length() > 0.1:
            direction_vector = self.vel.normalize()
            tail_pos = self.pos - (direction_vector * bullet_length)
            line_thickness = int(self.radius * 0.7) if int(self.radius * 0.7) > 0 else 1
            pygame.draw.line(screen, self.color, self.pos, tail_pos, line_thickness)
        else:
            pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), int(self.radius / 2))

    def get_rect(self):
        return pygame.Rect(self.pos.x - self.radius, self.pos.y - self.radius, self.radius * 2, self.radius * 2)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Advanced Ballistics Simulation")
    clock = pygame.time.Clock()

    projectiles = []
    walls_enabled = True # 벽 활성화 상태를 저장하는 변수

    # 벽 생성 (중앙에 구멍이 있는 형태)
    walls = [
        pygame.Rect(600, 0, 30, HEIGHT / 2 - 70),
        pygame.Rect(600, HEIGHT / 2 + 70, 30, HEIGHT - (HEIGHT / 2 + 70))
    ]

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0 

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    walls_enabled = not walls_enabled
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                start_pos = pygame.math.Vector2(100, HEIGHT // 2)
                m_pos = pygame.math.Vector2(pygame.mouse.get_pos())
                angle = math.degrees(math.atan2(m_pos.y - start_pos.y, m_pos.x - start_pos.x))

                if event.button == 1:
                    p = Projectile(start_pos.x, start_pos.y, angle, 800, 10, RED, mass=10.0)
                    projectiles.append(p)
                
                elif event.button == 3:
                    p = Projectile(start_pos.x, start_pos.y, angle, 700, 5, YELLOW, mass=1.0)
                    projectiles.append(p)

        # Update
        active_walls = walls if walls_enabled else []
        for p in projectiles[:]:
            p.update(dt, active_walls) # 활성화 상태에 따라 walls 전달
            if not p.alive:
                projectiles.remove(p)

        # Draw
        screen.fill(BLACK)
        
        # 벽 그리기 (활성화된 경우에만)
        if walls_enabled:
            for wall in walls:
                pygame.draw.rect(screen, WALL_COLOR, wall)
        
        # 총알 그리기 및 궤적 표시
        for p in projectiles:
            if len(p.path) > 1:
                pygame.draw.lines(screen, p.color, False, p.path, 1)
            p.draw(screen)
        
        # 발사대
        pygame.draw.circle(screen, BLUE, (100, HEIGHT // 2), 20)

        # UI Info
        font = pygame.font.SysFont("Arial", 16)
        controls_text = "LMB: Fire Heavy Bullet | RMB: Fire Light Bullet"
        screen.blit(font.render(controls_text, True, WHITE), (10, 10))
        
        info_text = f"Projectiles: {len(projectiles)}"
        screen.blit(font.render(info_text, True, WHITE), (10, 30))
        
        wind_text = f"Wind Force: ({int(WIND_FORCE.x)}, {int(WIND_FORCE.y)})"
        screen.blit(font.render(wind_text, True, WHITE), (10, 50))

        wall_status_text = f"Walls: {'ON' if walls_enabled else 'OFF'} (Press 'W' to toggle)"
        screen.blit(font.render(wall_status_text, True, WHITE), (10, 70))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()