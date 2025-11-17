from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import os
import uuid
import json
from download_file import download_file
import base64
import mimetypes
from config import get_api_key

# ---用于 Base64 编码 ---
# 格式为 data:{mime_type};base64,{base64_data}
def encode_file(image_path):
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type or not mime_type.startswith("image/"):
        raise ValueError("不支持或无法识别的图像格式")

    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(
                image_file.read()).decode('utf-8')
        return f"data:{mime_type};base64,{encoded_string}"
    except IOError as e:
        raise IOError(f"读取文件时出错: {image_path}, 错误: {str(e)}")

def generate_dream_image_and_plan(dream: str = "成为一名畅销书作家", image_path: str = "/path/to/cat_image.png"):
    api_key = get_api_key("google")
    if not api_key:
        return "Google API key not found in config.ini", None
    client = genai.Client(api_key=api_key)

    prompt = (
        """# 指令：生成梦想实现后的未来图景

    请你扮演一个集艺术家、职业规划师和心灵导师于一身的AI。你的任务是根据用户提供的头像照片和他们的梦想，完成以下三项任务：

    ## **视觉化未来：生成梦想成真时的图像**
    * **核心元素:** 融合用户头像的面部特征，确保能看出是同一个人。人物脸部要特别明显，符合用户对未来的展望。请仔细辨别用户的性别、年龄和种族特征。
    * **场景设定:** 根据用户梦想，构建一个具体、生动的未来场景。例如，如果梦想是成为作家，场景可以是在一个阳光明媚的书房里，手捧着自己出版的畅销书；如果梦想是环游世界，场景可以是在异国他乡的标志性建筑前，面带笑容。
    * **风格要求:** 画面风格需积极、明亮、充满成就感和幸福感。可以是写实风格，也可以是带有艺术感的插画风格。
    * **人物状态:** 未来的人物形象要显得更加成熟、自信、充满活力。

    ## **规划实现路径**
    * **要求:** 提供清晰的行动指南
    * **目标拆解:** 将用户的宏大梦想拆解成3到5个可执行的关键步骤。
    * **路径规划:** 每个步骤都应清晰、具体，具有可操作性。例如：
        * 第一步：知识储备与技能学习（建议学习哪些课程、阅读哪些书籍）。
        * 第二步：实践与经验积累（建议参加哪些项目、实习或活动）。
        * 第三步：建立人脉与寻求机遇（建议如何拓展社交圈、寻找导师）。
        * 第四步：持续进步与突破（面对瓶颈时如何调整）。

    ## **寄语**
    * **要求:** 赋予精神力量，撰写一段激励人心的话语
    * **内容核心:** 肯定用户梦想的价值，鼓励他们相信自己的潜力。
    * **情感基调:** 真诚、温暖、有力量，能够激发用户的内在动力。
    * **结尾:** 用一句强有力的口号或祝福来结束。

    **总要求：** 文字部分总字数不超过500字。
    ---
    **现在，根据图片生成未来图像.**
    **用户的梦想是：{}**
    """.format(dream),
    )

    image = Image.open(image_path)

    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[prompt, image],
    )

    response_text = ""
    response_image = None
    for part in response.candidates[0].content.parts:
        if part.text is not None:
            response_text += part.text
        elif part.inline_data is not None:
            response_image = Image.open(BytesIO(part.inline_data.data))
            image_filename = "generated_image_{}.png".format(uuid.uuid4())
            response_image.save(os.path.join("uploads", image_filename))
        else:
            continue

    return response_text, image_filename

def generate_dream_image_and_plan_qwen(dream: str = "成为一名畅销书作家", image_path: str = "/path/to/cat_image.png"):
    from dashscope import MultiModalConversation, Generation
    import dashscope

    dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'
    api_key = get_api_key("qwen")
    if not api_key:
        return "Qwen API key not found in config.ini", None

    # generate image with qwen-image-edit-plus model
    response_image = None
    
    image = encode_file(image_path)

    messages = [
        {"role": "user",
            "content": [{"image": image},
                        {"text": f"""
    请你扮演一个集艺术家、职业规划师和心灵导师于一身的AI。你的任务是根据提供的头像照片和未来梦想，完成图像创作：
    
    总体目标：视觉化未来，生成梦想成真时的图像；
    核心元素: 融合用户头像的面部特征，确保能看出是同一个人。人物脸部要特别明显，符合用户对未来的展望。请仔细辨别用户的性别、年龄和种族特征。
    场景设定: 根据用户梦想，构建一个具体、生动的未来场景。例如，如果梦想是成为作家，场景可以是在一个阳光明媚的书房里，手捧着自己出版的畅销书；如果梦想是环游世界，场景可以是在异国他乡的标志性建筑前，面带笑容。
    风格要求: 画面风格需积极、明亮、充满成就感和幸福感。写实风格。
    人物状态: 未来的人物形象要显得更加自信、充满活力。可以根据推理生成梦想实现时的年龄的形象。

    用户的梦想是：{dream}
        """}]
        }
    ]

    response = MultiModalConversation.call(
        api_key=api_key,
        model="qwen-image-edit-plus",
        messages=messages,
        stream=False,
        n=1,
        watermark=False,
        negative_prompt=" "
    )
    
    if response.status_code == 200:
        # 如需查看完整响应，请取消下行注释
        # print(json.dumps(response, ensure_ascii=False))
        for i, content in enumerate(response.output.choices[0].message.content):
            image_url = content['image']
            response_image = download_file(image_url, save_directory="uploads")
    else:
        print(f"HTTP返回码：{response.status_code}")
        print(f"错误码：{response.code}")
        print(f"错误信息：{response.message}")
        print("请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code")


    # generate text plan with qwen3-max model
    response_text = ""
    messages = [
        {"role": "system",
            "content": f"""请你扮演一个业规划师和心灵导师于一身的AI。你的任务是根据的梦想，完成以下两项任务：
    ## 梦想路径指南
    要求: 提供清晰的行动指南
    目标拆解: 将用户的宏大梦想拆解成3到5个可执行的关键步骤。
    路径规划: 每个步骤都应清晰、具体，具有可操作性。例如：
        * 第一步：知识储备与技能学习（建议学习哪些课程、阅读哪些书籍）。
        * 第二步：实践与经验积累（建议参加哪些项目、实习或活动）。
        * 第三步：建立人脉与寻求机遇（建议如何拓展社交圈、寻找导师）。
        * 第四步：持续进步与突破（面对瓶颈时如何调整）。

    ## 梦想寄语
    要求: 赋予精神力量，撰写一段激励人心的话语
    内容核心: 肯定用户梦想的价值，鼓励他们相信自己的潜力。
    情感基调: 真诚、温暖、有力量，能够激发用户的内在动力。
    结尾: 用一句强有力的口号或祝福来结束。

    总要求： 文字部分总字数不超过500字。
    """},
        {"role": "user",
            "content": f"""用户的梦想是：{dream}"""}
    ]

    response = Generation.call(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key = "sk-xxx",
        api_key=api_key,
        model="qwen3-max",
        messages=messages,
        result_format="message",
    )

    response_text = response.output.choices[0].message.content

    return response_text, response_image

def generate_dream_image_and_plan_doubao(dream: str = "成为一名畅销书作家", image_path: str = "/path/to/cat_image.png"):
    # Placeholder for future implementation with Doubao model
    # 通过 pip install 'volcengine-python-sdk[ark]' 安装方舟SDK 
    from volcenginesdkarkruntime import Ark 

    api_key = get_api_key("doubao")
    if not api_key:
        return "Doubao API key not found in config.ini", None

    # 初始化Ark客户端，从环境变量中读取您的API Key 
    client = Ark( 
        # 此为默认路径，您可根据业务所在地域进行配置 
        base_url="https://ark.cn-beijing.volces.com/api/v3", 
        # 从环境变量中获取您的 API Key。此为默认方式，您可根据需要进行修改 
        api_key=api_key, 
    ) 

    image_generation_prompt = f"""
    请你扮演一个集艺术家、职业规划师和心灵导师于一身的AI。你的任务是根据提供的头像照片和未来梦想，完成图像创作：
    
    总体目标：视觉化未来，生成梦想成真时的图像；
    核心元素: 融合用户头像的面部特征，确保能看出是同一个人。人物脸部要特别明显，符合用户对未来的展望。请仔细辨别用户的性别、年龄和种族特征。
    场景设定: 根据用户梦想，构建一个具体、生动的未来场景。例如，如果梦想是成为作家，场景可以是在一个阳光明媚的书房里，手捧着自己出版的畅销书；如果梦想是环游世界，场景可以是在异国他乡的标志性建筑前，面带笑容。
    风格要求: 画面风格需积极、明亮、充满成就感和幸福感。写实风格。
    人物状态: 未来的人物形象要显得更加自信、充满活力。可以根据推理生成梦想实现时的年龄的形象。

    用户的梦想是：{dream}
        """
    imagesResponse = client.images.generate(
        model="doubao-seedream-4-0-250828", 
        prompt=image_generation_prompt,
        image=encode_file(image_path),
        size="2K",
        response_format="url",
        watermark=False
    ) 
 
    image_url = imagesResponse.data[0].url

    response_image = download_file(image_url, save_directory="uploads")
    

    # generate text plan with doubao model
    response_text = ""
    messages = [
        {"role": "system",
            "content": f"""请你扮演一个业规划师和心灵导师于一身的AI。你的任务是根据的梦想，完成以下两项任务：
    ## 梦想路径指南
    要求: 提供清晰的行动指南
    目标拆解: 将用户的宏大梦想拆解成3到5个可执行的关键步骤。
    路径规划: 每个步骤都应清晰、具体，具有可操作性。例如：
        * 第一步：知识储备与技能学习（建议学习哪些课程、阅读哪些书籍）。
        * 第二步：实践与经验积累（建议参加哪些项目、实习或活动）。
        * 第三步：建立人脉与寻求机遇（建议如何拓展社交圈、寻找导师）。
        * 第四步：持续进步与突破（面对瓶颈时如何调整）。

    ## 梦想寄语
    要求: 赋予精神力量，撰写一段激励人心的话语
    内容核心: 肯定用户梦想的价值，鼓励他们相信自己的潜力。
    情感基调: 真诚、温暖、有力量，能够激发用户的内在动力。
    结尾: 用一句强有力的口号或祝福来结束。

    总要求： 文字部分总字数不超过500字。
    """},
        {"role": "user",
            "content": f"""用户的梦想是：{dream}"""}
    ]

    completion = client.chat.completions.create(
        model="doubao-seed-1-6-lite-251015",
        messages=messages,
    )
    
    response_text = completion.choices[0].message.content

    return response_text, response_image


if __name__ == "__main__":
    dream = "成为一名畅销书作家"
    image_path = "uploads/cai.png"  # 替换为你的图片路径
    
    # gemini api
    # response_text, response_image = generate_dream_image_and_plan(dream, image_path)
    # 
    #print the response text
    # print("Generated Text:\n", response_text)
    #save the response image with a unique filename
    # if response_image is not None:
        # response_image.save("generated_image_{}.png".format(uuid.uuid4()))

    # qwen api
    # response_text, response_image = generate_dream_image_and_plan_qwen(dream, image_path)
    # # print the response text
    # print("Generated Text:\n", response_text)

    # doubao api
    response_text, response_image = generate_dream_image_and_plan_doubao(dream, image_path)
    # print the response text
    print("Generated Text:\n", response_text)