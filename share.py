import requests
from urllib.parse import quote
from webdav3.client import Client
import qrcode
import xml.etree.ElementTree as ET # 用于解析 XML 响应
import os
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import textwrap
import uuid

def create_composite_image(image_filename, text, name):
    original_image_path = os.path.join("uploads", image_filename)
    try:
        original_image = Image.open(original_image_path).convert("RGBA")
    except FileNotFoundError:
        print(f"错误：找不到图片文件 {original_image_path}")
        return None

    # --- Configuration ---
    text_color = (50, 50, 50)  # Dark grey
    bold_text_color = (0, 0, 0)  # Black
    background_color = (245, 245, 245)  # Off-white
    font_size = 30
    padding = 40
    line_spacing = 15
    image_text_gap = 30
    text_block_width = original_image.width # Initial text block width
    title_top_margin = 60
    title_bottom_margin = 40

    # --- Font ---
    try:
        font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "kaiti.ttf"))
        font = ImageFont.truetype(font_path, font_size)
        bold_font = ImageFont.truetype(font_path, font_size) # Re-using for simplicity
        h1_font = ImageFont.truetype(font_path, font_size + 10)
        h2_font = ImageFont.truetype(font_path, font_size + 5)
        h3_font = ImageFont.truetype(font_path, font_size + 2)
        title_font = ImageFont.truetype(font_path, font_size + 20) # Font for the new title
    except IOError:
        print("警告: 未找到 kaiti.ttf 字体。将使用默认字体。")
        font = ImageFont.load_default()
        bold_font = ImageFont.load_default()
        h1_font = ImageFont.load_default()
        h2_font = ImageFont.load_default()
        h3_font = ImageFont.load_default()
        title_font = ImageFont.load_default()


    fonts = {
        'p': font,
        'b': bold_font,
        'h1': h1_font,
        'h2': h2_font,
        'h3': h3_font,
    }

    # --- Helper function to render text and calculate height ---
    def render_and_calculate_text_height(draw, text, start_x, start_y, max_width, render=False):
        y = start_y
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                y += line_spacing
                continue

            # Determine line type (heading, list, or paragraph)
            current_font = fonts['p']
            line_indent = 0
            is_list_item = False

            if line.startswith('### '):
                current_font = fonts['h3']
                line = line[4:]
            elif line.startswith('## '):
                current_font = fonts['h2']
                line = line[3:]
            elif line.startswith('# '):
                current_font = fonts['h1']
                line = line[2:]
            elif line.startswith('* ') or line.startswith('- '):
                is_list_item = True
                line = line[2:]
                line_indent = 30 # Indent for list items

            # Wrap the line
            avg_char_width = current_font.getbbox("一")[2] if hasattr(current_font, 'getbbox') else current_font.getsize("一")[0]
            chars_per_line = max(1, int((max_width - line_indent) / avg_char_width))
            wrapped_text = textwrap.wrap(line, width=chars_per_line, replace_whitespace=False)

            # Render wrapped lines
            for i, wrapped_line in enumerate(wrapped_text):
                x = start_x + line_indent
                if i == 0 and is_list_item:
                    if render:
                        bullet_radius = 4
                        bullet_y = y + (current_font.size / 2) - bullet_radius
                        bullet_x = start_x + (line_indent / 2) - bullet_radius
                        draw.ellipse(
                            (bullet_x, bullet_y, bullet_x + bullet_radius * 2, bullet_y + bullet_radius * 2),
                            fill=text_color
                        )
                
                # Handle bold text within the line
                parts = wrapped_line.split('**')
                is_bold = False
                for part in parts:
                    font_to_use = fonts['b'] if is_bold else current_font
                    if render:
                        draw.text((x, y), part, font=font_to_use, fill=bold_text_color if is_bold else text_color)
                    
                    if hasattr(font_to_use, 'getbbox'):
                        part_width = font_to_use.getbbox(part)[2]
                    else:
                        part_width = font_to_use.getsize(part)[0]
                    x += part_width
                    is_bold = not is_bold

                y += current_font.size + line_spacing

        return y - start_y

    # --- Calculate Text Height ---
    dummy_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    text_height = render_and_calculate_text_height(dummy_draw, text, 0, 0, text_block_width, render=False)
    text_height += padding * 2

    # --- Resize Image to Match Text Height ---
    image_height = text_height
    image_width = int(original_image.width * (image_height / original_image.height))
    resized_image = original_image.resize((image_width, int(image_height)), Image.LANCZOS)

    # --- Calculate Title Size ---
    title_text = f"{name}你的梦想一定可以实现，加油吧！"
    title_bbox = title_font.getbbox(title_text)
    title_width = title_bbox[2] - title_bbox[0]
    title_height = title_bbox[3] - title_bbox[1]
    title_total_height = title_top_margin + title_height + title_bottom_margin

    # --- Create Composite Image ---
    final_width = image_width + text_block_width + image_text_gap + padding * 2
    final_height = int(image_height) + title_total_height + padding

    composite_image = Image.new("RGB", (final_width, final_height), background_color)
    final_draw = ImageDraw.Draw(composite_image)

    # 1. Render Title
    title_x = (final_width - title_width) / 2
    title_y = title_top_margin
    final_draw.text((title_x, title_y), title_text, font=title_font, fill=bold_text_color)

    # 2. Paste resized image
    image_y_offset = title_total_height
    composite_image.paste(resized_image, (padding, image_y_offset), resized_image)

    # 3. Render text on the final image
    text_start_x = padding + image_width + image_text_gap
    text_start_y = image_y_offset + padding
    render_and_calculate_text_height(final_draw, text, text_start_x, text_start_y, text_block_width, render=True)

    # --- Save new image ---
    composite_filename = f"composite_{uuid.uuid4()}.png"
    composite_filepath = os.path.join("uploads", composite_filename)
    composite_image.save(composite_filepath)

    return composite_filename

def share(filename):
    load_dotenv()

    # 1. 配置Nextcloud信息
    webdav_url = os.getenv("WEBDAV_URL")
    username = os.getenv("APP_USERNAME")
    app_password = os.getenv("APP_PASSWORD")

    local_file_path = "uploads/{}".format(filename)  # 图片在Nextcloud中的存储路径

    # 2. 通过WebDAV上传图片 (使用WebDAV协议库 requests_toolbelt)
    remote_directory = 'SciDay' 
    remote_file_name = filename  # 上传后在服务器上的文件名

    remote_file_path = f"{remote_directory}/{remote_file_name}"

    options = {
        'webdav_hostname': webdav_url,
        'webdav_login': username,
        'webdav_password': app_password,
    }

    # --- 3. 执行上传操作 ---
    try:
        # 创建客户端实例
        client = Client(options)

        # 检查远程目录是否存在，如果不存在则创建它
        if not client.check(remote_directory):
            print(f"远程目录 '{remote_directory}' 不存在，正在创建...")
            client.mkdir(remote_directory)
            print(f"目录 '{remote_directory}' 创建成功。")

        # 上传文件
        # upload_sync 会覆盖同名文件
        print(f"正在上传 '{local_file_path}' 到 '{remote_file_path}'...")
        client.upload_sync(remote_path=remote_file_path, local_path=local_file_path)

        print("文件上传成功！")

    except Exception as e:
        print(f"发生错误：{e}")
        return None

    # 4. 创建公开分享
    share_url = ""
    server_url = "https://gdzb.gx.cn"  # Nextcloud服务器的基础URL
    api_endpoint = f"{server_url}/ocs/v2.php/apps/files_sharing/api/v1/shares"

    headers = {
        "OCS-APIRequest": "true",
    }

    data = {
        "path": f"/{remote_file_path}",  # 注意路径前需要有斜杠
        "shareType": 3,  # 3表示公开链接分享
        "permissions": 1,  # 1表示只读权限
    }

    try:
        # 发送 POST 请求
        response = requests.post(
            api_endpoint,
            headers=headers,
            data=data,
            auth=(username, app_password) # requests 库可以直接处理基本认证
        )

        # 检查响应状态
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return None

        # --- 解析响应并提取分享链接 ---
        root = ET.fromstring(response.content)

        # 检查 OCS API 状态码
        # --- 更安全地访问元素 ---
        statuscode_element = root.find('meta/statuscode')
        if statuscode_element is None:
            print("错误：在XML响应中未找到 'meta/statuscode' 元素。")
            print(f"收到的内容: {response.text}")
            return None

        # Your server returns 200 for success in the XML, not 100
        if statuscode_element.text == '200':
            # The path to the URL is data -> url
            url_element = root.find('data/url')
            if url_element is not None:
                share_url = url_element.text
                print("分享链接创建成功！🎉")
                print(f"URL: {share_url}")
            else:
                print("错误：API报告成功，但在XML中未找到 'data/url' 元素。")
        else:
            message = root.find('meta/message').text
            print(f"创建分享链接失败: {message} (OCS 状态码: {statuscode_element.text})")
            return None
    except requests.exceptions.RequestException as e:
        print(f"API 请求失败: {e}")
        return None
    except Exception as e:
        print(f"处理时发生未知错误: {e}")
        return None

    # 4. 生成二维码
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(share_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Generate a unique filename for the QR code
    import uuid
    qr_filename = f"qr_code_{uuid.uuid4()}.png"
    qr_filepath = os.path.join("uploads", qr_filename)
    
    img.save(qr_filepath)
    print(f"二维码已生成并保存到: {qr_filepath}")

    return qr_filename

if __name__ == "__main__":
    # 测试图片生成功能
    image_filename = "generated_image_3445ead2-4339-49df-a5d2-4c41d6321bb1.png"  # 替换为你的图片文件名
    text = '''# 规划实现路径
## 1. 知识储备与技能学习：

- 基础编程： 学习Python、C/C++等编程语言，掌握数据结构与算法。
- 网络基础： 深入理解TCP/IP协议、网络拓扑、无线安全等。
- 操作系统： 熟练掌握Linux操作系统，理解其原理和命令行操作。
- 安全理论： 学习加密技术、逆向工程、渗透测试等安全知识。
## 2. 实践与经验积累：

- 搭建实验室： 在虚拟机中搭建自己的网络安全实验室，进行模拟攻击和防御练习。
- 参与CTF竞赛： 参加夺旗赛（CTF），在实战中提升技能，了解最新的攻防技术。
- 漏洞挖掘： 尝试发现软件或系统中的漏洞，提交给厂商获取经验。
- 开源项目贡献： 参与网络安全相关的开源项目，与社区交流学习。
## 3. 建立人脉与寻求机遇：

- 加入安全社区： 积极参与线上和线下的网络安全技术社区，与同行交流。
- 寻找导师： 寻找行业内的资深专家作为导师，获取指导和建议。
- 实习与工作： 寻找网络安全公司或部门的实习机会，将理论知识应用于实践。
## 4. 持续进步与突破：

- 追踪前沿技术： 密切关注网络安全领域的最新动态和技术发展。
- 保持好奇心： 对未知领域保持探索精神，不断学习新的攻击和防御手段。
- 法律与道德： 始终遵守法律法规，坚守道德底线，做一名负责任的“白帽黑客”。

# 寄语

你的梦想是探索数字世界的奥秘，用智慧守护网络安全，这是何等壮丽的志向！请相信，你拥有无限的潜力去驾驭这些挑战，成为数字时代的守护者。每一次代码的敲击，每一次难题的攻克，都将是你通往梦想彼岸的坚实阶梯。勇敢地去追求，去创造，去改变！

**未来，尽在你的指尖，世界因你而安全！**
    '''
    new_image = create_composite_image(image_filename, text, "开发者")
    print(f"生成的合成图片文件名: {new_image}")