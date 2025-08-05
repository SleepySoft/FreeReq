# pip install mecab-python3 jaconv beautifulsoup4
# sudo apt-get install mecab libmecab-dev mecab-ipadic-utf8  # Ubuntu
# https://github.com/ikegami-yukino/mecab/releases


import MeCab
import jaconv
from bs4 import BeautifulSoup, NavigableString, CData


def add_furigana_to_html(html_content):
    # 初始化MeCab（注意：词典路径需根据实际安装位置调整）
    tagger = MeCab.Tagger(r'-d "C:\Program Files\MeCab\dic\ipadic"')

    soup = BeautifulSoup(html_content, 'html.parser')

    for text_node in soup.find_all(string=True):

        if text_node.parent.name in ['script', 'style']:
            continue

        text = str(text_node).strip()
        if not text or text.isascii():
            continue  # 跳过空文本或纯英文

        # 分词并生成注音标签
        container = soup.new_tag('span')  # 创建容器包裹<ruby>
        node = tagger.parseToNode(text)

        while node:
            if node.surface.strip():
                features = node.feature.split(",")
                if len(features) < 8:  # 确保特征字段完整
                    node = node.next
                    continue

                # 提取关键特征[8](@ref)
                surface = node.surface
                pos = features[0]
                origin = features[-3]  # 词汇来源
                kata_reading = features[-2]  # 片假名读音

                # 智能选择注音形式[1,5](@ref)
                if "外来" in origin or pos in ["名詞-固有名詞-人名", "名詞-固有名詞-地名"]:
                    reading = kata_reading  # 专有名词保留片假名
                else:
                    reading = jaconv.kata2hira(kata_reading)  # 普通词汇转平假名

                # 生成<ruby>标签结构[1](@ref)
                ruby_tag = soup.new_tag("ruby")
                ruby_tag.string = surface
                rt_tag = soup.new_tag("rt")
                rt_tag.string = reading
                ruby_tag.append(rt_tag)
                container.append(ruby_tag)

            node = node.next

        # 用容器替换原始文本
        if container.contents:
            text_node.replace_with(container)

    return str(soup)


# CSS样式增强（建议添加到HTML头部）[1](@ref)
css_enhancement = """
<style>
  ruby {
    display: inline-flex;
    flex-direction: column-reverse;
    text-indent: 0;
    line-height: 1.5;
    margin: 0 1px;
  }
  rt {
    font-size: 0.6em;
    color: #e74c3c;
    text-align: center;
    font-family: "Hiragino Sans", sans-serif;
  }
</style>
"""

html_input = """
<p>東京の銀行で新しいプロジェクトを発表しました</p>
<script>const ignore = "この部分は処理されない";</script>
"""

result = add_furigana_to_html(html_input)
print(css_enhancement + result)


# import MeCab
# import jaconv
# from bs4 import BeautifulSoup, NavigableString, CData
#
#
# def get_annotated_text(text):
#     tagger = MeCab.Tagger(r'-d "C:\\Program Files\\MeCab\\dic\\ipadic"')  # 指定词典路径
#     node = tagger.parseToNode(text)
#     result = []
#     while node:
#         if node.surface.strip():
#             surface = node.surface  # 词汇原形
#             features = node.feature.split(",")  # 词性特征数组
#             pos = features[0]  # 词性（如名詞、動詞）
#             origin = features[-3]  # 词汇来源（如"外来"）
#             reading_katakana = features[-2]  # 片假名读音
#
#             # 判断是否外来语或特殊词汇
#             if "外来" in origin or pos in ["名詞-固有名詞-人名", "名詞-固有名詞-地名"]:
#                 kana = reading_katakana  # 保留片假名
#             else:
#                 kana = jaconv.kata2hira(reading_katakana)  # 转平假名
#
#             result.append((surface, kana))
#         node = node.next
#     return result
#
#
# def add_furigana_to_html(html_content):
#     tagger = MeCab.Tagger(r'-d "C:\\Program Files\\MeCab\\dic\\ipadic"')  # 替换为您的词典路径
#
#     soup = BeautifulSoup(html_content, 'html.parser')
#
#     all_text_nodes = soup.find_all(string=True)
#     for text_node in all_text_nodes:
#         if isinstance(text_node, (CData, NavigableString)) and text_node.parent.name in ['script', 'style']:
#             continue
#
#         text = str(text_node).strip()
#         if not text or text.isascii():
#             continue
#
#         # 分词并生成注音
#         node = tagger.parseToNode(text)
#         annotated_text = []
#         while node:
#             if node.surface.strip():
#                 surface = node.surface
#                 reading = node.feature.split(",")[-2]
#                 fullwidth_reading = jaconv.h2z(reading)
#
#                 ruby_tag = soup.new_tag("ruby")
#                 ruby_tag.append(surface)
#                 rt_tag = soup.new_tag("rt")
#                 rt_tag.string = fullwidth_reading
#                 ruby_tag.append(rt_tag)
#                 annotated_text.append(ruby_tag)
#             node = node.next
#
#         # === 修复部分：用容器包裹多个标签 ===
#         if annotated_text:
#             # 创建容器包裹所有<ruby>标签
#             container = soup.new_tag('span')
#             for ruby in annotated_text:
#                 container.append(ruby)
#
#             # 用容器替换原始文本节点
#             text_node.replace_with(container)
#
#     return str(soup)


# # 测试用例
# html_input = """
# <html>
# <body>
#   <p>日本語の漢字（かんじ）は難しいが、学生は頑張って勉強する。</p>
#   <script>const example = "この部分は処理しない";</script>
# </body>
# </html>
# """
#
# result = add_furigana_to_html(html_input)
# print(result)
