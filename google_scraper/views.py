from django.shortcuts import render
from django.http import HttpResponse
from .set import WAIT_DAYS
from .forms import ScraperForm
import urllib.request
import json
from .models import Query, Link
import operator
# important to selenium
from selenium import webdriver
import os
import datetime



class Record:
    def __init__(self, link, title, description, num):
        self.link = link
        self.title = title
        self.description = description
        self.num = num


def get_ip(request):
    ip = request.META["REMOTE_ADDR"]
    if ip != '127.0.0.1':
        return ip
    url = 'https://api.myip.com'
    response = urllib.request.urlopen(url)
    data = response.read()
    data = json.loads(data)
    ip = data['ip']
    return ip


def get_data_from_selenium(phraze, query):
    records = []
    if query:
        links = query.links.all()
        for link in links:
            records.append(Record(link.link, link.title, link.description, link.position))
            num_results = query.num_results
        return records, num_results
    else:
        phraze_list = phraze.strip().split()
        phraze = ""
        for ph in phraze_list:
            phraze += ph+"+"
        phraze = phraze[:-1]
        path = os.path.abspath('/home/angel/Downloads/geckodriver')
        driver = webdriver.Firefox(executable_path=path)
        driver.get("https://www.google.com/search?q={}".format(phraze))
        pre_num_results = driver.find_element_by_id("resultStats").text
        #links = driver.find_elements_by_class_name("r")
        links = driver.find_elements_by_xpath("//div[@class='r']")
        titles = driver.find_elements_by_class_name("LC20lb")
        descriptions = driver.find_elements_by_class_name("st")

        links = links[(len(links)-len(titles)):]
        for i in range(len(links)):
            records.append(Record(links[i].get_attribute('innerHTML').split('"')[1],
                                 titles[i].text, descriptions[i].text, i+1))
        driver.close()
        num_results = ""
        pre_num_results = pre_num_results.strip().split()[1:-3]
        for num in pre_num_results:
            num_results += num
        num_results = int(num_results)
        return records, num_results


def is_right_word(word):
    forbidden_char = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '+', '=',
                      '-', '_', '[', ']', '{', '}', '"', "'", '|', '\\',
                      '/', '?', '.', '>', '<', '–', '(', ')', ':', ';', ',']
    for char in forbidden_char:
        if char in word:
            return False
    return True


def replace_unwanted_char(word):
    forbidden_char = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '+', '=',
                      '-', '_', '[', ']', '{', '}', '"', "'", '|', '\\',
                      '/', '?', '.', '>', '<', '–', '(', ')', ':', ';', ',']
    for char in forbidden_char:
        word = word.replace(char, ' ')
    return word


def get_popular_word(query):
    links = query.links.all()
    words = set()
    for link in links:
        title_words = link.title.lower()
        title_words = replace_unwanted_char(title_words).split()
        desc_words = link.description.lower()
        desc_words = replace_unwanted_char(desc_words).split()
        words = words | set(title_words)
        words = words | set(desc_words)
    word_dict = {}
    for word in words:
        word_dict[word] = 0
    for link in links:
        title_words = link.title.lower()
        desc_words = link.description.lower()
        for word in words:
            word_dict[word] += title_words.lower().count(word)
            word_dict[word] += desc_words.lower().count(word)
        sorted_d = sorted(word_dict.items(), key=operator.itemgetter(1), reverse=True)
        wordss = []
        for w in sorted_d:
            if is_right_word(w[0]):
                wordss.append(w[0])
            if len(wordss) == 10:
                break

    return wordss


def main(request):
    num_days = WAIT_DAYS
    if request.method == 'POST':
        query = ""
        form = ScraperForm(request.POST)
        quest = form["quest"].value()
        ip = get_ip(request)
        qu = Query.objects.filter(ip=ip, phrase=quest)
        date_now = datetime.datetime.now()
        date_now = int(date_now.strftime("%Y%m%d"))
        for q in qu:
            date_untill = q.created.replace(day=num_days+q.created.day)
            date_untill = int(date_untill.strftime("%Y%m%d"))
            if date_untill >= date_now:
                query = q
                break
        data, num_results = get_data_from_selenium(quest, query)
        if not query:
            # zapis do bazy danych moze byc przez celery
            #query
            query = Query.objects.create(
                ip=ip,
                phrase=quest,
                num_results=num_results,
            )
            #links
            for rec in data:
                Link.objects.create(
                    link=rec.link,
                    description=rec.description,
                    position=rec.num,
                    title=rec.title,
                    query=query,
                )
        # popular word
        words = get_popular_word(query)
        return render(request,
                  'google_scraper/summarize.html',
                  {'data': data,
                   'num_results': num_results,
                   'words': words,
                   'query': query,
                   })
    else:
        form = ScraperForm()
        return render(request,
                      'google_scraper/main.html',
                      {'form': form})
