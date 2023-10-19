from bs4 import BeautifulSoup
import requests
import psycopg2
from bs4 import BeautifulSoup

url = 'https://bestsellingalbums.org/charts/vk-albums/'
chart_data = ''

response = requests.get(url)
sup = BeautifulSoup(response.text, 'html.parser')
teg = sup.find_all('div', class_='data_col')

for teg in teg[:13]:
    text = teg.text.replace('Прослушивания',' - Прослушивания').replace(')', ') ')
    chart_data += text + '.\n'


