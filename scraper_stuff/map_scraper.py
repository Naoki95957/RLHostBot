import os
import re
from pathlib import Path
import selenium
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import json

# A quick little scraper I threw togther to get map info from steam workshop
# it also does some basic analysis from leth's maps

# if a map is removed/timedout from steam, it'll mark the map as a txt file 
# preventing other processes from using it

# !!!!IMPORTANT!!!!
# It assumes it will find a combo of leth maps in their folders as if you downloaded and extracted them
# and steam workshop maps in their folders as if you downloaded and extracted them
# IE:
# Steam maps have this format -> in the folder '1246337892':
#   greenscreen_p.udk
#   prev2.jpg
#   preview.jpg
#   WorkshopItemInfo.JSON
# 
# and for leth -> in the folder 'Beach Brawl':
#   BeachBrawl.jpg
#   info.json
#   LethBeachBrawl.udk

WORKSHOP_URL = "https://steamcommunity.com/sharedfiles/filedetails/?id="
CHROME_DRIVER = './win_chromedriver89.exe'

class WebThingy:
    my_url = ''
    driver = None

    def __init__(self, url):
        self.my_url = url
        options = Options()
        options.add_argument('--log-level=3')
        options.headless = True
        full_path = str(Path(str(__file__)).parents[0])
        self.driver = selenium.webdriver.Chrome(
            options=options,
            executable_path=(full_path + CHROME_DRIVER))
        self.driver.get(self.my_url)

    def __del__(self):
        self.driver.quit()

    def set_url(self, url):
        self.my_url = url
        self.driver.get(self.my_url)
    
    def clean_url(self, url: str) -> str:
        '''
        This just removes the link filter if any
        '''
        return url.replace("https://steamcommunity.com/linkfilter/?url=", "")

    def start(self):
        clean_str = lambda string : str(re.sub(r"^\s+", '', string))
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((
                By.ID, 'rightContents')))
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        author_element = soup.find('div', {'class':'friendBlockContent'})
        title_element = soup.find('div', {'class':'workshopItemTitle'})
        description_element = soup.find('div', {'class':'workshopItemDescription', 'id':'highlightContent'})
        # get rid of these for loops if you don't want the discord markup
        for a in description_element.findAll('a'):
            # if the hyperlink is literally like this:
            # <a href='something.com'>something.com</a>
            if a.get_text() == a['href']:
                a.replace_with("<" + self.clean_url(a.get_text()) + ">")
            # otherwise get the hyperink
            else:
                a.replace_with(a.get_text() + ": <" + self.clean_url(a['href']) + ">")
        for b in description_element.findAll('b'):
            if b.get_text():
                b.replace_with("**" + b.get_text() + "**")
            else:
                b = None
        for u in description_element.findAll('u'):
            if u.get_text():
                u.replace_with("__" + u.get_text() + "__")
            else: 
                u = None
        for i in description_element.findAll('i'):
            if i.get_text():
                i.replace_with("*" + i.get_text() + "*")
            else:
                i = None
        author = clean_str(author_element.contents[0])
        title = clean_str(title_element.contents[0])
        desc = description_element.get_text('\n')
        return (title, author, desc)

def main():
    load_dotenv('./config.env')
    rl_dir = os.getenv("CUSTOM_PATH")
    map_index = {}
    counter = 0
    scraper = None
    for root, dirs, files in os.walk(rl_dir):
        for file in files:
            if file.endswith('.udk'):
                if file not in map_index:
                    map_index[file] = {}
                    # steam maps
                    if os.path.basename(root).isnumeric():
                        try:
                            if scraper:
                                scraper.set_url(WORKSHOP_URL + os.path.basename(root))
                            else:
                                scraper = WebThingy(WORKSHOP_URL + os.path.basename(root))
                            results = scraper.start()
                        except Exception as e:
                            # be aware that you'll have to deal with these scenarios
                            # (you can choose to find the info urself, delete the map, etc)
                            # before you can run this again
                            print("DROPPED STEAM MAP -> " + os.path.basename(root))
                            os.rename(os.path.join(root, file), os.path.join(root, file + "(ERROR).txt"))
                            counter += 1
                            continue
                        map_index[file]['title'] = results[0]
                        map_index[file]['author'] = results[1]
                        map_index[file]['description'] = results[2]
                        map_index[file]['source'] = (WORKSHOP_URL + os.path.basename(root))
                        counter += 1
                        print(counter, "maps compete")
                    else: 
                        # it's one of leth's maps
                        title = os.path.basename(root)
                        info = json.load(open(os.path.join(root, "info.json")))
                        author = info["author"]
                        description = info["desc"]
                        map_index[file]['title'] = title
                        map_index[file]['author'] = author
                        map_index[file]['description'] = description
                        counter += 1
                        print(counter, "maps compete")
    json_str = json.dumps(map_index)
    file = open("./map_info.json", 'w')
    file.write(json_str)
    file.close()
    
if __name__ == "__main__":
    main()