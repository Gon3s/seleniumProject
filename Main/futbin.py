import json
import os.path
import time
from datetime import datetime
from functools import partial
from tkinter.ttk import Progressbar, Separator, Treeview

from selenium import webdriver
from bs4 import BeautifulSoup
import requests
from tkinter import *
from threading import Thread

# Drivers Chrome
options = webdriver.ChromeOptions()
options.add_argument("user-data-dir=C:\\Users\\gones\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 1")
options.add_argument('--headless')

url_price = "https://www.futbin.com/22/playerGraph?type={}&year=22&player={}&set_id="

columns = ("id", "note", "name", "position", "club", "country", "type", "price", "minPrice", "maxPrice", "avgPrice", "diffMin")
folder = "players/"


class GetPlayers(Thread):
    def __init__(self, url):
        super().__init__()

        self.data = None
        self.url = url

    def run(self):

        self.get_players(self.url)

    def get_info_players(self, url, id):

        file = folder + id + ".json"
        if os.path.isfile(file):
            self.data = json.load(open(file, 'r'))
        else:
            url = "https://www.futbin.com/" + url

            # page_source = driver.page_source
            r = requests.get(url)
            soup = BeautifulSoup(r.text, 'html.parser')

            self.data = {
                "id": soup.find(id="page-info")['data-player-resource'],
                "note": soup.select_one("#Player-card > div.pcdisplay-rat").text,
                "name": soup.select_one("#Player-card > div.pcdisplay-name").text,
                "position": soup.select_one("#Player-card > div.pcdisplay-pos").text,
                "club": soup.select_one("#info_content > table > tr:nth-child(3) > td > a").text,
                "country": soup.select_one("#info_content > table > tr:nth-child(4) > td > a").text,
                "type": soup.select_one("#info_content > table > tr:nth-child(12) > td").text
            }

            with open(file, "w") as file_object:
                json.dump(self.data, file_object)

        time.sleep(0.5)

        r = requests.get(url_price.format("today", self.data['id']))
        today = r.json()

        prices = {}
        if 'pc' in today:
            for todayPc in today['pc']:
                prices[todayPc[0]] = todayPc[1]

        time.sleep(0.5)

        r = requests.get(url_price.format("yesterday", self.data['id']))
        yesterday = r.json()

        if 'pc' in yesterday:
            for yesterdayPc in yesterday['pc']:
                prices[yesterdayPc[0]] = yesterdayPc[1]

        if len(prices) > 0:
            key_max = max(prices.keys(), key=(lambda k: prices[k]))
            key_min = min(prices.keys(), key=(lambda k: prices[k]))
            last_price_key = max(prices.keys())

            self.data['price'] = prices[last_price_key]

            self.data['minPrice'] = prices[key_min]
            self.data['maxPrice'] = prices[key_max]
            self.data['avgPrice'] = round(sum(prices.values()) / len(prices))
            self.data['diffMin'] = self.data['price'] - prices[key_min]

        app.update(self.data)

    def get_players(self, url):
        print(url)
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')

        trs = soup.select("#repTb > tbody > tr")
        if trs is None:
            return

        cpt = 0
        for tr in trs:
            cpt += 1
            a = tr.select_one('.player_name_players_table')['href']
            id = tr.select_one("td.table-row-text.row > div.d-inline.pt-2.pl-3 > div:nth-child(1) > a")['data-site-id']

            self.get_info_players(a, id)
            # if cpt > 0:
            #     break

        next_page = soup.select_one('.pagination li:last-child a[aria-label="Next"]')
        if next_page is not None:
            self.get_players("https://www.futbin.com" + next_page["href"])


class MyTreeview(Treeview):
    def heading(self, column, sort_by=None, **kwargs):
        if sort_by and not hasattr(kwargs, 'command'):
            func = getattr(self, f"_sort_by_{sort_by}", None)
            if func:
                kwargs['command'] = partial(func, column, False)
        return super().heading(column, **kwargs)

    def _sort(self, column, reverse, data_type, callback):
        l = [(self.set(k, column), k) for k in self.get_children('')]
        l.sort(key=lambda t: data_type(t[0]), reverse=reverse)
        for index, (_, k) in enumerate(l):
            self.move(k, '', index)
        self.heading(column, command=partial(callback, column, not reverse))

    def _sort_by_num(self, column, reverse):
        self._sort(column, reverse, int, self._sort_by_num)

    def _sort_by_name(self, column, reverse):
        self._sort(column, reverse, str, self._sort_by_name)

    def _sort_by_date(self, column, reverse):
        def _str_to_datetime(string):
            return datetime.strptime(string, "%Y-%m-%d %H:%M:%S")
        self._sort(column, reverse, _str_to_datetime, self._sort_by_date)


class App(Tk):

    def __init__(self):
        super().__init__()

        self.datas = []

        self.state('zoomed')

        self.menu = Menu(self)
        self.file_menu = Menu(self.menu, tearoff=False)

        self.frame_tree = Frame(self)
        self.tree = MyTreeview(self.frame_tree, show='headings', columns=columns)
        self.scrollbar_tree = Scrollbar(self.frame_tree, orient=HORIZONTAL, command=self.tree.xview)

        self.bar_progress = Progressbar(self, mode="indeterminate", length=2000)

        self.value_label = Label(self, text=self.update_progress_label())

        self.create_interface()

    def create_interface(self):
        self.title("FUTBin format")

        self.config(menu=self.menu)
        self.file_menu.add_command(
            label="Send",
            command=self.handle_download
        )
        self.file_menu.add_command(
            label="Load",
            command=self.load
        )
        self.file_menu.add_command(
            label="Save",
            command=self.save
        )
        self.file_menu.add_command(
            label='Exit',
            command=self.destroy,
        )
        self.menu.add_cascade(
            label="File",
            menu=self.file_menu
        )

        self.value_label.pack(padx=10, pady=10, fill="x")

        self.create_tree()

        # self.load()

    def create_tree(self):
        self.tree.heading('id', text='Identifiant')
        self.tree.heading('note', text='Note', sort_by='num')
        self.tree.heading('name', text='Nom', sort_by='name')
        self.tree.heading('position', text='Poste')
        self.tree.heading('country', text='Pays')
        self.tree.heading('club', text='Club')
        self.tree.heading('type', text='Type')
        self.tree.heading('price', text='Prix', sort_by='num')
        self.tree.heading('minPrice', text='Prix mini', sort_by='num')
        self.tree.heading('maxPrice', text='Prix maxi', sort_by='num')
        self.tree.heading('avgPrice', text='Prix moyen', sort_by='num')
        self.tree.heading('diffMin', text='Différence prix & mini', sort_by='num')

        for column in columns:
            self.tree.column(column, width=150, stretch=False)

        self.tree.pack(fill="both", expand=True)

        self.scrollbar_tree.pack(fill="x")

        self.tree['xscrollcommand'] = self.scrollbar_tree.set

        self.frame_tree.pack(fill="both", expand=True)

    def treeview_sort_column(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        print(l)
        l.sort(reverse=reverse)

        # rearrange items in sorted positions
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        # reverse sort next time
        self.tree.heading(col, command=lambda: self.treeview_sort_column(col, not reverse))

    def update(self, data):
        self.datas.append(data)
        self.tree.insert('', END, values=list(data.values()))

    def handle_download(self):
        self.bar_progress.pack(fill="x")
        self.bar_progress.start(20)

        self.datas = []
        self.tree.delete(*self.tree.get_children())

        url = 'https://www.futbin.com/22/players?page=1&eUnt=1&pc_price=10500-35000&version=all_specials&sort=likes&order=desc'

        download_thread = GetPlayers(url)
        download_thread.start()

        self.monitor(download_thread)

    def monitor(self, download_thread):
        """ Monitor the download thread """
        if download_thread.is_alive():
            self.after(1000, lambda: self.monitor(download_thread))
        else:
            self.bar_progress.stop()
            self.bar_progress.pack_forget()
            # self.save()
            pass

    def update_progress_label(self):
        return f"Current Progress: {self.bar_progress['value']}%"

    def save(self):
        if len(self.datas) == 0:
            return

        with open("data.json", "w") as file_object:
            json.dump(self.datas, file_object)

    def load(self):
        datas = open('data.json', 'r')
        self.datas = json.load(datas)

        for data in self.datas:
            self.tree.insert('', END, values=list(data.values()))


if __name__ == '__main__':
    app = App()
    app.mainloop()