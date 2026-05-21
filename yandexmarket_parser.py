from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from datetime import datetime

# Инициализация драйвера
driver = webdriver.Chrome()
driver.maximize_window()
# Список
products_data = []

try:
    # Открытие главной страницы Яндекс Маркета
    driver.get('https://market.yandex.ru/')
    time.sleep(3)

    # выполнение поискового запроса
    search = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "header-search"))
    )
    search.send_keys('гантели')  # Ввод поискового запроса
    search.send_keys(Keys.RETURN)
    time.sleep(3)

    # Поиск всех карточек товаров на странице
    product_cards = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-auto-themler='card']"))
    )

    # Обработка первых 10 карточек товаров
    for i, card in enumerate(product_cards[:10]):
        driver.execute_script("arguments[0].scrollIntoView(true);", card)
        time.sleep(1)  # Небольшая пауза для загрузки

        product = {}
        # названия товара
        try:
            product['название'] = card.find_element(By.CSS_SELECTOR, "[data-auto='snippet-link-title']").text
        except:
            product['название'] = "Нету"

        # описания товара
        try:
            specs = card.find_elements(By.CSS_SELECTOR, "[data-auto='snippet-specs'] span")
            # Объединение первых трех характеристик через запятую
            product['описание'] = ', '.join([spec.text for spec in specs[:3]]) if specs else "Нету"
        except:
            product['описание'] = "Нету"

        # цена товара
        try:
            product['цена'] = card.find_element(By.CSS_SELECTOR, "[data-auto='price-value']").text
        except:
            product['цена'] = "Цена не указана"

        # рейтинг товара
        try:
            product['рейтинг'] = card.find_element(By.CSS_SELECTOR, "[data-auto='snippet-rating']").text
        except:
            product['рейтинг'] = "Нет оценок"

        # ссылка на изображение товара
        try:
            img = card.find_element(By.CSS_SELECTOR, "img")
            # Получение атрибута src
            product['картинка'] = img.get_attribute('src') or img.get_attribute('data-src') or "Картини нету"
        except:
            product['картинка'] = "Картинка не найдена"

        products_data.append(product)

    # Создание DataFrame из собранных данных
    df = pd.DataFrame(products_data)
    # Выбор и упорядочивание нужных колонок
    df = df[['название', 'описание', 'картинка', 'цена', 'рейтинг']]

    filename = f"tovary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    # Сохранение данных в Excel файл
    df.to_excel(filename, index=False, engine='openpyxl')
    print(f"Сохранено {len(products_data)} товаров в файл {filename}")

except Exception as e:
    print(f"Ошибка: {e}")

finally:
    # Завершение
    time.sleep(2)
    driver.quit()
