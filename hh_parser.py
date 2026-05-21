# Импорт необходимых библиотек
import requests  # Для отправки HTTP-запросов
from bs4 import BeautifulSoup  # Для парсинга HTML
import pandas as pd  # Для работы с данными и сохранения в CSV

# Создаем пустой список
work = []

# URL страницы с вакансиями на HeadHunter
url = "https://hh.ru/search/vacancy?text=Водитель+офисный&from=suggest_post&salary=1000&ored_clusters=true&excluded_text=&area=1&suggestId=8dde36a7-c67f-4b75-8084-2425dec7d366&hhtmFrom=vacancy_search_list&hhtmFromLabel=vacancy_search_line"

# Заголовки для HTTP-запроса, имитирующие реальный браузер
# Это необходимо, чтобы сайт не заблокировал наш парсер
headers = {'User-Agent':
               'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
           }

# Отправляем GET-запрос
response = requests.get(url, headers=headers)

# Получаем HTML-содержимое страницы
html_content = response.text

# Создаем объект BeautifulSoup для парсинга HTML
soup = BeautifulSoup(html_content, "html.parser")

# Находим все div-элементы
# В этих элементах содержится информация о каждой вакансии
data = soup.find_all("div", class_="magritte-redesign")

# Проходим по каждой найденной вакансии
for i in data:
    name = i.find("h2", class_="bloko-header-section-2").text
    price = i.find("span",class_="magritte-text___pbpft_4-5-0 magritte-text_style-primary___AQ7MW_4-5-0 magritte-text_typography-label-1-regular___pi3R-_4-5-0").text
    experience = i.find("div", class_="magritte-tag__label___YHV-o_5-1-1").text
    worker = i.find("a",class_="magritte-link___b4rEM_7-1-3 magritte-link_mode_primary___l6una_7-1-3 magritte-link_style_neutral___iqoW0_7-1-3").text

    # Добавляем словарь с данными о вакансии в список
    work.append({"должность": name, "зарплата": price, "опыт": experience, "работодатель": worker})

    # Создаем DataFrame из списка вакансий
    df = pd.DataFrame(work)

    # Сохраняем DataFrame в CSV-файл
    df.to_csv("work2.csv", index=False)
df = pd.read_csv('file.csv', encoding='utf-8')  # или encoding='cp1251' для Windows

# Сохраняем в Excel
df.to_excel('file.xlsx', index=False, engine='openpyxl')

    print("success")
