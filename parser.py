# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import parse_engine

# class Parser:
#     class _parser:
#         def __init__(self):
#             self.parse = parse
#     instance = None
#     isFree = True

#     def __init__(self):
#         if (not Parser.instance):
#             Parser.instance = Parser._parser()
#     def doParse(self):
#         if Parser.isFree:
#             Parser.isFree = False
#             try:
#                 parse()
#             except:
#                 print('Something goes wrong!')
#             finally:
#                 Parser.isFree = True
        

BASE_URL = 'https://www.rozklad.onaft.edu.ua'

resp = requests.get(BASE_URL + '/guest_n.php')

if resp.ok:
    html = resp.text
else:
    print ("Boo! {}".format(resp.status_code))
    html = resp.text
soup = BeautifulSoup(html, "lxml")
facks = soup.find_all(
    "a",
    attrs={"class": "tile double double-vertical bg-darkBlue"}
)
i = 0
for faculty in facks:
    #if i > 1:
    #    break
    if faculty.get("href"):
        resp = requests.get(BASE_URL + '/' + faculty.get("href"))
        if resp.ok:
            print('Факультет: ' + faculty.get_text().strip())
            html = resp.text
            soup = BeautifulSoup(html, "lxml")
            groups = soup.find_all(
                "a",
                attrs={"class": "tile ribbed-darkCyan double double-vertical"}
            )

            for row in groups:
                print('  Группа: ' + row.find("span", attrs={"class": "name"}).text)
                parse_engine.parse_group(row.get("href"), faculty.get_text().strip())
        else:
            print("Boo! {}".format(resp.status_code))
    i += 1

    # faculty = '?view=f&id=20'
    # parse_engine.parse_group('guest_n.php?view=g&id=773')
