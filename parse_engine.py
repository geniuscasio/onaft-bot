# -*- coding: utf-8 -*-
import config
import ast
import requests
from bs4 import BeautifulSoup
import json
from Postgres import Postgres

def parse_group(group_url, faculty_name):
    ONAFT_URL = 'https://www.rozklad.onaft.edu.ua'
    faculty = group_url
    response = requests.get(ONAFT_URL + '/' + faculty)

    if response.ok:
        html = response.text
    else:
        print("Boo! {}".format(response.status_code))
        html = response.text

    soup = BeautifulSoup(html, "lxml")

    tbody = soup.find("tbody")

    isTwoLetters = True

    if soup.find("thead").find("tr").find("th", attrs={"colspan": "2"}):
        isTwoLetters = True
        group_id = soup.find("thead").find("tr").find(
            "th", attrs={"colspan": "2"})
        if group_id:
            group_id = group_id.text
    else:
        isTwoLetters = False
        group_id = soup.find("thead").find("tr").find(
                "th", attrs={"colspan": "1"}
            )
        if group_id:
            group_id = group_id.text
    if not group_id:
        exit

    # группы А / Б
    a = []
    b = []

    i = 1
    for days in tbody.find_all("tr"):
        day = days.find_all("td")
        empty = {'lecture' :'', 'lecturer' :'', 'lecturer_full': '', 'room': ''}
        for item in day:
            if item.find("strong"):
                item_block = {}
                try:
                    predm = item.find("strong").find(
                        "span", attrs={"class": "predm"}).text.strip()
                except:
                    predm = ''

                try:
                    lector = item.find("strong").find(
                    "span", attrs={"class": "prp"}).text.strip()
                except:
                    lector = ''
                
                try:
                    lector_full = item.find("strong").find(
                        "span", attrs={"class": "prp"})['title'].strip()
                except:
                    lector_full = ''

                try:
                    room = item.find(
                        "a", attrs={"class": "text-info"}).find("strong").text.strip()
                except:
                    room = ''

                item_block['lecture'] = predm
                item_block['lecturer'] = lector
                item_block['lecturer_full'] = lector_full
                item_block['room'] = room
                
                print(item_block)
                i = i * (-1)
                if predm:
                    if not isTwoLetters:
                        a.append(item_block)
                        continue
                    if i > 0:
                        b.append(item_block)
                        continue
                    else:
                        a.append(item_block)
                        continue
                else:
                    if not isTwoLetters:
                        a.append(empty)
                        continue
                    if i > 0:
                        b.append(empty)
                    else:
                        a.append(empty)
                    continue
                continue


    lectures = ast.literal_eval(str(a))
    for l in lectures:
        print(l['lecture'])
    db = Postgres()
    print(faculty_name)
    if isTwoLetters:
        db.set_schedule(group_id+config.LATTER_A, a, faculty_name)
        db.set_schedule(group_id+config.LATTER_B, b, faculty_name)
    else:
        db.set_schedule(group_id, a, faculty_name)

