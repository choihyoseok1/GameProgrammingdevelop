import pygame
import math

WIDTH, HEIGHT = 1200, 800
FPS = 60

GRAVITY = pygame.math.Vector2(0, 300) 
WIND_VELOCITY = pygame.math.Vector2(150, 0)  

BLACK = (20, 20, 30)
WHITE = (255, 255, 255)
RED = (255, 100, 100)
YELLOW = (255, 255, 0)
BLUE = (100, 100, 255)
WALL_COLOR = (180, 180, 180)

class Bullet:
    def __init__(self, x, y, angle, speed, radius, color, mass, drag_coefficient=0.005):
        self.pos = pygame.math.Vector2(x, y)
        self.radius = radius
        self.color = color
        self.mass = mass
        self.drag_coefficient = drag_coefficient
        self.alive = True
        self.path = []
        self.penetrated_walls = [] 

        rad = math.radians(angle)
        self.vel = pygame.math.Vector2(math.cos(rad), math.sin(rad)) * speed
        self.vel -= WIND_VELOCITY
        
    def update(self, dt, walls): 
        speed = self.vel.length()
        drag_force = pygame.math.Vector2(0, 0)
        if speed > 0:
            drag_force = -self.vel.normalize() * self.drag_coefficient * speed**2
        
        drag_acceleration = drag_force / self.mass if self.mass > 0 else pygame.math.Vector2(0, 0)
        total_acceleration = GRAVITY + drag_acceleration
        
        self.vel += total_acceleration * dt
        self.pos += self.vel * dt
        self.path.append(self.pos.copy())

        prev_pos = self.pos.copy()   
        for wall in walls:
            proj_rect = self.get_rect()
            AABB_collision = proj_rect.colliderect(wall)
            RayCast_collision = wall.clipline(prev_pos, self.pos)
            if AABB_collision or RayCast_collision:
                if RayCast_collision:
                    self.pos = pygame.math.Vector2(RayCast_collision[0])
                    proj_rect = self.get_rect()

                if self.mass <= 5.0:
                    overlap = proj_rect.clip(wall)
                
                    if overlap.width == 0 and overlap.height == 0:
                        dx = abs(prev_pos.x - wall.centerx) - (wall.width / 2)
                        dy = abs(prev_pos.y - wall.centery) - (wall.height / 2)
                        if dx > dy: collision_side = 'x' 
                        else: collision_side = 'y'
                    elif overlap.width < overlap.height:
                        collision_side = 'x'
                    else:
                        collision_side = 'y'

                    if collision_side == 'x':
                        self.vel.x *= -0.85
                        if self.pos.x < wall.centerx: self.pos.x -= 2
                        else: self.pos.x += 2
                    else:
                        self.vel.y *= -0.85
                        if self.pos.y < wall.centery: self.pos.y -= 2
                        else: self.pos.y += 2

                        break
                else:
                    if wall not in self.penetrated_walls:
                        self.vel *= 0.6 
                        self.penetrated_walls.append(wall)

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

    Bullets = []
    walls_enabled = True 

    walls = [
        pygame.Rect(600, 0, 30, HEIGHT / 2),
        pygame.Rect(600, HEIGHT / 2 , 30, HEIGHT - (HEIGHT / 2 ))
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
                    p = Bullet(start_pos.x, start_pos.y, angle, 800, 10, RED, mass=10.0)
                    Bullets.append(p)
                
                elif event.button == 3:
                    p = Bullet(start_pos.x, start_pos.y, angle, 700, 5, YELLOW, mass=1.0)
                    Bullets.append(p)

        active_walls = walls if walls_enabled else []
        for p in Bullets[:]:
            p.update(dt, active_walls) 
            if not p.alive:
                Bullets.remove(p)

        screen.fill(BLACK)
        
        if walls_enabled:
            for wall in walls:
                pygame.draw.rect(screen, WALL_COLOR, wall)
        
        for p in Bullets:
            if len(p.path) > 1:
                pygame.draw.lines(screen, p.color, False, p.path, 1)
            p.draw(screen)
        
        pygame.draw.circle(screen, BLUE, (100, HEIGHT // 2), 20)

        font = pygame.font.SysFont("Arial", 16)
        controls_text = "LMB: Fire Heavy Bullet | RMB: Fire Light Bullet"
        screen.blit(font.render(controls_text, True, WHITE), (10, 10))
        
        info_text = f"Bullets: {len(Bullets)}"
        screen.blit(font.render(info_text, True, WHITE), (10, 30))
        
        wind_text = f"Wind Velocity: ({int(WIND_VELOCITY.x)}, {int(WIND_VELOCITY.y)})"
        screen.blit(font.render(wind_text, True, WHITE), (10, 50))

        wall_status_text = f"Walls: {'ON' if walls_enabled else 'OFF'} (Press 'W' to toggle)"
        screen.blit(font.render(wall_status_text, True, WHITE), (10, 70))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()