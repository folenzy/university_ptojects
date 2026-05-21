import asyncio
import aiohttp
import json
import os
import random
import re
from datetime import datetime
from collections import Counter
from bs4 import BeautifulSoup

CONCURRENT = 40
DELAY = (0.1, 0.3)
OUTPUT_DIR = "patents_json"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


async def get_patent(session, patent_id):
    url = f"https://freepatent.ru/patents/{patent_id}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        async with session.get(url, headers=headers, timeout=30) as resp:
            html = await resp.text()
            if resp.status != 200 or "отсутствует в нашей базе" in html:
                return {"id": patent_id, "exists": False}

            soup = BeautifulSoup(html, 'html.parser')

            title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Без названия"

            # описание
            referat = soup.find('div', class_='referat')
            referat = referat.get_text(separator=" ", strip=True) if referat else "Реферат не найден"

            # МПК
            ipc = "не указана"
            for row in soup.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 2 and 'Классы МПК' in cells[0].get_text():
                    match = re.search(r'([A-Z]\d{2}[A-Z]\s*\d+/\d+)', cells[1].get_text())
                    if match:
                        ipc = match.group(1).strip()
                    break

            # Авторы
            authors = []
            for row in soup.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 2 and 'Автор(ы):' in cells[0].get_text():
                    spans = cells[1].find_all('span', itemprop='author')
                    authors = [s.get_text(strip=True) for s in spans] if spans else ["не указаны"]
                    break

            # Патентообладатель
            assignee = "не указан"
            for row in soup.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 2 and 'Патентообладатель(и):' in cells[0].get_text():
                    assignee = cells[1].get_text(strip=True)
                    break

            # Дата публикации
            pub_date = "не указана"
            date_span = soup.find('span', itemprop='datePublished')
            if date_span:
                pub_date = date_span.get_text(strip=True)

            print(f" {patent_id}: {title[:40]}... | Дата: {pub_date}")

            return {
                "id": patent_id,
                "exists": True,
                "title": title,
                "referat": referat[:5000],
                "ipc_class": ipc,
                "authors": authors,
                "assignee": assignee,
                "publication_date": pub_date,
                "word_count": len(referat.split())
            }

    except Exception as e:
        print(f"✗ {patent_id}: {e}")
        return {"id": patent_id, "exists": False, "error": str(e)}


def get_stats(patents):  # Статистика
    existing = [p for p in patents if p.get("exists")]

    if not existing:
        return None

    # Количество записей
    total = len(existing)

    # Количество уникальных слов
    all_text = " ".join([p.get("referat", "") for p in existing])
    words = re.findall(r'[А-Яа-яA-Za-z]{3,}', all_text.lower())
    unique_words = len(set(words))

    # Статистика по длине описания
    lengths = [p.get("word_count", 0) for p in existing]

    # Даты
    dates = [p.get("publication_date") for p in existing if p.get("publication_date") != "не указана"]

    # Пропуски
    missing_date = sum(1 for p in existing if p.get("publication_date") == "не указана")
    missing_ipc = sum(1 for p in existing if p.get("ipc_class") == "не указана")
    missing_authors = sum(1 for p in existing if p.get("authors") == ["не указаны"])

    return {
        "total_records": total,
        "unique_words": unique_words,
        "word_count": {
            "min": min(lengths),
            "max": max(lengths),
            "avg": round(sum(lengths) / len(lengths), 1),
            "median": sorted(lengths)[len(lengths) // 2]
        },
        "date_range": {
            "min": min(dates) if dates else "нет",
            "max": max(dates) if dates else "нет"
        },
        "missing_percentage": {
            "date": round(missing_date / total * 100, 1),
            "ipc": round(missing_ipc / total * 100, 1),
            "authors": round(missing_authors / total * 100, 1)
        }
    }


async def main():
    print("\n1 - ТЕСТ")
    print("2 - ПОЛНЫЙ(5500 патентов)")
    mode = input("Выберите (1/2): ")

    if mode == "1":
        ids = ["2036095", "2049619", "2050029", "2064471", "2079702", "2086345", "2098123", "2100456"]
    else:
        ids = [str(i) for i in range(2036095, 2041596)]

    print(f"\n Патентов: {len(ids)}")
    input("Нажмите Enter...")

    semaphore = asyncio.Semaphore(CONCURRENT)

    async def fetch(pid, session):
        async with semaphore:
            res = await get_patent(session, pid)
            await asyncio.sleep(random.uniform(*DELAY))
            return res

    start = datetime.now()

    async with aiohttp.ClientSession() as session:
        tasks = [fetch(pid, session) for pid in ids]
        results = await asyncio.gather(*tasks)

    elapsed = (datetime.now() - start).total_seconds()
    found = [r for r in results if r.get("exists")]

    # Статистика
    stats = get_stats(results)

    # Сохранение
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"patents_{timestamp}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "total": len(ids),
                "found": len(found),
                "duration_sec": round(elapsed, 1)
            },
            "statistics": stats,
            "patents": results
        }, f, ensure_ascii=False, indent=2)

    # ВЫВОД СТАТИСТИКИ
    print("\n" + "=" * 50)
    print(" ХАРАКТЕРИСТИКИ ДАТАСЕТА")
    print("=" * 50)

    if stats:
        print(f"\n Количество записей: {stats['total_records']}")
        print(f" Количество уникальных слов: {stats['unique_words']}")

        print(f"\n Количество слов в реферате:")
        print(f"    -Минимум: {stats['word_count']['min']}")
        print(f"    -Максимум: {stats['word_count']['max']}")
        print(f"    -Среднее: {stats['word_count']['avg']}")
        print(f"    -Медиана: {stats['word_count']['median']}")

        print(f"\n Диапазон дат публикации:")
        print(f"    -С: {stats['date_range']['min']}")
        print(f"    -По: {stats['date_range']['max']}")

        print(f"\n Доля пропусков:")
        print(f"    -Дата публикации: {stats['missing_percentage']['date']}%")
        print(f"    -Класс МПК: {stats['missing_percentage']['ipc']}%")
        print(f"    -Авторы: {stats['missing_percentage']['authors']}%")

    print(f"\n Сбор завершен")
    print(f" Файл: {output_file}")
    print(f" Время: {round(elapsed, 1)} сек.")


if __name__ == "__main__":
    asyncio.run(main())
