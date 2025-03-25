import json

import requests
from bs4 import BeautifulSoup
from openai import OpenAI

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

proxies = {
    "http": "http://web-proxy.houston.softwaregrp.net:8080",
    "https": "http://web-proxy.houston.softwaregrp.net:8080"
}

link_system_prompt = """
你获得了一个网页上找到的链接列表。
你可以决定哪些链接与制作学校宣传册最为相关，
例如关于页面的链接、公司页面（的链接，或者职业/工作页面的链接。
你应该按照以下示例的JSON格式进行回复：
{
    "links": [
        {"type": "关于页面", "url": "https://full.url/goes/here/about"},
        {"type": "职业页面": "url": "https://another.full.url/careers"}
    ]
}
"""

system_prompt = """
你是一个智能助手，负责分析学校网站中多个相关页面的内容，
并制作一份简短的宣传册，面向潜在的需要报考该学校的学生家长。请使用Markdown格式回复。

若获取到相关信息，需包含以下内容：
- 校长介绍
- 学校领导
- 学校文化
- 教学理念
- 办学特点
- 获奖情况
- 校园环境
- 招生情况
- 优秀校友
- 优秀学生
- 党团活动
- 社会责任
- 联系方式
- 学校地址
- 学校新闻
"""


class Website:
    def __init__(self, url):
        self.url = url
        try:
            response = requests.get(url, headers=headers, proxies=None)
            self.body = response.content
            soup = BeautifulSoup(self.body, 'html.parser')
            self.title = soup.title.string if soup.title else "No title found"
            if soup.body:
                for irrelevant in soup.body(["script", "style", "img", "input"]):
                    irrelevant.decompose()
                self.text = soup.body.get_text(separator="\n", strip=True)
            else:
                self.text = ""

            links = [link.get("href") for link in soup.find_all('a')]
            self.links = [link for link in links if link]
        except Exception as e:
            self.title = None
            self.text = None
            self.links = None

    def get_contents(self):
        return f"网站标题:\n{self.title}\n网站内容:\n{self.text}\n\n" if self.title else ''


def get_links_user_prompt(website):
    link_str = "\n".join(website.links)
    user_prompt = f"""
    以下是{website.url}网站上的链接列表 -
    请判断以下哪些链接适合放入学校宣传册中，
    并以JSON格式返回完整的https链接。
    
    链接列表（部分可能为相对路径）：
    {link_str}
    """
    return user_prompt


def get_links(url):
    website = Website(url)
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(website)}
        ],
        response_format={"type": "json_object"}
    )
    result = response.choices[0].message.content
    return json.loads(result)


def get_all_details(url):
    result = "主页:\n"
    result += Website(url).get_contents()
    links = get_links(url)
    print("Found links:", links)
    if not links or "links" not in links:
        return ''
    for link in links["links"]:
        if "type" not in link or "url" not in link:
            continue
        link_type = link['type']
        link_url = link["url"]
        url_contents = Website(link_url).get_contents()
        result += f"""
        
        
        {link_type}
        {url_contents}
        """
    return result


def get_brochure_user_prompt(company_name, url):
    page_details = get_all_details(url)
    user_prompt = f"""
    您正在查看的学校名为： {company_name}
    以下是该学校官网首页及其他相关页面的内容，请根据这些信息，使用 Markdown 格式编写一份详实的学校宣传册。
    {page_details}
    """
    return user_prompt


def create_brochure(company_name, url):
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": get_brochure_user_prompt(company_name, url)}
        ],
    )
    result = response.choices[0].message.content
    file_name = f"{company_name}_profile.md"
    with open(file_name, "x", encoding="utf-8") as f:
        f.write(result)


def stream_brochure(company_name, url):
    stream = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": get_brochure_user_prompt(company_name, url)}
        ],
        stream=True
    )

    file_name = f"{company_name}_profile.md"
    with open(file_name, "w", encoding="utf-8") as f:
        for chunk in stream:
            delta= chunk.choices[0].delta.content or ''
            print(chunk.choices[0].delta)
            f.write(delta)


model = "deepseek-r1:1.5b"
openai = OpenAI(base_url="http://localhost:11434/v1", api_key='ollama')
stream_brochure("上海师范大学附属中学", "https://www.ssdfz.pudong-edu.sh.cn/")
