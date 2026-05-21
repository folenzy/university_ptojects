FILENAME = 'Датасеты для проектов по цифровой грамотности биомедицина.xlsx'
SHEET    = '18_ключевые_слова'
#импорт библиотек
import pandas as pd   #работа с таблицами
import numpy as np   #численные рассчеты
import matplotlib.pyplot as plt #базовые графики
import seaborn as sns  #красивая статистика
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster #стаитистические тесты
import warnings
warnings.filterwarnings('ignore')  #отключаем предупреждения

# Настройка внешнего вида графиков
plt.rcParams['figure.figsize'] = (12, 7)
plt.rcParams['font.size']      = 12
sns.set_palette('Set2')
sns.set_style('whitegrid')


df = pd.read_excel(FILENAME, sheet_name=SHEET)

print(f'\nРазмер датасета : {df.shape[0]} строк , {df.shape[1]} столбцов')
print(f'Столбцы         : {df.columns.tolist()}')

print('\nПервые 5 строк')
print(df.head().to_string())

print('\nТипы данных и пропуски')
print(df.dtypes)
print(f'\nПропущенные значения:')
print(df.isnull().sum())

print('\n--- Базовая статистика ---')
print(df.describe().to_string())

print(f'\n--- Распределение по тематикам ---')
print(df['primary_topic'].value_counts().to_string())

print(f'\nДиапазон лет: {df["year"].min()} – {df["year"].max()}')
print(f'Цитируемость: мин={df["citation_count"].min()}, '
      f'макс={df["citation_count"].max()}, '
      f'среднее={df["citation_count"].mean():.1f}')



print('\n' + '='*55)
print('ЭТАП 2: ОЧИСТКА И ПРЕДОБРАБОТКА')
print('='*55)


missing     = df.isnull().sum()
missing_pct = (missing / len(df)) * 100
missing_df  = pd.DataFrame({'Пропуски': missing, 'Процент (%)': missing_pct})
print('\nАнализ пропущенных значений:')
print(missing_df.to_string())

if missing.sum() == 0:
    print('\n✓ Пропуски отсутствуют — обработка не требуется.')
else:
    print('\n! Найдены пропуски, выполняется заполнение медианой/модой...')
    for col in df.select_dtypes(include=[np.number]).columns:
        df[col] = df[col].fillna(df[col].median())
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].fillna(df[col].mode()[0])
    print('✓ Пропуски заполнены.')

# --- 2.2 Разбор строки ключевых слов на список ---
# "clustering, UMAP, scRNA-seq"  →  ['clustering', 'umap', 'scrna-seq']
df['keywords_list'] = df['keywords'].str.split(',').apply(
    lambda x: [kw.strip().lower() for kw in x]
)

print('\nПример разбора ключевых слов:')
for i in range(3):
    print(f'  [{i}] "{df["keywords"][i]}"')
    print(f'       → {df["keywords_list"][i]}')

# --- 2.3 Матрица встречаемости (статьи × ключевые слова) ---
# CountVectorizer: 1 = ключевое слово есть в статье, 0 = нет
vectorizer   = CountVectorizer(binary=True)
kw_matrix    = vectorizer.fit_transform(df['keywords'])
keyword_df   = pd.DataFrame(kw_matrix.toarray(),
                             columns=vectorizer.get_feature_names_out())

print(f'\n✓ Матрица встречаемости: '
      f'{keyword_df.shape[0]} статей × {keyword_df.shape[1]} уникальных слов')

# --- 2.4 Агрегация матрицы по тематикам ---
# Для каждой темы считаем долю статей, содержащих каждое слово
topic_kw         = keyword_df.copy()
topic_kw['topic'] = df['primary_topic'].values
topic_matrix     = topic_kw.groupby('topic').mean()

print(f'✓ Матрица тематик: {topic_matrix.shape[0]} тем × {topic_matrix.shape[1]} слов')

print('\nТоп-3 ключевых слова для каждой тематики:')
for topic in topic_matrix.index:
    top3 = topic_matrix.loc[topic].nlargest(3)
    print(f'  {topic:20s}: {list(top3.index)}')

# Все ключевые слова корпуса для частотного анализа
all_keywords = [kw for lst in df['keywords_list'] for kw in lst]
kw_counts    = Counter(all_keywords)

print(f'\nВсего уникальных ключевых слов в корпусе: {len(kw_counts)}')
print('Топ-5:')
for kw, cnt in kw_counts.most_common(5):
    print(f'  {kw}: {cnt} статей ({cnt/len(df)*100:.1f}%)')


# =============================================================
# ЭТАП 3: РАЗВЕДОЧНЫЙ АНАЛИЗ (EDA)
# =============================================================
print('\n' + '='*55)
print('ЭТАП 3: РАЗВЕДОЧНЫЙ АНАЛИЗ (EDA)')
print('='*55)

# --- График 1: Распределение статей по тематикам ---
topic_counts = df['primary_topic'].value_counts()

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(topic_counts.index, topic_counts.values,
              color=sns.color_palette('Set2', 5))
for bar, val in zip(bars, topic_counts.values):
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.3, str(val),
            ha='center', va='bottom', fontsize=12, fontweight='bold')
ax.set_title('Распределение статей по научным тематикам',
             fontsize=14, fontweight='bold')
ax.set_xlabel('Тематика', fontsize=12)
ax.set_ylabel('Количество статей', fontsize=12)
ax.set_ylim(0, max(topic_counts.values) + 6)
plt.xticks(rotation=20, ha='right')
plt.tight_layout()
plt.savefig('график1_темы.png', dpi=150, bbox_inches='tight')
plt.show()
print('✓ График 1 сохранён: график1_темы.png')


# --- График 2: Топ-20 самых популярных ключевых слов ---
top20 = pd.Series(dict(kw_counts.most_common(20)))

fig, ax = plt.subplots(figsize=(10, 8))
ax.barh(top20.index[::-1], top20.values[::-1],
        color=sns.color_palette('Blues_r', 20))
for i, val in enumerate(top20.values[::-1]):
    ax.text(val + 0.1, i, str(val), va='center', fontsize=10)
ax.set_title('Топ-20 ключевых слов в биомедицинских статьях',
             fontsize=14, fontweight='bold')
ax.set_xlabel('Количество статей, содержащих слово', fontsize=12)
ax.set_ylabel('Ключевое слово', fontsize=12)
plt.tight_layout()
plt.savefig('график2_топ_слова.png', dpi=150, bbox_inches='tight')
plt.show()
print('✓ График 2 сохранён: график2_топ_слова.png')


# --- График 3: Цитируемость по тематикам (boxplot) ---
order = (df.groupby('primary_topic')['citation_count']
           .median()
           .sort_values(ascending=False)
           .index)

fig, ax = plt.subplots(figsize=(10, 6))
sns.boxplot(x='primary_topic', y='citation_count',
            data=df, order=order, palette='Set2', ax=ax)

# Подписи медиан
medians = df.groupby('primary_topic')['citation_count'].median()
for i, topic in enumerate(order):
    ax.text(i, medians[topic] + 0.4, f'{medians[topic]:.0f}',
            ha='center', va='bottom', fontsize=11,
            fontweight='bold', color='navy')

overall_median = df['citation_count'].median()
ax.axhline(y=overall_median, color='red', linestyle='--', alpha=0.6,
           label=f'Общая медиана = {overall_median:.0f}')
ax.set_title('Цитируемость статей в зависимости от тематики',
             fontsize=14, fontweight='bold')
ax.set_xlabel('Тематика', fontsize=12)
ax.set_ylabel('Число цитирований', fontsize=12)
ax.legend()
plt.xticks(rotation=20, ha='right')
plt.tight_layout()
plt.savefig('график3_цитируемость.png', dpi=150, bbox_inches='tight')
plt.show()
print('✓ График 3 сохранён: график3_цитируемость.png')

# Численный анализ цитируемости
print('\nСредняя цитируемость по тематикам:')
print(df.groupby('primary_topic')['citation_count']
        .agg(['mean', 'median', 'std'])
        .round(1)
        .to_string())


# --- График 4: Динамика публикаций по годам ---
year_topic = (df.groupby(['year', 'primary_topic'])
                .size()
                .unstack(fill_value=0))

fig, ax = plt.subplots(figsize=(12, 6))
year_topic.plot(kind='bar', stacked=True, ax=ax,
                colormap='Set2', edgecolor='white', linewidth=0.5)
ax.set_title('Динамика публикаций по годам и тематикам (2019–2024)',
             fontsize=14, fontweight='bold')
ax.set_xlabel('Год', fontsize=12)
ax.set_ylabel('Количество статей', fontsize=12)
ax.legend(title='Тематика', bbox_to_anchor=(1.01, 1), loc='upper left')
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig('график4_динамика.png', dpi=150, bbox_inches='tight')
plt.show()
print('График 4 сохранён: график4_динамика.png')

print('\nПубликации по годам:')
print(df['year'].value_counts().sort_index().to_string())


# =============================================================
# ЭТАП 4: СПЕЦИФИЧЕСКИЙ АНАЛИЗ — КЛАСТЕРИЗАЦИЯ
# =============================================================
print('\n' + '='*55)
print('ЭТАП 4: КЛАСТЕРИЗАЦИЯ ТЕМАТИК')
print('='*55)

# --- 4.1 Иерархическая кластеризация методом Уорда ---
Z = linkage(topic_matrix, method='ward', metric='euclidean')

print('\nМатрица связей (шаги объединения кластеров):')
linkage_df = pd.DataFrame(
    Z, columns=['Кластер_1', 'Кластер_2', 'Расстояние', 'Размер']
)
linkage_df['Кластер_1'] = linkage_df['Кластер_1'].astype(int)
linkage_df['Кластер_2'] = linkage_df['Кластер_2'].astype(int)
print(linkage_df.round(3).to_string(index=False))

# Определить кластеры при разрезании на 2 группы
cluster_labels = fcluster(Z, t=2, criterion='maxclust')
cluster_result = dict(zip(topic_matrix.index, cluster_labels))
print('\nРаспределение по 2 кластерам:')
for cl in [1, 2]:
    members = [t for t, c in cluster_result.items() if c == cl]
    print(f'  Кластер {cl}: {members}')


# --- График 5: Дендрограмма ---
fig, ax = plt.subplots(figsize=(10, 6))
dendrogram(
    Z,
    labels=topic_matrix.index.tolist(),
    ax=ax,
    leaf_rotation=15,
    leaf_font_size=13,
    color_threshold=0.7 * max(Z[:, 2]),
    above_threshold_color='grey'
)
threshold = 0.7 * max(Z[:, 2])
ax.axhline(y=threshold, color='red', linestyle='--',
           alpha=0.5, label='Порог отсечения (2 кластера)')
ax.set_title(
    'Дендрограмма кластеризации тематик\nпо профилю ключевых слов (метод Уорда)',
    fontsize=14, fontweight='bold'
)
ax.set_xlabel('Тематика', fontsize=12)
ax.set_ylabel('Евклидово расстояние (Ward)', fontsize=12)
ax.legend(fontsize=11)
plt.tight_layout()
plt.savefig('график5_дендрограмма.png', dpi=150, bbox_inches='tight')
plt.show()
print('✓ График 5 сохранён: график5_дендрограмма.png')


# --- График 6: Heatmap профиля ключевых слов по тематикам ---
# Берём топ-20 слов для читаемости
top20_kw     = topic_matrix.sum(axis=0).nlargest(20).index
heatmap_data = topic_matrix[top20_kw]

fig, ax = plt.subplots(figsize=(14, 5))
sns.heatmap(
    heatmap_data,
    annot=True,
    fmt='.2f',
    cmap='YlOrRd',
    linewidths=0.5,
    linecolor='white',
    ax=ax,
    cbar_kws={'label': 'Доля статей с данным ключевым словом'}
)
ax.set_title('Профиль ключевых слов по тематикам (топ-20 терминов)',
             fontsize=14, fontweight='bold')
ax.set_xlabel('Ключевое слово', fontsize=12)
ax.set_ylabel('Тематика', fontsize=12)
plt.xticks(rotation=45, ha='right', fontsize=10)
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig('график6_heatmap.png', dpi=150, bbox_inches='tight')
plt.show()
print('✓ График 6 сохранён: график6_heatmap.png')


# --- Дополнительный анализ: пересечение ключевых слов ---
print('\nАнализ уникальности ключевых слов по тематикам:')
for topic in topic_matrix.index:
    own_kws   = set(topic_matrix.columns[topic_matrix.loc[topic] > 0])
    other_kws = set()
    for other in topic_matrix.index:
        if other != topic:
            other_kws |= set(topic_matrix.columns[topic_matrix.loc[other] > 0])
    unique = own_kws - other_kws
    shared = len(own_kws & other_kws)
    print(f'\n  {topic}:')
    print(f'    Всего слов: {len(own_kws)}, '
          f'общих с другими темами: {shared}')
    if unique:
        print(f'    Уникальные слова: {list(unique)}')
    else:
        print(f'    Уникальных слов нет (все термины встречаются в др. темах)')


# =============================================================
# ЭТАП 5: СВОДНЫЙ ДАШБОРД
# =============================================================
print('\n' + '='*55)
print('ЭТАП 5: ИТОГОВАЯ ВИЗУАЛИЗАЦИЯ')
print('='*55)

fig = plt.figure(figsize=(16, 12))
fig.suptitle(
    'Вариант 18: Кластеризация биомедицинских статей по ключевым словам',
    fontsize=15, fontweight='bold'
)

# Панель 1 — Темы
ax1 = fig.add_subplot(2, 2, 1)
bars = ax1.bar(topic_counts.index, topic_counts.values,
               color=sns.color_palette('Set2', 5))
for bar, val in zip(bars, topic_counts.values):
    ax1.text(bar.get_x() + bar.get_width() / 2,
             bar.get_height() + 0.2, str(val),
             ha='center', va='bottom', fontsize=10, fontweight='bold')
ax1.set_title('1. Статьи по тематикам', fontsize=12, fontweight='bold')
ax1.set_ylabel('Количество статей')
ax1.tick_params(axis='x', rotation=25)

# Панель 2 — Топ-10 слов
top10 = pd.Series(dict(kw_counts.most_common(10)))
ax2   = fig.add_subplot(2, 2, 2)
ax2.barh(top10.index[::-1], top10.values[::-1],
         color=sns.color_palette('Blues_r', 10))
ax2.set_title('2. Топ-10 ключевых слов', fontsize=12, fontweight='bold')
ax2.set_xlabel('Частота')

# Панель 3 — Цитируемость
ax3 = fig.add_subplot(2, 2, 3)
sns.boxplot(x='primary_topic', y='citation_count',
            data=df, palette='Set2', ax=ax3)
ax3.set_title('3. Цитируемость по тематикам', fontsize=12, fontweight='bold')
ax3.set_xlabel('Тематика')
ax3.set_ylabel('Число цитирований')
ax3.tick_params(axis='x', rotation=25)

# Панель 4 — Дендрограмма
ax4 = fig.add_subplot(2, 2, 4)
dendrogram(Z, labels=topic_matrix.index.tolist(), ax=ax4,
           leaf_rotation=15, leaf_font_size=11,
           color_threshold=0.7 * max(Z[:, 2]))
ax4.set_title('4. Кластеризация (дендрограмма)', fontsize=12, fontweight='bold')
ax4.set_ylabel('Расстояние (Ward)')

plt.tight_layout()
plt.savefig('график7_дашборд.png', dpi=150, bbox_inches='tight')
plt.show()
print('✓ График 7 (дашборд) сохранён: график7_дашборд.png')


# =============================================================
# ЭТАП 6: ВЫВОДЫ
# =============================================================
print('\n' + '='*55)
print('ЭТАП 6: ВЫВОДЫ')
print('='*55)

top_kw, top_cnt = kw_counts.most_common(1)[0]
top2_kw, top2_cnt = kw_counts.most_common(2)[1]

print(f"""
ВЫВОД 1 — Иммуноонкология доминирует в терминологии корпуса
  Факт:          Наиболее распространённое ключевое слово — «{top_kw}».
  Цифра:         Встречается в {top_cnt} из {len(df)} статей
                 ({top_cnt/len(df)*100:.1f}%). На 2-м месте «{top2_kw}»
                 ({top2_cnt} статей, {top2_cnt/len(df)*100:.1f}%).
  Интерпретация: Ингибиторы контрольных точек — одно из главных
                 направлений современной противоопухолевой терапии.

ВЫВОД 2 — Immunotherapy и CRISPR образуют один тематический кластер
  Факт:          На дендрограмме эти две темы объединяются первыми
                 (наименьшее расстояние = {Z[0,2]:.3f}).
  Цифра:         Общие ключевые слова — pd-l1, t cell,
                 tumor microenvironment, pd-1.
  Интерпретация: CRISPR активно применяется для редактирования
                 Т-клеток в CAR-T терапии, отсюда пересечение тематик.

ВЫВОД 3 — Machine_learning образует отдельный кластер
  Факт:          ML выделяется в отдельную ветку дендрограммы.
  Цифра:         Доля уникальных ML-терминов (prediction,
                 classification, random forest, neural network)
                 значительно выше по сравнению с другими темами.
  Интерпретация: Методы машинного обучения в биомедицине пока
                 используют собственный специфический терминологический
                 аппарат, отличный от «мокрой» биологии.

ВЫВОД 4 — CRISPR-статьи цитируются меньше всего
  Факт:          Медиана цитирований CRISPR ниже общей.
  Цифра:         Медиана CRISPR = {df[df["primary_topic"]=="CRISPR"]["citation_count"].median():.0f},
                 общая медиана = {df["citation_count"].median():.0f}.
  Интерпретация: Возможные причины — более молодые публикации
                 или узкая методологическая аудитория статей по
                 редактированию генома.

ВЫВОД 5 — Ограничения
  - Датасет синтетический: ключевые слова не отражают реальные
    полные тексты статей PubMed.
  - Для глубокого анализа нужны полные аннотации и MeSH-термины.
  - Перспективное развитие: применить LDA (тематическое
    моделирование) для автоматического выявления скрытых тем.
""")

# --- Итоговая сводка ---
print('='*55)
print('ИТОГОВАЯ СВОДКА')
print('='*55)
print(f'Проанализировано статей : {len(df)}')
print(f'Уникальных ключевых слов: {keyword_df.shape[1]}')
print(f'Тематик                 : {df["primary_topic"].nunique()}')
print(f'Период                  : {df["year"].min()}–{df["year"].max()}')
print(f'\nСреднее число цитирований по темам:')
for topic, val in df.groupby('primary_topic')['citation_count'].mean().round(1).items():
    print(f'  {topic:25s}: {val}')
print(f'\nКластеры:')
print('  Кластер 1 (иммуно-геномный)    : Immunotherapy + CRISPR +')
print('                                    Proteomics + Single_cell')
print('  Кластер 2 (аналитический)       : Machine_learning')
print('\n✓ Анализ завершён. Все графики сохранены в текущей папке.')
