import tkinter as tk
import random
import ctypes
import json
import os
import math
import threading
import sys
from tkinter import colorchooser, filedialog, messagebox
from PIL import Image, ImageTk
try:
    import pystray
    from pystray import MenuItem as item
    from PIL import Image, ImageDraw
    SYSTRAY_AVAILABLE = True
except ImportError:
    SYSTRAY_AVAILABLE = False
    print("[WARN] pystray库未安装，无法使用系统托盘功能")
    print("[INFO] 请运行: pip install pystray")

# ================== 默认配置 ==================
DEFAULT_CONFIG = {
    "color_start": (0, 220, 255),
    "color_end": (255, 0, 255),
    "particle_max_life": 30,
    "particle_speed": 0.3,
    "particle_size": 8,  # 增加默认大小使爱心更明显
    "spawn_count": 1,
    "trail_type": "circle",  # circle, star, heart, image, text
    "image_path": "",
    "text_content": "❤",  # 文字拖尾内容
    "text_size": 24,  # 文字大小
    "text_font": "Arial",  # 文字字体
    "text_opacity": 100,  # 文字透明度（0-100%）
    "text_rotation": 0,  # 文字旋转角度
    "text_shadow": False,  # 文字阴影效果
    "text_weight": "normal",  # 文字粗细
    "click_texts": "✨;🌟;💖;🎉;👍;😊;🎯;💫;🔥;⭐",  # 点击时显示的文字，用分号分隔
    "click_text_size": 36,  # 点击文字大小
    "click_text_opacity": 100,  # 点击文字透明度（0-100%）
    "click_animation": "float",  # 点击文字动画效果
    "click_direction": "center",  # 点击文字方向
    "click_duration": 100,  # 点击文字持续时间
    "only_when_moving": True,
    "trail_enabled": True,
    "always_trail": False,
    "click_effect_enabled": True,  # 点击效果开关
    "collision_enabled": False,  # 粒子碰撞效果
    "gravity_enabled": False,  # 粒子重力效果
    "follow_mouse": True,  # 粒子跟随鼠标
    "trail_particles": False,  # 粒子产生拖尾
    "rotation_speed": 1.0,  # 粒子旋转速度
    "opacity_mode": "linear",  # 透明度变化模式
    "particle_shape": "circle",  # 粒子形状
    "color_mode": "linear",  # 颜色过渡模式
    "rainbow_speed": 1.0,  # 彩虹色速度
    "random_colors": False,  # 随机颜色
    "auto_start": False,  # 开机启动
    "spawn_interval": 2  # 粒子生成间隔（帧数）
}

# ================== 全局配置 ==================
config = DEFAULT_CONFIG.copy()
CONFIG_FILE = "mouse_trail_config.json"

# 加载配置
def load_config():
    global config
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                # 确保所有配置项都存在
                for key in DEFAULT_CONFIG:
                    if key in loaded:
                        config[key] = loaded[key]
                print("[OK] 配置已加载")
    except Exception as e:
        print(f"[ERROR] 加载配置失败: {e}")

# 保存配置
def save_config():
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print("[OK] 配置已保存")
    except Exception as e:
        print(f"[ERROR] 保存配置失败: {e}")

# 加载现有配置
load_config()

# 配置快捷访问
COLOR_START = config["color_start"]
COLOR_END = config["color_end"]
PARTICLE_MAX_LIFE = config["particle_max_life"]
PARTICLE_SPEED = config["particle_speed"]
PARTICLE_SIZE = config["particle_size"]
SPAWN_COUNT = min(config["spawn_count"], 3)  # 限制最大粒子数量为3
TRAIL_TYPE = config["trail_type"]
IMAGE_PATH = config["image_path"]
TEXT_CONTENT = config["text_content"]
TEXT_SIZE = config.get("text_size", 24)
TEXT_FONT = config.get("text_font", "Arial")
TEXT_OPACITY = config.get("text_opacity", 100)
CLICK_TEXTS = config["click_texts"]
CLICK_TEXT_SIZE = config.get("click_text_size", 36)
CLICK_TEXT_OPACITY = config.get("click_text_opacity", 100)
CLICK_ANIMATION = config.get("click_animation", "float")
CLICK_DIRECTION = config.get("click_direction", "center")
CLICK_DURATION = config.get("click_duration", 100)
ONLY_WHEN_MOVING = config["only_when_moving"]
TRAIL_ENABLED = config["trail_enabled"]
ALWAYS_TRAIL = config["always_trail"]
CLICK_EFFECT_ENABLED = config["click_effect_enabled"]
COLLISION_ENABLED = config.get("collision_enabled", False)
GRAVITY_ENABLED = config.get("gravity_enabled", False)
FOLLOW_MOUSE = config.get("follow_mouse", True)
TRAIL_PARTICLES = config.get("trail_particles", False)
ROTATION_SPEED = config.get("rotation_speed", 1.0)
OPACITY_MODE = config.get("opacity_mode", "linear")
PARTICLE_SHAPE = config.get("particle_shape", "circle")
COLOR_MODE = config.get("color_mode", "linear")
RAINBOW_SPEED = config.get("rainbow_speed", 1.0)
RANDOM_COLORS = config.get("random_colors", False)
AUTO_START = config.get("auto_start", False)
SPAWN_INTERVAL = config.get("spawn_interval", 2)
RANDOM_COLORS = config.get("random_colors", False)
AUTO_START = config.get("auto_start", False)

user32 = ctypes.WinDLL('user32', use_last_error=True)

# 高DPI
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    user32.SetProcessDPIAware()

# 全局鼠标
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def get_cursor_pos():
    pt = POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

# 配置管理器
class ConfigManager:
    def __init__(self, screen_width=None, screen_height=None):
        self.last_mouse_pos = (0, 0)
        self.mouse_moving = False
        self.image_cache = None
        self.last_left_click_state = False
        self.click_particles = []  # 点击产生的粒子
        self.screen_width = screen_width
        self.screen_height = screen_height
        
    def is_mouse_moving(self, current_pos):
        if current_pos != self.last_mouse_pos:
            self.mouse_moving = True
        else:
            self.mouse_moving = False
        self.last_mouse_pos = current_pos
        return self.mouse_moving
    
    def should_spawn_particles(self):
        if not config["trail_enabled"]:
            return False
        if config["always_trail"]:
            return True
        if config["only_when_moving"]:
            return self.mouse_moving
        return True
    
    def load_image(self):
        if config["image_path"] and os.path.exists(config["image_path"]):
            try:
                img = Image.open(config["image_path"])
                img = img.resize((int(PARTICLE_SIZE * 3), int(PARTICLE_SIZE * 3)), Image.Resampling.LANCZOS)
                self.image_cache = ImageTk.PhotoImage(img)
                return True
            except Exception as e:
                print(f"[ERROR] 加载图片失败: {e}")
                return False
        return False
    
    def check_mouse_click(self):
        """检测鼠标左键点击"""
        try:
            # 获取鼠标左键状态
            left_button_state = user32.GetAsyncKeyState(0x01) & 0x8000
            
            # 检测按下事件
            if left_button_state and not self.last_left_click_state:
                self.last_left_click_state = True
                return True
            elif not left_button_state:
                self.last_left_click_state = False
            
            return False
        except:
            return False
    
    def get_click_texts(self):
        """获取点击文字列表"""
        if not config["click_texts"]:
            return ["✨", "🌟", "💖", "🎉", "👍"]
        
        texts = config["click_texts"].split(';')
        # 过滤空字符串
        texts = [text.strip() for text in texts if text.strip()]
        if not texts:
            return ["✨", "🌟", "💖", "🎉", "👍"]
        return texts
    
    def create_click_particle(self, x, y):
        """创建点击文字粒子"""
        if not config["click_effect_enabled"]:
            return None
        
        texts = self.get_click_texts()
        if texts:
            text = random.choice(texts)
            particle = ClickTextParticle(x, y, text, CLICK_TEXT_SIZE, TEXT_FONT, CLICK_TEXT_OPACITY, 
                                        self.screen_width, self.screen_height)
            self.click_particles.append(particle)
            return particle
        return None
    
    def update_click_particles(self):
        """更新点击粒子"""
        alive = []
        for p in self.click_particles:
            if p.update(self.screen_width, self.screen_height):
                alive.append(p)
        self.click_particles = alive
        return alive

# 粒子基类
class Particle:
    def __init__(self, x, y):
        self.x = x + random.uniform(-1.5, 1.5)
        self.y = y + random.uniform(-1.5, 1.5)
        self.vx = random.uniform(-PARTICLE_SPEED, PARTICLE_SPEED)
        self.vy = random.uniform(-PARTICLE_SPEED, PARTICLE_SPEED)
        self.life = PARTICLE_MAX_LIFE
        self.max_life = PARTICLE_MAX_LIFE
        self.size = PARTICLE_SIZE
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-5, 5)
        
        # 动画效果相关
        self.original_size = self.size
        self.pulse_phase = random.uniform(0, math.pi * 2)
        self.bounce_phase = random.uniform(0, math.pi * 2)
        self.original_x = self.x
        self.original_y = self.y
        
        # 重力效果
        self.gravity_vy = 0
        self.gravity_strength = 0.1

    def update(self, screen_width=None, screen_height=None):
        # 应用重力效果
        if config.get("gravity_enabled", False):
            self.gravity_vy += self.gravity_strength
            self.vy += self.gravity_vy * 0.1
        
        # 应用跟随鼠标效果
        if config.get("follow_mouse", True):
            # 轻微的向鼠标方向移动
            mx, my = get_cursor_pos()
            dx = mx - self.x
            dy = my - self.y
            distance = max(math.sqrt(dx*dx + dy*dy), 1)
            attraction_strength = 0.01
            self.vx += (dx / distance) * attraction_strength
            self.vy += (dy / distance) * attraction_strength
        
        # 应用碰撞效果（简单的边界反弹）
        if config.get("collision_enabled", False):
            # 使用传入的屏幕尺寸或默认值
            if screen_width is None:
                screen_width = 1920
            if screen_height is None:
                screen_height = 1080
            
            # 简单的边界检测和反弹
            if self.x <= 0 or self.x >= screen_width:
                self.vx *= -0.8  # 反弹并损失能量
            if self.y <= 0 or self.y >= screen_height:
                self.vy *= -0.8
        
        # 基础移动
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        
        # 应用旋转效果
        rotation_speed = config.get("rotation_speed", 1.0)
        self.rotation += self.rotation_speed * rotation_speed
        
        # 应用动画效果
        self.apply_animation_effects()
        
        return self.life > 0
    
    def apply_animation_effects(self):
        """应用动画效果"""
        opacity_mode = config.get("opacity_mode", "linear")
        particle_shape = config.get("particle_shape", "circle")
        
        # 根据透明度模式调整生命周期计算
        if opacity_mode == "fade_in":
            # 淡入效果：开始时透明，逐渐显现
            self.life_display = self.life / self.max_life
        elif opacity_mode == "fade_out":
            # 淡出效果：开始时明显，逐渐消失
            self.life_display = 1 - self.life / self.max_life
        elif opacity_mode == "pulse":
            # 脉冲效果：周期性变化
            pulse_speed = 0.1
            self.life_display = 0.5 + 0.5 * math.sin(self.life * pulse_speed + self.pulse_phase)
        else:  # linear
            # 线性效果：默认
            self.life_display = self.life / self.max_life
        
        # 根据粒子形状调整大小
        if particle_shape == "square":
            # 方形粒子：大小保持不变
            pass
        elif particle_shape == "triangle":
            # 三角形粒子：轻微的大小变化
            self.size = self.original_size * (0.8 + 0.4 * math.sin(self.life * 0.1))
        elif particle_shape == "diamond":
            # 菱形粒子：旋转时大小变化
            self.size = self.original_size * (0.7 + 0.6 * abs(math.sin(self.rotation * 0.01)))
        elif particle_shape == "hexagon":
            # 六边形粒子：轻微脉动
            self.size = self.original_size * (0.9 + 0.2 * math.sin(self.life * 0.05))
        else:  # circle
            # 圆形粒子：默认
            pass
        
        # 应用粒子拖尾效果
        if config.get("trail_particles", False):
            # 这里可以在后续扩展中实现粒子产生拖尾
            pass

    def color(self):
        color_mode = config.get("color_mode", "linear")
        rainbow_speed = config.get("rainbow_speed", 1.0)
        random_colors = config.get("random_colors", False)
        
        if random_colors:
            # 随机颜色模式
            return f'#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}'
        
        if color_mode == "rainbow":
            # 彩虹色模式
            t = (self.life * rainbow_speed * 0.01) % 1.0
            r = int(255 * (0.5 + 0.5 * math.sin(2 * math.pi * t)))
            g = int(255 * (0.5 + 0.5 * math.sin(2 * math.pi * t + 2 * math.pi / 3)))
            b = int(255 * (0.5 + 0.5 * math.sin(2 * math.pi * t + 4 * math.pi / 3)))
            return f'#{r:02x}{g:02x}{b:02x}'
        elif color_mode == "gradient":
            # 渐变模式：使用多个颜色
            colors = [
                (255, 0, 0),    # 红
                (255, 165, 0),  # 橙
                (255, 255, 0),  # 黄
                (0, 255, 0),    # 绿
                (0, 0, 255),    # 蓝
                (75, 0, 130),   # 靛
                (238, 130, 238) # 紫
            ]
            t = 1 - self.life / self.max_life
            color_index = t * (len(colors) - 1)
            idx1 = int(color_index)
            idx2 = min(idx1 + 1, len(colors) - 1)
            blend = color_index - idx1
            
            r = int(colors[idx1][0] + (colors[idx2][0] - colors[idx1][0]) * blend)
            g = int(colors[idx1][1] + (colors[idx2][1] - colors[idx1][1]) * blend)
            b = int(colors[idx1][2] + (colors[idx2][2] - colors[idx1][2]) * blend)
            return f'#{r:02x}{g:02x}{b:02x}'
        elif color_mode == "radial":
            # 径向渐变：从中心向外颜色变化
            t = math.sqrt((self.x - 960)**2 + (self.y - 540)**2) / 1000  # 假设屏幕中心
            t = min(t, 1.0)
            r = int(COLOR_START[0] + (COLOR_END[0]-COLOR_START[0])*t)
            g = int(COLOR_START[1] + (COLOR_END[1]-COLOR_START[1])*t)
            b = int(COLOR_START[2] + (COLOR_END[2]-COLOR_START[2])*t)
            return f'#{r:02x}{g:02x}{b:02x}'
        else:  # linear
            # 线性渐变：默认
            t = 1 - self.life / self.max_life
            r = int(COLOR_START[0] + (COLOR_END[0]-COLOR_START[0])*t)
            g = int(COLOR_START[1] + (COLOR_END[1]-COLOR_START[1])*t)
            b = int(COLOR_START[2] + (COLOR_END[2]-COLOR_START[2])*t)
            return f'#{r:02x}{g:02x}{b:02x}'
    
    def draw(self, canvas):
        """绘制粒子，子类可以重写此方法"""
        color = self.color()
        particle_shape = config.get("particle_shape", "circle")
        
        # 应用透明度
        alpha = self.life_display
        if alpha <= 0:
            return
            
        # 根据粒子形状绘制
        if particle_shape == "square":
            # 绘制方形
            canvas.create_rectangle(
                self.x - self.size, self.y - self.size,
                self.x + self.size, self.y + self.size,
                fill=color, outline=""
            )
        elif particle_shape == "triangle":
            # 绘制三角形
            points = [
                self.x, self.y - self.size,
                self.x - self.size, self.y + self.size,
                self.x + self.size, self.y + self.size
            ]
            canvas.create_polygon(points, fill=color, outline="")
        elif particle_shape == "diamond":
            # 绘制菱形
            points = [
                self.x, self.y - self.size,
                self.x + self.size, self.y,
                self.x, self.y + self.size,
                self.x - self.size, self.y
            ]
            canvas.create_polygon(points, fill=color, outline="")
        elif particle_shape == "hexagon":
            # 绘制六边形
            points = []
            for i in range(6):
                angle = self.rotation + 60 * i
                rad = math.radians(angle)
                x = self.x + self.size * math.cos(rad)
                y = self.y + self.size * math.sin(rad)
                points.extend([x, y])
            canvas.create_polygon(points, fill=color, outline="")
        else:  # circle
            # 绘制圆形
            canvas.create_oval(
                self.x - self.size, self.y - self.size,
                self.x + self.size, self.y + self.size,
                fill=color, outline=""
            )

# 星星粒子
class StarParticle(Particle):
    def draw(self, canvas):
        color = self.color()
        points = []
        for i in range(5):
            # 外角
            angle = self.rotation + 72 * i
            rad = math.radians(angle)
            x1 = self.x + self.size * math.cos(rad)
            y1 = self.y + self.size * math.sin(rad)
            points.extend([x1, y1])
            
            # 内角
            angle_inner = self.rotation + 72 * i + 36
            rad_inner = math.radians(angle_inner)
            x2 = self.x + (self.size / 2) * math.cos(rad_inner)
            y2 = self.y + (self.size / 2) * math.sin(rad_inner)
            points.extend([x2, y2])
        
        canvas.create_polygon(points, fill=color, outline="")

# 爱心粒子（改进版，效果更明显）
class HeartParticle(Particle):
    def draw(self, canvas):
        color = self.color()
        scale = self.size * 2.5  # 缩放因子
        
        # 标准的爱心参数方程
        # x = 16 * sin³(t)
        # y = 13 * cos(t) - 5 * cos(2t) - 2 * cos(3t) - cos(4t)
        points = []
        
        # 生成爱心形状的点
        for t in range(0, 360, 5):
            rad = math.radians(t)
            
            # 爱心参数方程
            sin_t = math.sin(rad)
            cos_t = math.cos(rad)
            cos2_t = math.cos(2 * rad)
            cos3_t = math.cos(3 * rad)
            cos4_t = math.cos(4 * rad)
            
            # 爱心方程
            x = 16 * sin_t * sin_t * sin_t  # 16 * sin³(t)
            y = 13 * cos_t - 5 * cos2_t - 2 * cos3_t - cos4_t
            
            # 缩放并移动到正确位置
            x_scaled = self.x + x * scale * 0.1  # 缩小比例
            y_scaled = self.y - y * scale * 0.1  # 注意：y轴是向下的，所以用减号
        
            points.extend([x_scaled, y_scaled])
        
        # 绘制填充的爱心
        if len(points) >= 6:  # 至少需要3个点
            canvas.create_polygon(points, fill=color, outline="", smooth=True)
            # 添加轮廓使爱心更清晰
            outline_color = self.get_outline_color(color)
            canvas.create_polygon(points, fill="", outline=outline_color, width=1, smooth=True)
    
    def get_outline_color(self, fill_color):
        """根据填充色计算轮廓色"""
        # 简单的颜色变暗处理
        try:
            # 解析颜色
            if fill_color.startswith('#'):
                r = int(fill_color[1:3], 16)
                g = int(fill_color[3:5], 16)
                b = int(fill_color[5:7], 16)
                # 变暗
                r = max(0, r - 50)
                g = max(0, g - 50)
                b = max(0, b - 50)
                return f'#{r:02x}{g:02x}{b:02x}'
        except:
            pass
        return "#000000"  # 默认黑色轮廓

# 图片粒子
class ImageParticle(Particle):
    def __init__(self, x, y, image):
        super().__init__(x, y)
        self.image = image
    
    def draw(self, canvas):
        if self.image:
            canvas.create_image(
                self.x, self.y,
                image=self.image,
                anchor=tk.CENTER
            )

# 文字粒子
class TextParticle(Particle):
    def __init__(self, x, y, text, font_size=None, font_family=None, opacity=None):
        super().__init__(x, y)
        self.text = text
        # 使用配置的文字大小和字体
        self.font_size = font_size if font_size is not None else TEXT_SIZE
        self.font_family = font_family if font_family is not None else TEXT_FONT
        self.opacity = opacity if opacity is not None else TEXT_OPACITY
    
    def draw(self, canvas):
        color = self.color()
        # 计算透明度：粒子生命周期透明度 + 配置透明度
        life_alpha = self.life / self.max_life  # 0-1
        config_alpha = self.opacity / 100.0  # 0-1
        total_alpha = life_alpha * config_alpha
        
        # 由于Tkinter不支持文字透明度，我们通过调整颜色亮度来模拟
        rgba_color = self.apply_opacity_to_color(color, total_alpha)
        
        # 绘制文字
        canvas.create_text(
            self.x, self.y,
            text=self.text,
            fill=rgba_color,
            font=(self.font_family, self.font_size, "bold"),
            anchor=tk.CENTER
        )
    
    def apply_opacity_to_color(self, hex_color, alpha):
        """将透明度应用到颜色上（通过调整亮度）"""
        if hex_color.startswith('#'):
            # 解析RGB值
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            
            # 根据透明度调整颜色亮度（简单的线性混合）
            # alpha=1时颜色不变，alpha=0时变暗
            r = int(r * alpha + 255 * (1 - alpha) * 0.5)  # 混合到灰色背景
            g = int(g * alpha + 255 * (1 - alpha) * 0.5)
            b = int(b * alpha + 255 * (1 - alpha) * 0.5)
            
            # 确保值在0-255范围内
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            
            return f'#{r:02x}{g:02x}{b:02x}'
        return hex_color

# 点击文字粒子
class ClickTextParticle(Particle):
    def __init__(self, x, y, text, font_size=None, font_family=None, opacity=None, screen_width=None, screen_height=None):
        super().__init__(x, y)
        self.text = text
        # 使用配置的文字大小和字体
        self.font_size = font_size if font_size is not None else CLICK_TEXT_SIZE
        self.original_font_size = self.font_size
        self.font_family = font_family if font_family is not None else TEXT_FONT
        self.opacity = opacity if opacity is not None else CLICK_TEXT_OPACITY
        
        # 保存屏幕尺寸用于碰撞检测
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # 动画效果相关
        self.animation_type = config.get("click_animation", "float")
        self.direction = config.get("click_direction", "center")
        self.duration = config.get("click_duration", 100)
        self.max_life = self.duration  # 使用配置的持续时间
        self.life = self.max_life
        
        # 动画状态
        self.rotation = random.uniform(0, 360)
        self.bounce_height = 0
        self.explode_speed = random.uniform(1, 3)
        self.explode_angle = random.uniform(0, 2 * math.pi)
        
        # 根据方向设置初始速度
        self.set_initial_velocity(x, y, screen_width, screen_height)
        
        # 存储原始位置用于某些动画
        self.original_x = x
        self.original_y = y
        
        # 随机动画相位
        self.animation_phase = random.uniform(0, 2 * math.pi)
    
    def set_initial_velocity(self, x, y, screen_width=None, screen_height=None):
        """根据方向设置初始速度"""
        if self.direction == "center":
            # 获取屏幕尺寸或使用默认值
            if screen_width is None or screen_height is None:
                try:
                    import tkinter as tk
                    temp_root = tk.Tk()
                    screen_width = temp_root.winfo_screenwidth()
                    screen_height = temp_root.winfo_screenheight()
                    temp_root.destroy()
                except:
                    screen_width = 1920
                    screen_height = 1080
            
            # 向屏幕中央飘动
            screen_center_x = screen_width // 2
            screen_center_y = screen_height // 2
            dx = screen_center_x - x
            dy = screen_center_y - y
            distance = max(math.sqrt(dx*dx + dy*dy), 1)
            speed = 2.0
            self.vx = (dx / distance) * speed
            self.vy = (dy / distance) * speed
            
        elif self.direction == "up":
            self.vx = random.uniform(-0.5, 0.5)
            self.vy = -random.uniform(1, 3)
        elif self.direction == "down":
            self.vx = random.uniform(-0.5, 0.5)
            self.vy = random.uniform(1, 3)
        elif self.direction == "left":
            self.vx = -random.uniform(1, 3)
            self.vy = random.uniform(-0.5, 0.5)
        elif self.direction == "right":
            self.vx = random.uniform(1, 3)
            self.vy = random.uniform(-0.5, 0.5)
        elif self.direction == "random":
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 3)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
        else:  # "float" or default
            self.vx = random.uniform(-0.5, 0.5)
            self.vy = random.uniform(-0.5, 0.5)
    
    def update(self, screen_width=None, screen_height=None):
        # 使用传入的屏幕尺寸或实例保存的屏幕尺寸
        width = screen_width if screen_width is not None else self.screen_width
        height = screen_height if screen_height is not None else self.screen_height
        
        # 先调用父类的update方法，应用重力、碰撞等效果
        if not super().update(width, height):
            return False
            
        # 应用点击文字特定的动画效果
        self.apply_animation_effect()
        
        return self.life > 0
    
    def apply_animation_effect(self):
        """应用点击文字特定的动画效果"""
        if self.animation_type == "explode":
            # 爆炸效果：向外扩散
            self.x += math.cos(self.explode_angle) * self.explode_speed
            self.y += math.sin(self.explode_angle) * self.explode_speed
            self.explode_speed *= 0.95  # 逐渐减速
            
        elif self.animation_type == "rotate":
            # 旋转效果：围绕原始位置旋转
            angle = self.life * 0.1 + self.animation_phase
            radius = 20 + (self.max_life - self.life) * 0.5
            self.x = self.original_x + math.cos(angle) * radius
            self.y = self.original_y + math.sin(angle) * radius
            self.rotation += 5  # 文字自身旋转
            
        elif self.animation_type == "fade":
            # 淡入淡出效果：主要靠透明度实现
            # 文字大小保持基本不变
            self.font_size = self.original_font_size * (0.8 + 0.4 * math.sin(self.life * 0.05))
            
        elif self.animation_type == "bounce":
            # 弹跳效果
            self.bounce_height = 10 * abs(math.sin(self.life * 0.2))
            self.y = self.original_y - self.bounce_height
            self.vx *= 0.98  # 水平方向逐渐减速
            
        else:  # "float" or default
            # 浮动效果：轻微上下浮动
            float_height = 3 * math.sin(self.life * 0.1 + self.animation_phase)
            self.y += float_height * 0.1
            # 逐渐减速并变大
            self.vx *= 0.99
            self.vy *= 0.99
            self.font_size = min(self.original_font_size + (self.max_life - self.life) * 0.3, 72)
    
    def draw(self, canvas):
        # 点击文字使用固定颜色，更醒目
        colors = ["#FF6B6B", "#4ECDC4", "#FFD166", "#06D6A0", "#118AB2", "#EF476F", "#FF9A00", "#9B59B6", "#1ABC9C", "#E74C3C"]
        color_idx = hash(self.text) % len(colors)
        color = colors[color_idx]
        
        # 计算透明度：粒子生命周期透明度 + 配置透明度
        life_alpha = self.life_display if hasattr(self, 'life_display') else (self.life / self.max_life)
        config_alpha = self.opacity / 100.0  # 0-1
        total_alpha = life_alpha * config_alpha
        
        # 应用透明度到颜色
        rgba_color = self.apply_opacity_to_color(color, total_alpha)
        
        # 根据动画类型调整绘制效果
        if self.animation_type == "rotate":
            # 旋转动画：需要特殊处理，Tkinter不支持文字旋转
            # 使用多个文字叠加创建旋转效果
            for i in range(3):
                offset = i * 120  # 120度间隔
                angle = self.rotation + offset
                rad = math.radians(angle)
                offset_x = math.cos(rad) * 5
                offset_y = math.sin(rad) * 5
                
                # 绘制阴影
                shadow_color = self.apply_opacity_to_color("#000000", total_alpha * 0.3)
                canvas.create_text(
                    self.x + offset_x + 2, self.y + offset_y + 2,
                    text=self.text,
                    fill=shadow_color,
                    font=(self.font_family, int(self.font_size * 0.8), "bold"),
                    anchor=tk.CENTER
                )
                # 绘制主文字
                canvas.create_text(
                    self.x + offset_x, self.y + offset_y,
                    text=self.text,
                    fill=self.apply_opacity_to_color(color, total_alpha * 0.7),
                    font=(self.font_family, int(self.font_size * 0.8), "bold"),
                    anchor=tk.CENTER
                )
        else:
            # 其他动画效果
            shadow_strength = 2
            glow_strength = 0
            
            # 根据动画类型调整阴影和发光效果
            if self.animation_type == "explode":
                shadow_strength = 3
                glow_strength = 1
            elif self.animation_type == "bounce":
                shadow_strength = int(3 + self.bounce_height)
            
            # 绘制发光效果（多层文字叠加）
            if glow_strength > 0:
                for i in range(glow_strength * 2):
                    glow_alpha = total_alpha * 0.2
                    glow_color = self.apply_opacity_to_color("#FFFFFF", glow_alpha)
                    glow_size = self.font_size * (1 + i * 0.05)
                    canvas.create_text(
                        self.x, self.y,
                        text=self.text,
                        fill=glow_color,
                        font=(self.font_family, int(glow_size), "bold"),
                        anchor=tk.CENTER
                    )
            
            # 绘制阴影效果
            shadow_color = self.apply_opacity_to_color("#000000", total_alpha * 0.5)
            for i in range(shadow_strength):
                offset = i + 1
                canvas.create_text(
                    self.x + offset, self.y + offset,
                    text=self.text,
                    fill=shadow_color,
                    font=(self.font_family, int(self.font_size), "bold"),
                    anchor=tk.CENTER
                )
            
            # 绘制主文字
            canvas.create_text(
                self.x, self.y,
                text=self.text,
                fill=rgba_color,
                font=(self.font_family, int(self.font_size), "bold"),
                anchor=tk.CENTER
            )
            
            # 对于淡入淡出效果，添加外发光
            if self.animation_type == "fade":
                glow_color = self.apply_opacity_to_color(color, total_alpha * 0.3)
                canvas.create_text(
                    self.x, self.y,
                    text=self.text,
                    fill=glow_color,
                    font=(self.font_family, int(self.font_size * 1.2), "bold"),
                    anchor=tk.CENTER
                )
    
    def apply_opacity_to_color(self, hex_color, alpha):
        """将透明度应用到颜色上（通过调整亮度）"""
        if hex_color.startswith('#'):
            # 解析RGB值
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            
            # 根据透明度调整颜色亮度（简单的线性混合）
            # alpha=1时颜色不变，alpha=0时变暗
            r = int(r * alpha + 255 * (1 - alpha) * 0.5)  # 混合到灰色背景
            g = int(g * alpha + 255 * (1 - alpha) * 0.5)
            b = int(b * alpha + 255 * (1 - alpha) * 0.5)
            
            # 确保值在0-255范围内
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            
            return f'#{r:02x}{g:02x}{b:02x}'
        return hex_color

# 配置页面
class ConfigWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("鼠标拖尾-昨天软件开发-V1.0.0406")
        self.window.configure(bg="#f0f2f5")
        
        # 防止配置窗口被穿透
        self.window.attributes("-topmost", True)
        
        # 设置DPI缩放因子
        self.scale_factor = 1.0
        
        self.create_widgets()
        self.load_current_values()
        
        # 窗口居中显示
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_widgets(self):
        # 设置窗口DPI感知
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        
        # 获取屏幕DPI信息
        try:
            dpi = self.window.winfo_fpixels('1i')
            self.scale_factor = dpi / 96.0  # 96是标准DPI
        except:
            self.scale_factor = 1.0
        
        # 设置窗口背景色
        bg_color = "#f8f9fa"
        self.window.configure(bg=bg_color)
        
        # 创建主框架
        main_frame = tk.Frame(self.window, bg=bg_color)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题
        title_label = tk.Label(
            main_frame, 
            text="鼠标拖尾配置【昨天软件开发】", 
            font=self.get_scaled_font("Microsoft YaHei", 14, "bold"),
            bg=bg_color,
            fg="#2c3e50",
            pady=15
        )
        title_label.pack()
        
        # 创建滚动区域容器
        scroll_container = tk.Frame(main_frame, bg=bg_color)
        scroll_container.pack(fill="both", expand=True)
        
        # 创建Canvas和滚动条
        canvas = tk.Canvas(scroll_container, bg=bg_color, highlightthickness=0)
        scrollbar = tk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=bg_color)
        
        # 配置Canvas滚动
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # 在Canvas中创建窗口
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 绑定鼠标滚轮事件（兼容不同操作系统）
        def _on_mousewheel(event):
            # Windows和MacOS的鼠标滚轮事件处理
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # 绑定多种鼠标滚轮事件
        canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux向上
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Linux向下
        
        # 布局Canvas和滚动条
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 创建配置区域容器
        config_container = tk.Frame(scrollable_frame, bg=bg_color)
        config_container.pack(fill="both", expand=True, pady=10)
        
        # 创建左侧配置区域
        left_frame = tk.Frame(config_container, bg=bg_color)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # 创建右侧配置区域
        right_frame = tk.Frame(config_container, bg=bg_color)
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # 创建配置项
        self.create_config_sections(left_frame, right_frame)
        
        # 创建按钮区域
        self.create_action_buttons(main_frame)
        
        # 设置窗口大小和位置
        self.window.update_idletasks()
        width = 1200
        height = 900
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.window.resizable(True, True)
        
        # 初始显示图片选择
        self.on_trail_type_change()
    
    def get_scaled_font(self, font_name, size, weight="normal"):
        """获取缩放后的字体"""
        scaled_size = int(size * self.scale_factor)
        return (font_name, scaled_size, weight)
    
    def scale_int(self, value):
        """缩放整数值以适应DPI"""
        return int(value * self.scale_factor)
    
    def create_config_sections(self, left_frame, right_frame):
        """创建配置区域"""
        
        # 左侧框架：主要配置
        # 1. 拖尾类型配置
        self.create_trail_type_section(left_frame)
        
        # 2. 粒子参数配置
        self.create_particle_params_section(left_frame)
        
        # 3. 点击文字配置
        self.create_click_text_section(left_frame)
        
        # 右侧框架：辅助配置
        # 1. 颜色配置
        self.create_color_section(right_frame)
        
        # 2. 开关配置
        self.create_switch_section(right_frame)
    
    def create_trail_type_section(self, parent_frame):
        """创建拖尾类型配置区域"""
        section_frame = tk.LabelFrame(
            parent_frame,
            text="拖尾类型",
            font=("Microsoft YaHei", 11, "bold"),
            bg="#ffffff",
            fg="#2c3e50",
            padx=15,
            pady=15,
            relief="solid",
            bd=1
        )
        section_frame.pack(fill="x", pady=(0, 15))
        
        # 拖尾类型选择
        self.trail_type_var = tk.StringVar(value=config["trail_type"])
        types = [("圆形", "circle"), ("星星", "star"), ("爱心", "heart"), ("图片", "image"), ("文字", "text")]
        
        # 使用网格布局排列单选按钮
        for i, (text, value) in enumerate(types):
            rb = tk.Radiobutton(
                section_frame,
                text=text,
                variable=self.trail_type_var,
                value=value,
                command=self.on_trail_type_change,
                bg="#ffffff",
                fg="#34495e",
                font=("Microsoft YaHei", 10),
                selectcolor="#ecf0f1",
                padx=10,
                pady=2
            )
            rb.grid(row=i//3, column=i%3, sticky="w", padx=5, pady=3)
        
        # 图片选择框架
        self.image_frame = tk.Frame(section_frame, bg="#ffffff")
        self.image_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        
        tk.Label(self.image_frame, text="图片路径:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).pack(side="left", padx=(0, 5))
        
        self.image_path_var = tk.StringVar(value=config["image_path"])
        image_entry = tk.Entry(
            self.image_frame,
            textvariable=self.image_path_var,
            width=25,
            font=("Microsoft YaHei", 9),
            bg="#f8f9fa",
            relief="solid",
            bd=1
        )
        image_entry.pack(side="left", padx=(0, 5), fill="x", expand=True)
        
        browse_btn = tk.Button(
            self.image_frame,
            text="浏览",
            command=self.browse_image,
            font=("Microsoft YaHei", 9),
            bg="#ecf0f1",
            fg="#2c3e50",
            relief="raised",
            bd=1,
            padx=10,
            pady=2
        )
        browse_btn.pack(side="left")
        
        # 文字内容选择框架
        self.text_frame = tk.Frame(section_frame, bg="#ffffff")
        self.text_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        
        # 文字内容
        tk.Label(self.text_frame, text="文字内容:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).grid(row=0, column=0, sticky="w", pady=2)
        
        self.text_content_var = tk.StringVar(value=config["text_content"])
        text_entry = tk.Entry(
            self.text_frame,
            textvariable=self.text_content_var,
            width=20,
            font=("Microsoft YaHei", 9),
            bg="#f8f9fa",
            relief="solid",
            bd=1
        )
        text_entry.grid(row=0, column=1, columnspan=2, sticky="ew", padx=(5, 0), pady=2)
        
        # 文字大小
        tk.Label(self.text_frame, text="文字大小:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).grid(row=1, column=0, sticky="w", pady=2)
        
        self.text_size_var = tk.IntVar(value=config.get("text_size", 24))
        tk.Scale(
            self.text_frame,
            from_=8,
            to=72,
            variable=self.text_size_var,
            orient="horizontal",
            length=180,
            bg="#ffffff",
            fg="#34495e",
            highlightthickness=0,
            sliderrelief="raised"
        ).grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        
        size_label = tk.Label(self.text_frame, textvariable=self.text_size_var, 
                            bg="#ffffff", font=("Microsoft YaHei", 9))
        size_label.grid(row=1, column=2, sticky="w", padx=5, pady=2)
        
        # 文字字体
        tk.Label(self.text_frame, text="文字字体:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).grid(row=2, column=0, sticky="w", pady=2)
        
        self.text_font_var = tk.StringVar(value=config.get("text_font", "Arial"))
        fonts = ["Arial", "Microsoft YaHei", "SimHei", "SimSun", "KaiTi"]
        
        font_menu = tk.OptionMenu(self.text_frame, self.text_font_var, *fonts)
        font_menu.config(font=("Microsoft YaHei", 9), bg="#ecf0f1", fg="#2c3e50", 
                        relief="raised", bd=1, width=12)
        font_menu.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        # 文字透明度
        tk.Label(self.text_frame, text="透明度:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).grid(row=3, column=0, sticky="w", pady=2)
        
        self.text_opacity_var = tk.IntVar(value=config.get("text_opacity", 100))
        tk.Scale(
            self.text_frame,
            from_=0,
            to=100,
            variable=self.text_opacity_var,
            orient="horizontal",
            length=180,
            bg="#ffffff",
            fg="#34495e",
            highlightthickness=0,
            sliderrelief="raised"
        ).grid(row=3, column=1, sticky="ew", padx=5, pady=2)
        
        opacity_label = tk.Label(self.text_frame, textvariable=self.text_opacity_var, 
                               bg="#ffffff", font=("Microsoft YaHei", 9))
        opacity_label.grid(row=3, column=2, sticky="w", padx=5, pady=2)
        
        tk.Label(self.text_frame, text="%", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).grid(row=3, column=2, sticky="e", padx=(0, 5))
        
        # 文字旋转角度
        tk.Label(self.text_frame, text="旋转角度:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).grid(row=4, column=0, sticky="w", pady=2)
        
        self.text_rotation_var = tk.IntVar(value=config.get("text_rotation", 0))
        tk.Scale(
            self.text_frame,
            from_=0,
            to=360,
            variable=self.text_rotation_var,
            orient="horizontal",
            length=180,
            bg="#ffffff",
            fg="#34495e",
            highlightthickness=0,
            sliderrelief="raised"
        ).grid(row=4, column=1, sticky="ew", padx=5, pady=2)
        
        rotation_label = tk.Label(self.text_frame, textvariable=self.text_rotation_var, 
                               bg="#ffffff", font=("Microsoft YaHei", 9))
        rotation_label.grid(row=4, column=2, sticky="w", padx=5, pady=2)
        
        tk.Label(self.text_frame, text="°", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).grid(row=4, column=2, sticky="e", padx=(0, 5))
        
        # 文字阴影效果
        self.text_shadow_var = tk.BooleanVar(value=config.get("text_shadow", False))
        shadow_cb = tk.Checkbutton(
            self.text_frame,
            text="文字阴影效果",
            variable=self.text_shadow_var,
            bg="#ffffff",
            fg="#34495e",
            font=("Microsoft YaHei", 9),
            selectcolor="#ecf0f1",
            padx=5,
            pady=2
        )
        shadow_cb.grid(row=5, column=0, columnspan=3, sticky="w", pady=(10, 2))
        
        # 文字粗细
        tk.Label(self.text_frame, text="文字粗细:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).grid(row=6, column=0, sticky="w", pady=2)
        
        self.text_weight_var = tk.StringVar(value=config.get("text_weight", "normal"))
        weights = ["normal", "bold", "italic", "bold italic"]
        
        weight_menu = tk.OptionMenu(self.text_frame, self.text_weight_var, *weights)
        weight_menu.config(font=("Microsoft YaHei", 9), bg="#ecf0f1", fg="#2c3e50", 
                        relief="raised", bd=1, width=12)
        weight_menu.grid(row=6, column=1, sticky="w", padx=5, pady=2)
    
    def create_particle_params_section(self, parent_frame):
        """创建粒子参数配置区域"""
        section_frame = tk.LabelFrame(
            parent_frame,
            text="粒子参数",
            font=("Microsoft YaHei", 11, "bold"),
            bg="#ffffff",
            fg="#2c3e50",
            padx=15,
            pady=15,
            relief="solid",
            bd=1
        )
        section_frame.pack(fill="x", pady=(0, 15))
        
        # 使用网格布局
        section_frame.columnconfigure(1, weight=1)
        
        # 生命值
        tk.Label(section_frame, text="生命值:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).grid(row=0, column=0, sticky="w", pady=5)
        
        self.life_var = tk.IntVar(value=config["particle_max_life"])
        life_scale = tk.Scale(
            section_frame,
            from_=10,
            to=200,
            variable=self.life_var,
            orient="horizontal",
            length=200,
            bg="#ffffff",
            fg="#34495e",
            highlightthickness=0,
            sliderrelief="raised"
        )
        life_scale.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        tk.Label(section_frame, textvariable=self.life_var, bg="#ffffff", 
                font=("Microsoft YaHei", 9)).grid(row=0, column=2, sticky="w", padx=5)
        
        # 速度
        tk.Label(section_frame, text="速度:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).grid(row=1, column=0, sticky="w", pady=5)
        
        self.speed_var = tk.DoubleVar(value=config["particle_speed"])
        speed_scale = tk.Scale(
            section_frame,
            from_=0.1,
            to=5.0,
            resolution=0.1,
            variable=self.speed_var,
            orient="horizontal",
            length=200,
            bg="#ffffff",
            fg="#34495e",
            highlightthickness=0,
            sliderrelief="raised"
        )
        speed_scale.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        tk.Label(section_frame, textvariable=self.speed_var, bg="#ffffff", 
                font=("Microsoft YaHei", 9)).grid(row=1, column=2, sticky="w", padx=5)
        
        # 大小
        tk.Label(section_frame, text="大小:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).grid(row=2, column=0, sticky="w", pady=5)
        
        self.size_var = tk.IntVar(value=config["particle_size"])
        size_scale = tk.Scale(
            section_frame,
            from_=1,
            to=20,
            variable=self.size_var,
            orient="horizontal",
            length=200,
            bg="#ffffff",
            fg="#34495e",
            highlightthickness=0,
            sliderrelief="raised"
        )
        size_scale.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        tk.Label(section_frame, textvariable=self.size_var, bg="#ffffff", 
                font=("Microsoft YaHei", 9)).grid(row=2, column=2, sticky="w", padx=5)
        
        # 生成数量
        tk.Label(section_frame, text="数量:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).grid(row=3, column=0, sticky="w", pady=5)
        
        self.count_var = tk.IntVar(value=config["spawn_count"])
        count_scale = tk.Scale(
            section_frame,
            from_=1,
            to=20,
            variable=self.count_var,
            orient="horizontal",
            length=200,
            bg="#ffffff",
            fg="#34495e",
            highlightthickness=0,
            sliderrelief="raised"
        )
        count_scale.grid(row=3, column=1, sticky="ew", padx=10, pady=5)
        tk.Label(section_frame, textvariable=self.count_var, bg="#ffffff", 
                font=("Microsoft YaHei", 9)).grid(row=3, column=2, sticky="w", padx=5)
        
        # 粒子旋转速度
        tk.Label(section_frame, text="旋转速度:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).grid(row=4, column=0, sticky="w", pady=5)
        
        self.rotation_speed_var = tk.DoubleVar(value=config.get("rotation_speed", 1.0))
        rotation_scale = tk.Scale(
            section_frame,
            from_=0,
            to=10,
            resolution=0.1,
            variable=self.rotation_speed_var,
            orient="horizontal",
            length=200,
            bg="#ffffff",
            fg="#34495e",
            highlightthickness=0,
            sliderrelief="raised"
        )
        rotation_scale.grid(row=4, column=1, sticky="ew", padx=10, pady=5)
        tk.Label(section_frame, textvariable=self.rotation_speed_var, bg="#ffffff", 
                font=("Microsoft YaHei", 9)).grid(row=4, column=2, sticky="w", padx=5)
        
        # 粒子生成间隔
        tk.Label(section_frame, text="生成间隔:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).grid(row=5, column=0, sticky="w", pady=5)
        
        self.spawn_interval_var = tk.IntVar(value=config.get("spawn_interval", 2))
        interval_scale = tk.Scale(
            section_frame,
            from_=1,
            to=10,
            variable=self.spawn_interval_var,
            orient="horizontal",
            length=200,
            bg="#ffffff",
            fg="#34495e",
            highlightthickness=0,
            sliderrelief="raised"
        )
        interval_scale.grid(row=5, column=1, sticky="ew", padx=10, pady=5)
        tk.Label(section_frame, textvariable=self.spawn_interval_var, bg="#ffffff", 
                font=("Microsoft YaHei", 9)).grid(row=5, column=2, sticky="w", padx=5)
        
        # 粒子透明度变化模式
        tk.Label(section_frame, text="透明度模式:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).grid(row=6, column=0, sticky="w", pady=5)
        
        self.opacity_mode_var = tk.StringVar(value=config.get("opacity_mode", "linear"))
        opacity_modes = ["linear", "fade_in", "fade_out", "pulse"]
        
        opacity_menu = tk.OptionMenu(section_frame, self.opacity_mode_var, *opacity_modes)
        opacity_menu.config(font=("Microsoft YaHei", 9), bg="#ecf0f1", fg="#2c3e50", 
                          relief="raised", bd=1, width=12)
        opacity_menu.grid(row=6, column=1, sticky="w", padx=10, pady=5)
        
        # 粒子形状
        tk.Label(section_frame, text="粒子形状:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).grid(row=7, column=0, sticky="w", pady=5)
        
        self.particle_shape_var = tk.StringVar(value=config.get("particle_shape", "circle"))
        shapes = ["circle", "square", "triangle", "diamond", "hexagon"]
        
        shape_menu = tk.OptionMenu(section_frame, self.particle_shape_var, *shapes)
        shape_menu.config(font=("Microsoft YaHei", 9), bg="#ecf0f1", fg="#2c3e50", 
                        relief="raised", bd=1, width=12)
        shape_menu.grid(row=7, column=1, sticky="w", padx=10, pady=5)
    
    def create_color_section(self, parent_frame):
        """创建颜色配置区域"""
        section_frame = tk.LabelFrame(
            parent_frame,
            text="颜色配置",
            font=("Microsoft YaHei", 11, "bold"),
            bg="#ffffff",
            fg="#2c3e50",
            padx=15,
            pady=15,
            relief="solid",
            bd=1
        )
        section_frame.pack(fill="x", pady=(0, 15))
        
        # 起始颜色
        start_color_frame = tk.Frame(section_frame, bg="#ffffff")
        start_color_frame.pack(fill="x", pady=8)
        
        tk.Label(start_color_frame, text="起始颜色:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).pack(side="left", padx=(0, 10))
        
        self.start_color_btn = tk.Button(
            start_color_frame,
            text="选择",
            command=lambda: self.choose_color("color_start"),
            font=("Microsoft YaHei", 9),
            bg="#ecf0f1",
            fg="#2c3e50",
            relief="raised",
            bd=1,
            padx=12,
            pady=2
        )
        self.start_color_btn.pack(side="left", padx=(0, 10))
        
        self.start_color_preview = tk.Canvas(
            start_color_frame,
            width=40,
            height=20,
            bg=self.rgb_to_hex(config["color_start"]),
            relief="solid",
            bd=1
        )
        self.start_color_preview.pack(side="left")
        
        # 结束颜色
        end_color_frame = tk.Frame(section_frame, bg="#ffffff")
        end_color_frame.pack(fill="x", pady=8)
        
        tk.Label(end_color_frame, text="结束颜色:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).pack(side="left", padx=(0, 10))
        
        self.end_color_btn = tk.Button(
            end_color_frame,
            text="选择",
            command=lambda: self.choose_color("color_end"),
            font=("Microsoft YaHei", 9),
            bg="#ecf0f1",
            fg="#2c3e50",
            relief="raised",
            bd=1,
            padx=12,
            pady=2
        )
        self.end_color_btn.pack(side="left", padx=(0, 10))
        
        self.end_color_preview = tk.Canvas(
            end_color_frame,
            width=40,
            height=20,
            bg=self.rgb_to_hex(config["color_end"]),
            relief="solid",
            bd=1
        )
        self.end_color_preview.pack(side="left")
        
        # 颜色过渡模式
        color_mode_frame = tk.Frame(section_frame, bg="#ffffff")
        color_mode_frame.pack(fill="x", pady=8)
        
        tk.Label(color_mode_frame, text="颜色过渡:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).pack(side="left", padx=(0, 10))
        
        self.color_mode_var = tk.StringVar(value=config.get("color_mode", "linear"))
        color_modes = ["linear", "radial", "rainbow", "gradient"]
        
        color_mode_menu = tk.OptionMenu(color_mode_frame, self.color_mode_var, *color_modes)
        color_mode_menu.config(font=("Microsoft YaHei", 9), bg="#ecf0f1", fg="#2c3e50", 
                             relief="raised", bd=1, width=10)
        color_mode_menu.pack(side="left", padx=(0, 10))
        
        # 彩虹色速度
        rainbow_frame = tk.Frame(section_frame, bg="#ffffff")
        rainbow_frame.pack(fill="x", pady=8)
        
        tk.Label(rainbow_frame, text="彩虹速度:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).pack(side="left", padx=(0, 10))
        
        self.rainbow_speed_var = tk.DoubleVar(value=config.get("rainbow_speed", 1.0))
        rainbow_scale = tk.Scale(
            rainbow_frame,
            from_=0.1,
            to=5.0,
            resolution=0.1,
            variable=self.rainbow_speed_var,
            orient="horizontal",
            length=150,
            bg="#ffffff",
            fg="#34495e",
            highlightthickness=0,
            sliderrelief="raised"
        )
        rainbow_scale.pack(side="left", padx=(0, 10))
        
        tk.Label(rainbow_frame, textvariable=self.rainbow_speed_var, bg="#ffffff", 
                font=("Microsoft YaHei", 9)).pack(side="left")
        
        # 颜色随机性
        random_frame = tk.Frame(section_frame, bg="#ffffff")
        random_frame.pack(fill="x", pady=8)
        
        self.random_colors_var = tk.BooleanVar(value=config.get("random_colors", False))
        random_cb = tk.Checkbutton(
            random_frame,
            text="启用随机颜色",
            variable=self.random_colors_var,
            bg="#ffffff",
            fg="#34495e",
            font=("Microsoft YaHei", 9),
            selectcolor="#ecf0f1",
            padx=5,
            pady=2
        )
        random_cb.pack(side="left")
    
    def create_switch_section(self, parent_frame):
        """创建开关配置区域"""
        section_frame = tk.LabelFrame(
            parent_frame,
            text="开关配置",
            font=("Microsoft YaHei", 11, "bold"),
            bg="#ffffff",
            fg="#2c3e50",
            padx=15,
            pady=15,
            relief="solid",
            bd=1
        )
        section_frame.pack(fill="x", pady=(0, 15))
        
        # 启用拖尾
        self.enabled_var = tk.BooleanVar(value=config["trail_enabled"])
        enabled_cb = tk.Checkbutton(
            section_frame,
            text="启用拖尾效果",
            variable=self.enabled_var,
            bg="#ffffff",
            fg="#34495e",
            font=("Microsoft YaHei", 9),
            selectcolor="#ecf0f1",
            padx=5,
            pady=2
        )
        enabled_cb.pack(anchor="w", pady=4)
        
        # 仅移动时显示
        self.moving_var = tk.BooleanVar(value=config["only_when_moving"])
        moving_cb = tk.Checkbutton(
            section_frame,
            text="仅鼠标移动时显示",
            variable=self.moving_var,
            bg="#ffffff",
            fg="#34495e",
            font=("Microsoft YaHei", 9),
            selectcolor="#ecf0f1",
            padx=5,
            pady=2
        )
        moving_cb.pack(anchor="w", pady=4)
        
        # 一直显示
        self.always_var = tk.BooleanVar(value=config["always_trail"])
        always_cb = tk.Checkbutton(
            section_frame,
            text="一直显示拖尾",
            variable=self.always_var,
            bg="#ffffff",
            fg="#34495e",
            font=("Microsoft YaHei", 9),
            selectcolor="#ecf0f1",
            padx=5,
            pady=2
        )
        always_cb.pack(anchor="w", pady=4)
        
        # 启用点击效果
        self.click_enabled_var = tk.BooleanVar(value=config["click_effect_enabled"])
        click_cb = tk.Checkbutton(
            section_frame,
            text="启用鼠标点击效果",
            variable=self.click_enabled_var,
            bg="#ffffff",
            fg="#34495e",
            font=("Microsoft YaHei", 9),
            selectcolor="#ecf0f1",
            padx=5,
            pady=2
        )
        click_cb.pack(anchor="w", pady=4)
        
        # 启用拖尾碰撞检测
        self.collision_var = tk.BooleanVar(value=config.get("collision_enabled", False))
        collision_cb = tk.Checkbutton(
            section_frame,
            text="启用粒子碰撞效果",
            variable=self.collision_var,
            bg="#ffffff",
            fg="#34495e",
            font=("Microsoft YaHei", 9),
            selectcolor="#ecf0f1",
            padx=5,
            pady=2
        )
        collision_cb.pack(anchor="w", pady=4)
        
        # 启用粒子重力
        self.gravity_var = tk.BooleanVar(value=config.get("gravity_enabled", False))
        gravity_cb = tk.Checkbutton(
            section_frame,
            text="启用粒子重力效果",
            variable=self.gravity_var,
            bg="#ffffff",
            fg="#34495e",
            font=("Microsoft YaHei", 9),
            selectcolor="#ecf0f1",
            padx=5,
            pady=2
        )
        gravity_cb.pack(anchor="w", pady=4)
        
        # 启用粒子跟随鼠标
        self.follow_mouse_var = tk.BooleanVar(value=config.get("follow_mouse", True))
        follow_cb = tk.Checkbutton(
            section_frame,
            text="粒子跟随鼠标移动",
            variable=self.follow_mouse_var,
            bg="#ffffff",
            fg="#34495e",
            font=("Microsoft YaHei", 9),
            selectcolor="#ecf0f1",
            padx=5,
            pady=2
        )
        follow_cb.pack(anchor="w", pady=4)
        
        # 启用粒子拖尾
        self.trail_particles_var = tk.BooleanVar(value=config.get("trail_particles", False))
        trail_cb = tk.Checkbutton(
            section_frame,
            text="粒子产生拖尾",
            variable=self.trail_particles_var,
            bg="#ffffff",
            fg="#34495e",
            font=("Microsoft YaHei", 9),
            selectcolor="#ecf0f1",
            padx=5,
            pady=2
        )
        trail_cb.pack(anchor="w", pady=4)
    
    def create_click_text_section(self, parent_frame):
        """创建点击文字配置区域"""
        section_frame = tk.LabelFrame(
            parent_frame,
            text="点击文字配置",
            font=("Microsoft YaHei", 11, "bold"),
            bg="#ffffff",
            fg="#2c3e50",
            padx=15,
            pady=15,
            relief="solid",
            bd=1
        )
        section_frame.pack(fill="x", pady=(0, 15))
        
        # 点击文字内容
        tk.Label(section_frame, text="点击文字(用分号分隔):", bg="#ffffff", 
                font=("Microsoft YaHei", 9), anchor="w").pack(anchor="w", pady=(0, 5))
        
        self.click_texts_var = tk.StringVar(value=config["click_texts"])
        click_text_entry = tk.Entry(
            section_frame,
            textvariable=self.click_texts_var,
            font=("Microsoft YaHei", 9),
            bg="#f8f9fa",
            relief="solid",
            bd=1
        )
        click_text_entry.pack(fill="x", pady=(0, 5))
        
        tk.Label(section_frame, text="示例: ✨;🌟;💖;🎉;👍;😊", fg="#7f8c8d", 
                bg="#ffffff", font=("Microsoft YaHei", 8), anchor="w").pack(anchor="w")
        
        # 点击文字大小和透明度
        controls_frame = tk.Frame(section_frame, bg="#ffffff")
        controls_frame.pack(fill="x", pady=(10, 0))
        
        # 点击文字大小
        size_frame = tk.Frame(controls_frame, bg="#ffffff")
        size_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        tk.Label(size_frame, text="文字大小:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).pack(anchor="w")
        
        self.click_text_size_var = tk.IntVar(value=config.get("click_text_size", 36))
        click_size_scale = tk.Scale(
            size_frame,
            from_=8,
            to=72,
            variable=self.click_text_size_var,
            orient="horizontal",
            length=180,
            bg="#ffffff",
            fg="#34495e",
            highlightthickness=0,
            sliderrelief="raised"
        )
        click_size_scale.pack(fill="x", pady=5)
        tk.Label(size_frame, textvariable=self.click_text_size_var, bg="#ffffff", 
                font=("Microsoft YaHei", 9)).pack()
        
        # 点击文字透明度
        opacity_frame = tk.Frame(controls_frame, bg="#ffffff")
        opacity_frame.pack(side="right", fill="both", expand=True)
        
        tk.Label(opacity_frame, text="透明度:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).pack(anchor="w")
        
        self.click_text_opacity_var = tk.IntVar(value=config.get("click_text_opacity", 100))
        click_opacity_scale = tk.Scale(
            opacity_frame,
            from_=0,
            to=100,
            variable=self.click_text_opacity_var,
            orient="horizontal",
            length=180,
            bg="#ffffff",
            fg="#34495e",
            highlightthickness=0,
            sliderrelief="raised"
        )
        click_opacity_scale.pack(fill="x", pady=5)
        
        opacity_label_frame = tk.Frame(opacity_frame, bg="#ffffff")
        opacity_label_frame.pack()
        tk.Label(opacity_label_frame, textvariable=self.click_text_opacity_var, 
                bg="#ffffff", font=("Microsoft YaHei", 9)).pack(side="left")
        tk.Label(opacity_label_frame, text="%", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).pack(side="left")
        
        # 点击文字动画效果
        animation_frame = tk.Frame(section_frame, bg="#ffffff")
        animation_frame.pack(fill="x", pady=(15, 0))
        
        tk.Label(animation_frame, text="动画效果:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).pack(side="left", padx=(0, 10))
        
        self.click_animation_var = tk.StringVar(value=config.get("click_animation", "float"))
        animations = ["float", "explode", "rotate", "fade", "bounce"]
        
        animation_menu = tk.OptionMenu(animation_frame, self.click_animation_var, *animations)
        animation_menu.config(font=("Microsoft YaHei", 9), bg="#ecf0f1", fg="#2c3e50", 
                            relief="raised", bd=1, width=12)
        animation_menu.pack(side="left", padx=(0, 10))
        
        # 点击文字方向
        direction_frame = tk.Frame(section_frame, bg="#ffffff")
        direction_frame.pack(fill="x", pady=(10, 0))
        
        tk.Label(direction_frame, text="文字方向:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).pack(side="left", padx=(0, 10))
        
        self.click_direction_var = tk.StringVar(value=config.get("click_direction", "center"))
        directions = ["center", "up", "down", "left", "right", "random"]
        
        direction_menu = tk.OptionMenu(direction_frame, self.click_direction_var, *directions)
        direction_menu.config(font=("Microsoft YaHei", 9), bg="#ecf0f1", fg="#2c3e50", 
                            relief="raised", bd=1, width=12)
        direction_menu.pack(side="left", padx=(0, 10))
        
        # 点击文字持续时间
        duration_frame = tk.Frame(section_frame, bg="#ffffff")
        duration_frame.pack(fill="x", pady=(10, 0))
        
        tk.Label(duration_frame, text="持续时间:", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).pack(side="left", padx=(0, 10))
        
        self.click_duration_var = tk.IntVar(value=config.get("click_duration", 100))
        duration_scale = tk.Scale(
            duration_frame,
            from_=20,
            to=300,
            variable=self.click_duration_var,
            orient="horizontal",
            length=150,
            bg="#ffffff",
            fg="#34495e",
            highlightthickness=0,
            sliderrelief="raised"
        )
        duration_scale.pack(side="left", padx=(0, 10))
        
        tk.Label(duration_frame, textvariable=self.click_duration_var, bg="#ffffff", 
                font=("Microsoft YaHei", 9)).pack(side="left")
        tk.Label(duration_frame, text="帧", bg="#ffffff", 
                font=("Microsoft YaHei", 9)).pack(side="left", padx=(5, 0))
    
    def create_action_buttons(self, parent_frame):
        """创建操作按钮区域"""
        button_frame = tk.Frame(parent_frame, bg="#f8f9fa")
        button_frame.pack(fill="x", pady=20)
        
        # 配置操作按钮
        config_buttons_frame = tk.Frame(button_frame, bg="#f8f9fa")
        config_buttons_frame.pack(pady=(0, 10))
        
        # 第一行按钮：配置操作
        save_btn = tk.Button(
            config_buttons_frame,
            text="保存配置",
            command=self.save_config,
            font=("Microsoft YaHei", 10),
            bg="#27ae60",
            fg="white",
            relief="raised",
            bd=1,
            padx=15,
            pady=5,
            width=10
        )
        save_btn.pack(side="left", padx=5)
        
        apply_btn = tk.Button(
            config_buttons_frame,
            text="应用配置",
            command=self.apply_config,
            font=("Microsoft YaHei", 10),
            bg="#3498db",
            fg="white",
            relief="raised",
            bd=1,
            padx=15,
            pady=5,
            width=10
        )
        apply_btn.pack(side="left", padx=5)
        
        reset_btn = tk.Button(
            config_buttons_frame,
            text="重置默认",
            command=self.reset_default,
            font=("Microsoft YaHei", 10),
            bg="#f39c12",
            fg="white",
            relief="raised",
            bd=1,
            padx=15,
            pady=5,
            width=10
        )
        reset_btn.pack(side="left", padx=5)
        
        # 第二行按钮：程序控制
        control_buttons_frame = tk.Frame(button_frame, bg="#f8f9fa")
        control_buttons_frame.pack()
        
        autostart_btn = tk.Button(
            control_buttons_frame,
            text="开机启动",
            command=self.toggle_auto_start,
            font=("Microsoft YaHei", 10),
            bg="#9b59b6",
            fg="white",
            relief="raised",
            bd=1,
            padx=15,
            pady=5,
            width=10
        )
        autostart_btn.pack(side="left", padx=5)
        
        close_btn = tk.Button(
            control_buttons_frame,
            text="关闭配置",
            command=self.window.destroy,
            font=("Microsoft YaHei", 10),
            bg="#95a5a6",
            fg="white",
            relief="raised",
            bd=1,
            padx=15,
            pady=5,
            width=10
        )
        close_btn.pack(side="left", padx=5)
        
        exit_btn = tk.Button(
            control_buttons_frame,
            text="退出程序",
            command=self.exit_program,
            font=("Microsoft YaHei", 10),
            bg="#e74c3c",
            fg="white",
            relief="raised",
            bd=1,
            padx=15,
            pady=5,
            width=10
        )
        exit_btn.pack(side="left", padx=5)
    
    def rgb_to_hex(self, rgb):
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
    
    def on_trail_type_change(self):
        trail_type = self.trail_type_var.get()
        
        if trail_type == "image":
            self.image_frame.grid()
            self.text_frame.grid_remove()
        elif trail_type == "text":
            self.text_frame.grid()
            self.image_frame.grid_remove()
        else:
            self.image_frame.grid_remove()
            self.text_frame.grid_remove()
    
    def browse_image(self):
        filename = filedialog.askopenfilename(
            title="选择拖尾图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.gif *.bmp"), ("所有文件", "*.*")]
        )
        if filename:
            self.image_path_var.set(filename)
    
    def choose_color(self, color_key):
        current_color = config[color_key]
        color = colorchooser.askcolor(
            title=f"选择{color_key}颜色",
            initialcolor=self.rgb_to_hex(current_color)
        )
        if color[0]:
            rgb = tuple(int(c) for c in color[0])
            config[color_key] = rgb
            if color_key == "color_start":
                self.start_color_preview.config(bg=color[1])
            else:
                self.end_color_preview.config(bg=color[1])
    
    def load_current_values(self):
        self.trail_type_var.set(config["trail_type"])
        self.image_path_var.set(config["image_path"])
        self.text_content_var.set(config["text_content"])
        self.text_size_var.set(config.get("text_size", 24))
        self.text_font_var.set(config.get("text_font", "Arial"))
        self.text_opacity_var.set(config.get("text_opacity", 100))
        self.text_rotation_var.set(config.get("text_rotation", 0))
        self.text_shadow_var.set(config.get("text_shadow", False))
        self.text_weight_var.set(config.get("text_weight", "normal"))
        self.click_texts_var.set(config["click_texts"])
        self.click_text_size_var.set(config.get("click_text_size", 36))
        self.click_text_opacity_var.set(config.get("click_text_opacity", 100))
        self.click_animation_var.set(config.get("click_animation", "float"))
        self.click_direction_var.set(config.get("click_direction", "center"))
        self.click_duration_var.set(config.get("click_duration", 100))
        self.life_var.set(config["particle_max_life"])
        self.speed_var.set(config["particle_speed"])
        self.size_var.set(config["particle_size"])
        self.count_var.set(config["spawn_count"])
        self.rotation_speed_var.set(config.get("rotation_speed", 1.0))
        self.spawn_interval_var.set(config.get("spawn_interval", 2))
        self.opacity_mode_var.set(config.get("opacity_mode", "linear"))
        self.particle_shape_var.set(config.get("particle_shape", "circle"))
        self.enabled_var.set(config["trail_enabled"])
        self.moving_var.set(config["only_when_moving"])
        self.always_var.set(config["always_trail"])
        self.click_enabled_var.set(config["click_effect_enabled"])
        self.collision_var.set(config.get("collision_enabled", False))
        self.gravity_var.set(config.get("gravity_enabled", False))
        self.follow_mouse_var.set(config.get("follow_mouse", True))
        self.trail_particles_var.set(config.get("trail_particles", False))
        self.color_mode_var.set(config.get("color_mode", "linear"))
        self.rainbow_speed_var.set(config.get("rainbow_speed", 1.0))
        self.random_colors_var.set(config.get("random_colors", False))
        self.start_color_preview.config(bg=self.rgb_to_hex(config["color_start"]))
        self.end_color_preview.config(bg=self.rgb_to_hex(config["color_end"]))
    
    def save_config(self):
        self.apply_config()
        save_config()
        messagebox.showinfo("成功", "配置已保存到文件")
    
    def apply_config(self):
        # 更新配置
        config["trail_type"] = self.trail_type_var.get()
        config["image_path"] = self.image_path_var.get()
        config["text_content"] = self.text_content_var.get()
        config["text_size"] = self.text_size_var.get()
        config["text_font"] = self.text_font_var.get()
        config["text_opacity"] = self.text_opacity_var.get()
        config["text_rotation"] = self.text_rotation_var.get()
        config["text_shadow"] = self.text_shadow_var.get()
        config["text_weight"] = self.text_weight_var.get()
        config["click_texts"] = self.click_texts_var.get()
        config["click_text_size"] = self.click_text_size_var.get()
        config["click_text_opacity"] = self.click_text_opacity_var.get()
        config["click_animation"] = self.click_animation_var.get()
        config["click_direction"] = self.click_direction_var.get()
        config["click_duration"] = self.click_duration_var.get()
        config["particle_max_life"] = self.life_var.get()
        config["particle_speed"] = self.speed_var.get()
        config["particle_size"] = self.size_var.get()
        config["spawn_count"] = self.count_var.get()
        config["rotation_speed"] = self.rotation_speed_var.get()
        config["spawn_interval"] = self.spawn_interval_var.get()
        config["opacity_mode"] = self.opacity_mode_var.get()
        config["particle_shape"] = self.particle_shape_var.get()
        config["trail_enabled"] = self.enabled_var.get()
        config["only_when_moving"] = self.moving_var.get()
        config["always_trail"] = self.always_var.get()
        config["click_effect_enabled"] = self.click_enabled_var.get()
        config["collision_enabled"] = self.collision_var.get()
        config["gravity_enabled"] = self.gravity_var.get()
        config["follow_mouse"] = self.follow_mouse_var.get()
        config["trail_particles"] = self.trail_particles_var.get()
        config["color_mode"] = self.color_mode_var.get()
        config["rainbow_speed"] = self.rainbow_speed_var.get()
        config["random_colors"] = self.random_colors_var.get()
        
        # 更新全局变量
        global COLOR_START, COLOR_END, PARTICLE_MAX_LIFE, PARTICLE_SPEED, PARTICLE_SIZE, SPAWN_COUNT
        global TRAIL_TYPE, IMAGE_PATH, TEXT_CONTENT, TEXT_SIZE, TEXT_FONT, TEXT_OPACITY, CLICK_TEXTS, CLICK_TEXT_SIZE, CLICK_TEXT_OPACITY
        global ONLY_WHEN_MOVING, TRAIL_ENABLED, ALWAYS_TRAIL, CLICK_EFFECT_ENABLED, AUTO_START
        global ROTATION_SPEED, SPAWN_INTERVAL, OPACITY_MODE, PARTICLE_SHAPE, COLLISION_ENABLED, GRAVITY_ENABLED
        global FOLLOW_MOUSE, TRAIL_PARTICLES, COLOR_MODE, RAINBOW_SPEED, RANDOM_COLORS
        global CLICK_ANIMATION, CLICK_DIRECTION, CLICK_DURATION
        
        COLOR_START = config["color_start"]
        COLOR_END = config["color_end"]
        PARTICLE_MAX_LIFE = config["particle_max_life"]
        PARTICLE_SPEED = config["particle_speed"]
        PARTICLE_SIZE = config["particle_size"]
        SPAWN_COUNT = config["spawn_count"]
        TRAIL_TYPE = config["trail_type"]
        IMAGE_PATH = config["image_path"]
        TEXT_CONTENT = config["text_content"]
        TEXT_SIZE = config.get("text_size", 24)
        TEXT_FONT = config.get("text_font", "Arial")
        TEXT_OPACITY = config.get("text_opacity", 100)
        CLICK_TEXTS = config["click_texts"]
        CLICK_TEXT_SIZE = config.get("click_text_size", 36)
        CLICK_TEXT_OPACITY = config.get("click_text_opacity", 100)
        CLICK_ANIMATION = config.get("click_animation", "float")
        CLICK_DIRECTION = config.get("click_direction", "center")
        CLICK_DURATION = config.get("click_duration", 100)
        ONLY_WHEN_MOVING = config["only_when_moving"]
        TRAIL_ENABLED = config["trail_enabled"]
        ALWAYS_TRAIL = config["always_trail"]
        CLICK_EFFECT_ENABLED = config["click_effect_enabled"]
        COLLISION_ENABLED = config.get("collision_enabled", False)
        GRAVITY_ENABLED = config.get("gravity_enabled", False)
        FOLLOW_MOUSE = config.get("follow_mouse", True)
        TRAIL_PARTICLES = config.get("trail_particles", False)
        ROTATION_SPEED = config.get("rotation_speed", 1.0)
        SPAWN_INTERVAL = config.get("spawn_interval", 2)
        OPACITY_MODE = config.get("opacity_mode", "linear")
        PARTICLE_SHAPE = config.get("particle_shape", "circle")
        COLOR_MODE = config.get("color_mode", "linear")
        RAINBOW_SPEED = config.get("rainbow_speed", 1.0)
        RANDOM_COLORS = config.get("random_colors", False)
        AUTO_START = config.get("auto_start", False)
        
        messagebox.showinfo("成功", "配置已应用")
    
    def reset_default(self):
        global config
        config = DEFAULT_CONFIG.copy()
        self.load_current_values()
        messagebox.showinfo("成功", "已重置为默认配置")
    
    def toggle_auto_start(self):
        """切换开机启动状态"""
        import winreg
        import sys
        
        # 获取当前程序路径
        exe_path = sys.executable
        script_path = os.path.abspath(__file__)
        
        # 如果使用python解释器运行，则使用python解释器路径和脚本路径
        if exe_path.endswith("python.exe") or exe_path.endswith("pythonw.exe"):
            # 使用pythonw.exe避免显示控制台窗口
            pythonw_path = exe_path.replace("python.exe", "pythonw.exe").replace("pythonw.exe", "pythonw.exe")
            command = f'"{pythonw_path}" "{script_path}"'
        else:
            command = f'"{exe_path}"'
        
        # 注册表路径
        reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "MouseTrailEffect"
        
        try:
            # 打开注册表
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_ALL_ACCESS)
            
            # 检查当前状态
            try:
                current_value, _ = winreg.QueryValueEx(key, app_name)
                is_enabled = True
            except FileNotFoundError:
                is_enabled = False
            
            # 切换状态
            if is_enabled:
                # 删除开机启动项
                winreg.DeleteValue(key, app_name)
                config["auto_start"] = False
                messagebox.showinfo("成功", "已禁用开机启动")
            else:
                # 添加开机启动项
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, command)
                config["auto_start"] = True
                messagebox.showinfo("成功", "已启用开机启动")
            
            winreg.CloseKey(key)
            
            # 保存配置
            save_config()
            
        except Exception as e:
            messagebox.showerror("错误", f"设置开机启动失败: {e}")
    
    def exit_program(self):
        """退出整个程序（从配置窗口调用）"""
        # 尝试从父窗口获取DesktopTrail实例
        desktop_trail_instance = None
        if hasattr(self.parent, 'exit_program_from_tray'):
            # 如果父窗口有exit_program_from_tray方法，直接调用
            self.parent.exit_program_from_tray()
        else:
            # 否则使用原来的退出逻辑
            response = messagebox.askyesno("确认退出", "确定要退出鼠标拖尾程序吗？")
            if response:
                # 先关闭配置窗口
                self.window.destroy()
                # 然后关闭主程序
                if self.parent and hasattr(self.parent, 'destroy'):
                    self.parent.destroy()
                    print("[INFO] 程序已退出")
                else:
                    # 如果直接运行配置窗口，退出整个应用程序
                    import sys
                    sys.exit(0)

# 主窗口
class DesktopTrail:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 1)
        self.root.configure(bg="#000000")
        self.root.wm_attributes("-transparentcolor", "#000000")

        self.canvas = tk.Canvas(self.root, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.root.update()
        self.root.update_idletasks()

        # 关键：正确获取窗口句柄并开启穿透
        hwnd = user32.GetParent(self.root.winfo_id())
        if not hwnd:
            hwnd = self.root.winfo_id()

        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x00080000
        WS_EX_TRANSPARENT = 0x00000020
        WS_EX_TOPMOST = 0x00000008
        WS_EX_TOOLWINDOW = 0x00000080

        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE,
            style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST | WS_EX_TOOLWINDOW)

        # 配置管理器
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.config_manager = ConfigManager(self.screen_width, self.screen_height)
        self.particles = []
        self.last_mouse_pos = (0, 0)
        self.spawn_counter = 0  # 粒子生成间隔计数器
        
        # 系统托盘图标
        self.tray_icon = None
        self.tray_thread = None
        
        # 程序启动时立即应用配置
        self.apply_config_on_start()
        
        # 创建系统托盘图标
        self.create_system_tray()
        
        # 显示启动通知
        self.show_startup_notification()
        
        self.loop()



    def open_config_window(self):
        ConfigWindow(self.root)
    
    def create_system_tray(self):
        """创建系统托盘图标"""
        if not SYSTRAY_AVAILABLE:
            print("[WARN] pystray库未安装，使用传统配置按钮")
            # 回退到传统配置按钮
            self.create_fallback_button()
            return
        
        try:
            # 创建托盘图标图像
            image = self.create_tray_icon_image()
            
            # 定义托盘菜单
            menu = (
                item('打开配置', self.open_config_window),
                item('重新加载配置', self.reload_config),
                item('显示状态', self.show_status_notification),
                item('昨天软件开发', None),  # 分隔线
                item('退出程序', self.exit_program_from_tray)
            )
            
            # 创建系统托盘图标
            self.tray_icon = pystray.Icon(
                "mouse_trail",
                image,
                "鼠标拖尾效果By昨天软件开发",
                menu
            )
            
            # 在新线程中运行系统托盘
            self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            self.tray_thread.start()
            
            print("[OK] 系统托盘图标已创建")
            
        except Exception as e:
            print(f"[ERROR] 创建系统托盘失败: {e}")
            print("[INFO] 回退到传统配置按钮")
            self.create_fallback_button()
    
    def create_tray_icon_image(self):
        """创建托盘图标图像"""
        # 创建一个简单的图标：一个鼠标指针和拖尾效果
        image = Image.new('RGB', (64, 64), color='#333333')
        draw = ImageDraw.Draw(image)
        
        # 绘制鼠标指针形状
        draw.polygon([(32, 10), (50, 32), (42, 42), (32, 32)], fill='#4ECDC4')
        draw.polygon([(32, 32), (22, 42), (32, 42)], fill='#4ECDC4')
        
        # 绘制拖尾效果
        for i in range(3):
            x = 32 - i * 8
            y = 32 + i * 8
            size = 5 - i
            draw.ellipse([x-size, y-size, x+size, y+size], fill='#FF6B6B', outline='#FF6B6B')
        
        return image
    
    def create_fallback_button(self):
        """创建回退的传统配置按钮（当系统托盘不可用时）"""
        # 创建一个小的透明窗口作为配置按钮
        self.config_btn_window = tk.Toplevel(self.root)
        self.config_btn_window.overrideredirect(True)
        self.config_btn_window.attributes("-topmost", True)
        self.config_btn_window.attributes("-alpha", 0.8)
        
        # 将按钮放在屏幕右下角
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        button_width = 100
        button_height = 40
        padding = 10
        
        x_pos = screen_width - button_width - padding
        y_pos = screen_height - button_height - padding
        
        self.config_btn_window.geometry(f"{button_width}x{button_height}+{x_pos}+{y_pos}")
        self.config_btn_window.configure(bg="#333333")
        
        config_btn = tk.Button(self.config_btn_window, text="配置", 
                              command=self.open_config_window, 
                              bg="#555555", fg="white",
                              relief="flat", font=("Arial", 10))
        config_btn.pack(fill="both", expand=True)
        
        # 设置配置按钮窗口为可点击
        config_hwnd = user32.GetParent(self.config_btn_window.winfo_id())
        if not config_hwnd:
            config_hwnd = self.config_btn_window.winfo_id()
        
        GWL_EXSTYLE = -20
        WS_EX_TRANSPARENT = 0x00000020
        
        style = user32.GetWindowLongW(config_hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(config_hwnd, GWL_EXSTYLE,
            style & ~WS_EX_TRANSPARENT)
        
        print(f"[INFO] 传统配置按钮位置: 右下角 ({x_pos}, {y_pos})")
    
    def reload_config(self):
        """重新加载配置"""
        global config
        load_config()
        
        # 更新全局变量
        global COLOR_START, COLOR_END, PARTICLE_MAX_LIFE, PARTICLE_SPEED, PARTICLE_SIZE, SPAWN_COUNT
        global TRAIL_TYPE, IMAGE_PATH, TEXT_CONTENT, TEXT_SIZE, TEXT_FONT, TEXT_OPACITY, CLICK_TEXTS, CLICK_TEXT_SIZE, CLICK_TEXT_OPACITY
        global ONLY_WHEN_MOVING, TRAIL_ENABLED, ALWAYS_TRAIL, CLICK_EFFECT_ENABLED, AUTO_START
        global ROTATION_SPEED, SPAWN_INTERVAL, OPACITY_MODE, PARTICLE_SHAPE, COLLISION_ENABLED, GRAVITY_ENABLED
        global FOLLOW_MOUSE, TRAIL_PARTICLES, COLOR_MODE, RAINBOW_SPEED, RANDOM_COLORS
        global CLICK_ANIMATION, CLICK_DIRECTION, CLICK_DURATION
        
        COLOR_START = config["color_start"]
        COLOR_END = config["color_end"]
        PARTICLE_MAX_LIFE = config["particle_max_life"]
        PARTICLE_SPEED = config["particle_speed"]
        PARTICLE_SIZE = config["particle_size"]
        SPAWN_COUNT = config["spawn_count"]
        TRAIL_TYPE = config["trail_type"]
        IMAGE_PATH = config["image_path"]
        TEXT_CONTENT = config["text_content"]
        TEXT_SIZE = config.get("text_size", 24)
        TEXT_FONT = config.get("text_font", "Arial")
        TEXT_OPACITY = config.get("text_opacity", 100)
        CLICK_TEXTS = config["click_texts"]
        CLICK_TEXT_SIZE = config.get("click_text_size", 36)
        CLICK_TEXT_OPACITY = config.get("click_text_opacity", 100)
        CLICK_ANIMATION = config.get("click_animation", "float")
        CLICK_DIRECTION = config.get("click_direction", "center")
        CLICK_DURATION = config.get("click_duration", 100)
        ONLY_WHEN_MOVING = config["only_when_moving"]
        TRAIL_ENABLED = config["trail_enabled"]
        ALWAYS_TRAIL = config["always_trail"]
        CLICK_EFFECT_ENABLED = config["click_effect_enabled"]
        COLLISION_ENABLED = config.get("collision_enabled", False)
        GRAVITY_ENABLED = config.get("gravity_enabled", False)
        FOLLOW_MOUSE = config.get("follow_mouse", True)
        TRAIL_PARTICLES = config.get("trail_particles", False)
        ROTATION_SPEED = config.get("rotation_speed", 1.0)
        SPAWN_INTERVAL = config.get("spawn_interval", 2)
        OPACITY_MODE = config.get("opacity_mode", "linear")
        PARTICLE_SHAPE = config.get("particle_shape", "circle")
        COLOR_MODE = config.get("color_mode", "linear")
        RAINBOW_SPEED = config.get("rainbow_speed", 1.0)
        RANDOM_COLORS = config.get("random_colors", False)
        AUTO_START = config.get("auto_start", False)
        
        # 如果是图片拖尾类型，重新加载图片
        if TRAIL_TYPE == "image" and IMAGE_PATH:
            self.config_manager.load_image()
        
        # 显示通知
        self.show_notification("配置已重新加载", "鼠标拖尾效果配置已更新")
    
    def show_status_notification(self):
        """显示状态通知"""
        status_text = f"""
当前状态:
- 拖尾类型: {TRAIL_TYPE}
- 拖尾启用: {TRAIL_ENABLED}
- 点击效果: {CLICK_EFFECT_ENABLED}
- 粒子数量: {SPAWN_COUNT}
- 粒子大小: {PARTICLE_SIZE}
"""
        self.show_notification("鼠标拖尾状态", status_text)
    
    def show_startup_notification(self):
        """显示启动通知"""
        self.show_notification(
            "鼠标拖尾效果已启动",
            f"程序已在后台运行\n拖尾类型: {TRAIL_TYPE}\n右键点击系统托盘图标进行配置",
            duration=5
        )
    
    def show_notification(self, title, message, duration=3):
        """显示系统通知"""
        if not SYSTRAY_AVAILABLE:
            # 如果pystray不可用，使用Tkinter的消息框
            print(f"[NOTIFY] {title}: {message}")
            return
        
        try:
            # 使用pystray的通知功能
            if hasattr(self.tray_icon, 'notify'):
                self.tray_icon.notify(message, title)
            else:
                # 如果pystray版本不支持notify，打印到控制台
                print(f"[NOTIFY] {title}: {message}")
        except Exception as e:
            print(f"[ERROR] 显示通知失败: {e}")
            print(f"[NOTIFY] {title}: {message}")
    
    def exit_program_from_tray(self):
        """从系统托盘退出程序"""
        response = messagebox.askyesno("确认退出", "确定要退出鼠标拖尾程序吗？")
        if response:
            # 停止系统托盘
            if self.tray_icon:
                self.tray_icon.stop()
            
            # 关闭主窗口
            self.root.destroy()
            
            # 退出程序
            import sys
            sys.exit(0)
    
    def apply_config_on_start(self):
        """程序启动时应用配置"""
        print("[INFO] 程序启动，应用当前配置...")
        
        # 如果是图片拖尾类型，立即加载图片
        if TRAIL_TYPE == "image" and IMAGE_PATH:
            self.config_manager.load_image()
            if self.config_manager.image_cache:
                print(f"[OK] 已加载图片: {IMAGE_PATH}")
            else:
                print(f"[WARN] 无法加载图片: {IMAGE_PATH}")
        
        # 打印当前配置状态
        print(f"[CONFIG] 拖尾类型: {TRAIL_TYPE}")
        print(f"[CONFIG] 拖尾启用: {TRAIL_ENABLED}")
        print(f"[CONFIG] 仅移动时显示: {ONLY_WHEN_MOVING}")
        print(f"[CONFIG] 一直显示: {ALWAYS_TRAIL}")
        print(f"[CONFIG] 点击效果启用: {CLICK_EFFECT_ENABLED}")

    def create_particle(self, x, y):
        if TRAIL_TYPE == "star":
            return StarParticle(x, y)
        elif TRAIL_TYPE == "heart":
            return HeartParticle(x, y)
        elif TRAIL_TYPE == "image":
            if self.config_manager.image_cache is None:
                self.config_manager.load_image()
            if self.config_manager.image_cache:
                return ImageParticle(x, y, self.config_manager.image_cache)
        elif TRAIL_TYPE == "text":
            return TextParticle(x, y, TEXT_CONTENT, TEXT_SIZE, TEXT_FONT, TEXT_OPACITY)
        # 默认圆形粒子
        return Particle(x, y)

    def loop(self):
        self.canvas.delete("all")
        mx, my = get_cursor_pos()
        
        # 检测鼠标是否移动
        self.config_manager.is_mouse_moving((mx, my))
        
        # 检测鼠标点击
        if self.config_manager.check_mouse_click():
            # 在鼠标位置创建点击文字粒子
            self.config_manager.create_click_particle(mx, my)
        
        # 根据配置决定是否生成拖尾粒子
        if self.config_manager.should_spawn_particles():
            # 使用间隔控制粒子生成频率
            self.spawn_counter += 1
            if self.spawn_counter >= SPAWN_INTERVAL:
                self.spawn_counter = 0
                for _ in range(SPAWN_COUNT):
                    self.particles.append(self.create_particle(mx, my))

        # 更新和绘制拖尾粒子
        alive = []
        for p in self.particles:
            if p.update(self.screen_width, self.screen_height):
                p.draw(self.canvas)
                alive.append(p)
        self.particles = alive
        
        # 更新和绘制点击粒子
        click_particles = self.config_manager.update_click_particles()
        for p in click_particles:
            p.draw(self.canvas)

        self.root.after(16, self.loop)

    def start(self):
        self.root.mainloop()

if __name__ == "__main__":
    print("[OK] 鼠标粒子拖尾增强版（已开启鼠标穿透）")
    print("[FILE] 配置文件: mouse_trail_config.json")
    print("[TRAY] 系统托盘: 右键点击系统托盘图标进行配置")
    if not SYSTRAY_AVAILABLE:
        print("[WARN] pystray库未安装，将使用传统配置按钮")
        print("[INFO] 请安装: pip install pystray")
    print("[SETTINGS] 功能说明:")
    print("   - 支持圆形、星星、爱心、图片、文字拖尾")
    print("   - 爱心效果增强，更明显")
    print("   - 文字拖尾：可自定义任意文字/Emoji")
    print("   - 点击效果：左键点击随机显示文字")
    print("   - 可配置颜色、大小、速度、数量")
    print("   - 开关：启用/禁用拖尾")
    print("   - 开关：仅移动时显示/一直显示")
    print("   - 开关：启用鼠标点击效果")
    print("[ANIMATIONS] 动画效果:")
    print("   - 碰撞效果：粒子与边界碰撞反弹")
    print("   - 重力效果：粒子受重力影响")
    print("   - 跟随鼠标：粒子向鼠标方向移动")
    print("   - 粒子拖尾：粒子产生次级拖尾")
    print("   - 多种透明度模式：线性/淡入/淡出/脉冲")
    print("   - 多种粒子形状：圆形/方形/三角形/菱形/六边形")
    print("   - 多种颜色模式：线性/径向/彩虹/渐变")
    print("   - 点击动画：浮动/爆炸/旋转/淡入淡出/弹跳")
    print("   - 点击方向：中心/上/下/左/右/随机")
    print("[NOTIFY] 系统托盘: 程序启动时会显示通知")
    print("[CLOSE] 关闭: 通过系统托盘菜单退出程序")
    print("=" * 50)
    
    try:
        app = DesktopTrail()
        app.start()
    except Exception as e:
        print(f"[ERROR] 程序错误: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")