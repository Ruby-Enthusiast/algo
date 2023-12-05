### 전체적으로 Python 3.11.5, MacBook Pro 환경에서 빌드.

from django.shortcuts import render
from django.http import HttpResponse
from django.core.files.base import ContentFile
from bs4 import BeautifulSoup
import requests
import re
from tqdm import tqdm
from wordcloud import WordCloud ## 확인해보니 Python 3.12.0 이상에서는 작동 불능.
import matplotlib.pyplot as plt
import base64
from mecab import MeCab ## python-mecab-ko 라이브러리 설치 필요!! => 워드 클라우드를 위한 형태소 분석기.
from io import BytesIO ## 이미지를 바이너리 단위로 변환용, db 설정 안하고도 이미지 표시할 수 있게 하는 용도.
from .models import SearchHistory

# Create your views here.

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/98.0.4758.102"}

# font_path = "~/Library/Fonts/NanumGothic.ttf"  # Mac 환경용

    # Linux 환경이라면, 일단 나눔고딕 폰트를 설치하고,  
    # font_path = "(폰트 경로)/NanumGothic.ttf" 로 변경
    # 보통은 폰트 경로가 /usr/share/fonts/

    # Windows 환경이라면,
fontpath = "./font/NanumGothic.ttf"

def makePgNum(num):
    if num == 1:
        return num
    elif num == 0:
        return num + 1
    else:
        return num + 9 * (num - 1)

def makeUrl(search, press_code):
    url = f"https://search.naver.com/search.naver?where=news&query={search}&sm=tab_opt&sort=0&photo=0&field=0&pd=0&ds=&de=&docid=&related=0&mynews=1&office_type=2&office_section_code=1&news_office_checked={press_code}&nso=&is_sug_officeid=0&office_category=0&service_area=0"
    return [url]  

def news_attrs_crawler(articles, attrs):
    attrs_content = []
    for i in articles:
        attrs_content.append(i.attrs[attrs])
    return attrs_content

def articles_crawler(url):
    original_html = requests.get(url, headers=headers)
    html = BeautifulSoup(original_html.text, "html.parser")

    url_naver = html.select("div.group_news > ul.list_news > li div.news_area > div.news_info > div.info_group > a.info")
    url = news_attrs_crawler(url_naver, 'href')
    return url

def news_scraper(search, press_codes):
    news_titles = []
    news_url = []
    news_contents = []  
    news_dates = [] 

    for press_code in press_codes:
        url = makeUrl(search, press_code)
        for i in url:
            url_list = articles_crawler(i)
            news_url.extend(url_list)

    final_urls = []
    for i in tqdm(range(len(news_url))):
        if "news.naver.com" in news_url[i]:
            final_urls.append(news_url[i])

    for article_url in tqdm(final_urls):
    
        news_response = requests.get(article_url, headers=headers)
        news_html = BeautifulSoup(news_response.text, "html.parser")

        article_title = news_html.select_one("#articleTitle")
        if article_title is None:
            article_title = news_html.select_one("#content > div.end_ct > div > h2")
            if article_title is None:
                article_title = news_html.select_one("title")

        article_title = article_title.text.strip() if article_title else ""

        
        article_content = news_html.select("div#articleBodyContents")
        if not article_content:
            article_content = news_html.select("#articeBody")

        
        article_content = ''.join(str(article_content))

        
        pattern1 = '<[^>]*>'
        article_content = re.sub(pattern=pattern1, repl='', string=article_content)
        pattern2 = """[\n\n\n\n\n// flash 오류를 우회하기 위한 함수 추가\nfunction _flash_removeCallback() {}"""
        article_content = article_content.replace(pattern2, '')

        
        try:
            html_date = news_html.select_one(
                "div#ct> div.media_end_head.go_trans > div.media_end_head_info.nv_notrans > div.media_end_head_info_datestamp > div > span")
            news_date = html_date.attrs['data-date-time']
        except AttributeError:
            news_date = news_html.select_one("#content > div.end_ct > div > div.article_info > span > em")
            news_date = re.sub(pattern=pattern1, repl='', string=str(news_date))

        
        news_titles.append(article_title)
        news_contents.append(article_content)
        news_dates.append(news_date)

    new_data = list(zip(news_dates, news_titles, final_urls, news_contents))

    return {
        "titles": news_titles,
        "urls": final_urls,
        "dates": news_dates,
        "new_data": new_data,
    }

def remove_particles(text):
    mecab = MeCab()
    words = mecab.nouns(text)
    return ' '.join(words)

def generate_wordcloud(search, data):
    
    def remove_search_query(text):
        words = text.split()
        return ' '.join([word.replace(search, '') if word == search else word for word in words])

    # Remove the search query from titles and contents
    all_titles = [remove_search_query(remove_particles(row[1])) for row in data]
    all_contents = [remove_search_query(remove_particles(row[3])) for row in data]
    all_combined_text = ' '.join(all_titles + all_contents)

    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='white',
        font_path=fontpath,
    ).generate(all_combined_text)

    # Save the wordcloud to image stream
    image_stream = BytesIO()
    wordcloud.to_image().save(image_stream, format='PNG')
    
    return image_stream.getvalue()

def grab(request):
    queries = {}
    i = 1
    while f'query{i}' in request.GET:
        queries[f'query{i}'] = request.GET.get(f'query{i}', '')
        i += 1

    search = queries.get('query1', '')
    press_codes = [queries.get(f'query{i}', '') for i in range(2, i)]

    if not search or not any(press_codes):
        return HttpResponse("Invalid input. Please provide a search query and at least one press code.")
    
    news_data = news_scraper(search, press_codes)

    # news_data 기반으로 삽입 정렬 알고리즘 추가
    sorted_data = list(zip(news_data["dates"], news_data["titles"], news_data["urls"], news_data["new_data"]))
    for i in range(1, len(sorted_data)):
        key_data, key_title, key_url, key_content = sorted_data[i]

        j = i - 1
        while j >= 0 and key_data > sorted_data[j][0]:
            sorted_data[j + 1] = sorted_data[j]
            j -= 1

        sorted_data[j + 1] = (key_data, key_title, key_url, key_content)

    # 정렬된 데이터를 따로 저장
    sorted_dates, sorted_titles, sorted_urls, sorted_new_data = zip(*sorted_data)

    wordcloud_image = generate_wordcloud(search, news_data["new_data"])

    if not SearchHistory.objects.filter(search_query=search).exists():
        # If it doesn't exist, create a new entry in the database
        search_history = SearchHistory(search_query=search)

        # Save the wordcloud in the database
        search_history.wordcloud_image.save(f'{search}_wordcloud.png', ContentFile(wordcloud_image))

        search_history.save()

    # Convert the image to base64 for rendering in HTML
    encoded_image = base64.b64encode(wordcloud_image).decode('utf-8')

    context = {
        "search": search,
        "selected_newspapers": press_codes,
        "zipped_news": zip(sorted_titles, sorted_urls, sorted_dates),
        "wordcloud_image": f"data:image/png;base64,{encoded_image}",
    }

    return render(request, 'news/index.html', context)