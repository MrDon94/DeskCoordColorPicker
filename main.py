import tkinter as tk
from PIL import ImageTk, Image, ImageDraw
import pyautogui
import pyperclip
from io import BytesIO
import win32clipboard
import keyboard
import pystray
import os

def on_motion(event):
    root.attributes('-topmost', False)  # 关闭主窗口置顶
    x, y = pyautogui.position()  # 获取鼠标当前在屏幕上的坐标
    color = pyautogui.pixel(x, y)
    global hex_color
    hex_color = RGB_to_HEX(color)
    new_text = "鼠标坐标：({},{}),颜色值：{}".format(x, y, hex_color)
    sub_label_content.config(text=new_text)
    sub_label_color_tip.config(bg=hex_color)

    # 计算子窗口显示的合适位置
    w, h = pyautogui.size()
    sub_x = x
    sub_y = y
    offset_x = 10
    offset_y = 10
    if w - sub_x < sub_win_width:
        sub_x = sub_x - sub_win_width
        offset_x = -10
    if h - sub_y < sub_win_height:
        sub_y = sub_y - sub_win_height
        offset_y = -10
    sub_win.geometry(f"+{sub_x + offset_x}+{sub_y + offset_y}")

    # 截取鼠标周围100x100区域的部分
    img_size = 50
    left = max(-img_size, x - img_size)
    top = max(-img_size, y - img_size)
    right = min(screenshot.width + img_size, x + img_size)
    bottom = min(screenshot.height + img_size, y + img_size)
    region = screenshot.crop((left, top, right, bottom))
    # 放大图像（2倍）
    enlarged_region = region.resize((region.width * 2, region.height * 2), Image.NEAREST)

    # 在图像上创建一个绘画对象
    draw = ImageDraw.Draw(enlarged_region)
    line_width = 2
    draw.rectangle([(img_size-line_width, img_size-line_width),
                    (enlarged_region.width-img_size+line_width, enlarged_region.height-img_size+line_width)],
                   outline='red', width=line_width)
    # 绘制红色的垂直线
    draw.line([(enlarged_region.width // 2, 0), (enlarged_region.width // 2, enlarged_region.height)],
              fill='red', width=line_width)
    # 绘制红色的水平线
    draw.line([(0, enlarged_region.height // 2), (enlarged_region.width, enlarged_region.height // 2)],
              fill='red', width=line_width)

    # 显示带有十字瞄准线的图像
    enlarged_image_with_crosshair = ImageTk.PhotoImage(enlarged_region)
    sub_frame_top_label.configure(image=enlarged_image_with_crosshair)
    sub_frame_top_label.image = enlarged_image_with_crosshair


def on_click(event):
    on_motion(event)
    root.unbind('<Motion>')
    root.unbind('<Button-1>')
    sub_win.unbind('<Motion>')
    sub_win.unbind('<Button-1>')
    sub_frame_bottom.pack()


def on_quit(event):
    keycode = event.keycode
    print("按键码：{}".format(keycode))
    # 按Esc退出程序
    if keycode == 27:
        click_btn_close()


# 关闭
def click_btn_close():
    root.destroy()
    keyboard.add_hotkey('ctrl+alt+x', on_hotkey)


# 确定
def click_btn_confirm():
    output = BytesIO()
    screenshot.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()
    root.destroy()


def click_btn_copy():
    print("复制颜色值：{}".format(hex_color))
    pyperclip.copy(hex_color)
    root.destroy()


def RGB_to_HEX(rgb):
    r, g, b = rgb[0], rgb[1], rgb[2]
    hex_code = "#{:02x}{:02x}{:02x}".format(r, g, b)
    return hex_code

def on_hotkey():
    keyboard.remove_hotkey('ctrl+alt+x')
    global root
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    # 获取电脑屏幕的大小
    print("电脑的分辨率是%dx%d" % (screen_width, screen_height))
    root.geometry('{}x{}'.format(screen_width, screen_height))  # 设置窗口大小
    root.attributes('-topmost', True)  # 将窗口置于顶层
    root.state("zoomed")  # 设置窗口最大化
    # 隐藏菜单栏
    root.overrideredirect(True)

    global screenshot
    # 截取整个屏幕的图像
    screenshot = pyautogui.screenshot()

    # 调整图像大小为屏幕尺寸
    screenshot = screenshot.resize((screen_width, screen_height))

    # 创建一个新的图像对象，并复制原始截图
    bordered_image = Image.new('RGB', (screen_width, screen_height), color=(0, 0, 0))
    bordered_image.paste(screenshot, (0, 0))

    # 绘制红色边框
    draw = ImageDraw.Draw(bordered_image)
    border_width = 2
    border_color = 'red'
    draw.rectangle([0, 0, screen_width - border_width, screen_height - border_width],
                   outline=border_color, width=border_width)

    # 转换为ImageTk.PhotoImage对象
    image = ImageTk.PhotoImage(bordered_image)
    # 创建一个Label用于显示背景图片
    label = tk.Label(root, image=image)
    label.pack(fill=tk.BOTH, expand=True)

    # 计算子窗口居中时的位置
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - sub_win_width) // 2
    y = (screen_height - sub_win_height) // 2

    # 创建子窗口
    global sub_win
    sub_win = tk.Toplevel(root, width=sub_win_width, height=sub_win_height)
    sub_win.geometry(f"{sub_win_width}x{sub_win_height}+{x}+{y}")
    sub_win.attributes('-topmost', True)  # 将窗口置于顶层
    sub_win.overrideredirect(True)
    sub_win.config(bg="#ebebeb")
    sub_win.attributes("-alpha", 0.8)

    # 向子窗口添加控件
    sub_frame = tk.Frame(sub_win)
    sub_frame.pack()

    global sub_frame_top_label
    sub_frame_top = tk.Frame(sub_frame)
    sub_frame_top_label = tk.Label(sub_frame_top, width=100, height=100, bg="#FFFF00")
    sub_frame_top_label.pack(side='left', fill=tk.BOTH)
    sub_frame_top.pack()

    global sub_label_content, sub_label_color_tip
    sub_frame_middle = tk.Frame(sub_frame)
    sub_label_content = tk.Label(sub_frame_middle, text="这是一个子窗口")
    sub_label_content.pack(side='left')
    sub_label_color_tip = tk.Label(sub_frame_middle, width=2, height=1, bg='#7CCD7C')
    sub_label_color_tip.pack(side='left')
    sub_frame_middle.pack()

    global sub_frame_bottom
    sub_frame_bottom = tk.Frame(sub_frame)
    tk.Button(sub_frame_bottom, text='关闭', bg='#FFFFFF', width=10, height=1, command=click_btn_close).pack(
        side='left')
    tk.Button(sub_frame_bottom, text='复制截图', bg='#FFFFFF', width=10, height=1, command=click_btn_confirm).pack(
        side='left')
    tk.Button(sub_frame_bottom, text='复制颜色值', bg='#FFFFFF', width=10, height=1, command=click_btn_copy).pack(
        side='left')

    # 绑定鼠标移动事件
    root.bind('<Motion>', on_motion)
    sub_win.bind('<Motion>', on_motion)
    # 绑定按键点击事件
    root.bind('<Key>', on_quit)
    sub_win.bind('<Key>', on_quit)
    # 绑定鼠标单机左键事件
    root.bind('<Button-1>', on_click)
    sub_win.bind('<Button-1>', on_click)

    # 运行主循环
    root.mainloop()


def on_activate(icon, item):
    icon.stop()
    os._exit(0)


def create_icon():
    # 替换为你的图片的完整路径
    icon_path = "F:\\PycharmProjects\\DeskCoordColorPicker\\er_ha.jpg"
    image = Image.open(icon_path)
    icon = pystray.Icon("name", image, "桌面坐标颜色拾取器", menu=pystray.Menu(pystray.MenuItem('退出', on_activate)))
    icon.run()


# if __name__ == '__main__':
pyautogui.alert(text="服务已启动，按下ctrl+alt+x组合热键开始截图")
hex_color = ""
# 定义子窗口的宽高
sub_win_width = 280
sub_win_height = 170
# 注册热键（这里设置为按下Ctrl+Alt+X时触发）
keyboard.add_hotkey('ctrl+alt+x', on_hotkey)
create_icon()
# 监听键盘事件
keyboard.wait()