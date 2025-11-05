# To run this code you need to install the following dependencies:
# pip install google-genai

from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import os
import uuid
import dotenv

dotenv.load_dotenv()

def generate_dream_image_and_plan(dream: str = "成为一名畅销书作家", image_path: str = "/path/to/cat_image.png"):
    client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))

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
        else:
            continue

    return response_text, response_image

if __name__ == "__main__":
    dream = "成为一名畅销书作家"
    image_path = "uploads/cai.jpg"  # 替换为你的图片路径
    response_text, response_image = generate_dream_image_and_plan(dream, image_path)
    
    # print the response text
    print("Generated Text:\n", response_text)

    # save the response image with a unique filename
    if response_image is not None:
        response_image.save("generated_image_{}.png".format(uuid.uuid4()))