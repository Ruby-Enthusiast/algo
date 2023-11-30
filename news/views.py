from django.shortcuts import render
from django.http import HttpResponse
from bs4 import BeautifulSoup
import requests
import re
from tqdm import tqdm

# Create your views here.
# 삽입 정렬 + 뉴스 왼쪽에 언론사 출력 + 워드클라우드는 아직 미구현. 진행중.

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/98.0.4758.102"}

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


    return {
        "titles": news_titles,
        "urls": final_urls,
        "dates": news_dates,
    }

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

    zipped_news = zip(news_data["titles"], news_data["urls"], news_data["dates"])

    context = {
        "search": search,
        "selected_newspapers": press_codes,
        "zipped_news": zipped_news,
    }

    print(context)

    return render(request, 'news/index.html', context)