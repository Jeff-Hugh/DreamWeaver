import requests
from urllib.parse import quote
from webdav3.client import Client
import qrcode
import xml.etree.ElementTree as ET # 用于解析 XML 响应
import os
from dotenv import load_dotenv

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
    img.save("share_qrcode.png")  # 保存二维码图片，之后可在你的APP界面显示
    print("二维码已生成！")

    return share_url