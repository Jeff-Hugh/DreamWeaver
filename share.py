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

def create_composite_image(image_filename, text):
    original_image_path = os.path.join("uploads", image_filename)
    try:
        original_image = Image.open(original_image_path).convert("RGBA")
    except FileNotFoundError:
        print(f"错误：找不到图片文件 {original_image_path}")
        return None

    # --- Configuration ---
    text_color = (224, 224, 224)
    bold_text_color = (255, 255, 255)
    background_color = (18, 18, 18)
    font_size = 30
    padding = 40
    line_spacing = 15
    image_text_gap = 30
    text_block_width = original_image.width # Initial text block width

    # --- Font ---
    try:
        # Build absolute path to the font file, assuming it's in the same directory as the script.
        font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "simhei.ttf"))
        font = ImageFont.truetype(font_path, font_size)
        # Load the regular font for bold as well to avoid index errors with single-style font files.
        bold_font = ImageFont.truetype(font_path, font_size)
    except IOError:
        print("警告: 未找到 simhei.ttf 字体或字体文件已损坏/不完整。将使用默认字体。")
        font = ImageFont.load_default()
        bold_font = ImageFont.load_default()

    # --- Helper function to render text and calculate height ---
    def render_and_calculate_text_height(draw, text, start_x, start_y, max_width, render=False):
        lines = text.replace('**', '').split('\n')
        
        wrapped_lines = []
        for line in lines:
            # Wrap long lines
            if not line.strip(): # Keep empty lines for paragraphs
                wrapped_lines.append('')
                continue
            
            # A simple character-based wrapping logic
            avg_char_width = font.getbbox("一")[2] if hasattr(font, 'getbbox') else font.getsize("一")[0]
            chars_per_line = max(1, int(max_width / avg_char_width))
            wrapped_lines.extend(textwrap.wrap(line, width=chars_per_line, replace_whitespace=False))

        y = start_y
        x = start_x
        
        # Simple markdown parsing for **bold**
        # This approach splits by `**` and toggles bold state.
        for line in wrapped_lines:
            parts = line.split('**')
            is_bold = False
            for i, part in enumerate(parts):
                current_font = bold_font if is_bold else font
                if render:
                    draw.text((x, y), part, font=current_font, fill=bold_text_color if is_bold else text_color)
                
                if hasattr(current_font, 'getbbox'):
                    part_width = current_font.getbbox(part)[2]
                else:
                    part_width = current_font.getsize(part)[0]
                x += part_width
                
                # Don't toggle bold for the last part
                if i < len(parts) - 1:
                    is_bold = not is_bold

            y += font_size + line_spacing
            x = start_x
            
        return y - start_y - line_spacing if wrapped_lines else 0

    # --- Calculate Text Height ---
    # Create a dummy image to calculate the text block height
    dummy_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    text_height = render_and_calculate_text_height(dummy_draw, text, 0, 0, text_block_width, render=False)
    text_height += padding * 2 # Add top and bottom padding to the text block

    # --- Resize Image to Match Text Height ---
    image_height = text_height
    image_width = int(original_image.width * (image_height / original_image.height))
    resized_image = original_image.resize((image_width, image_height), Image.LANCZOS)

    # --- Create Composite Image ---
    final_width = image_width + text_block_width + image_text_gap + padding * 2
    final_height = image_height
    
    composite_image = Image.new("RGB", (final_width, final_height), background_color)
    
    # 1. Paste resized image
    composite_image.paste(resized_image, (padding, 0), resized_image)

    # 2. Render text on the final image
    final_draw = ImageDraw.Draw(composite_image)
    text_start_x = padding + image_width + image_text_gap
    render_and_calculate_text_height(final_draw, text, text_start_x, padding, text_block_width, render=True)

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
