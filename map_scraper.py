import os
import re
from pathlib import Path
import selenium
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import json

# A quick little scraper I threw togther to get map info from steam workshop
# it also does analysis from leth's maps


URL = "https://steamcommunity.com/sharedfiles/filedetails/?id=" 
DIR = "Z:\\rocketLeagueMaps"
CHROME_DRIVER = '/drivers/win_chromedriver89.exe'

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

    def clear_actions(self, action_chain):
        action_chain.w3c_actions.devices[0].clear_actions()
        action_chain.w3c_actions.devices[1].clear_actions()

    def set_url(self, url):
        self.my_url = url
        self.driver.get(self.my_url)

    def start(self):
        clean_str = lambda string : str(re.sub(r"^\s+", '', string))
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((
                By.ID, 'rightContents')))
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        author_element = soup.find('div', {'class':'friendBlockContent'})
        title_element = soup.find('div', {'class':'workshopItemTitle'})
        description_element = soup.find('div', {'class':'workshopItemDescription', 'id':'highlightContent'})
        author = clean_str(author_element.contents[0])
        title = clean_str(title_element.contents[0])
        desc = description_element.get_text('\n')
        return (title, author, desc)

def main():
    map_index = {}
    counter = 0
    scraper = None
    for root, dirs, files in os.walk(DIR):
        for file in files:
            if file.endswith('.udk'):
                map_index[file] = {}
                if os.path.basename(root).isnumeric():
                    if scraper:
                        scraper.set_url(URL + os.path.basename(root))
                    else:
                        scraper = WebThingy(URL + os.path.basename(root))
                    results = scraper.start()
                    map_index[file]['title'] = results[0]
                    map_index[file]['author'] = results[1]
                    map_index[file]['description'] = results[2]
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
    file = open("map_info.json", 'w')
    file.write(json_str)
    file.close()
    
if __name__ == "__main__":
    main()