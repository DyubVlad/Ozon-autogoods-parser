import logging
import collections
import csv
from selenium import webdriver
from selenium.webdriver import ActionChains
import bs4

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Ozon')
ParseResult = collections.namedtuple(
    'ParseResult',
    (
        'main_category',
        'category_name',
        'url',
    ),
)

class categoryParser:

    def loadPage(self, driver):
        driver.implicitly_wait(5)
        driver.get('http://www.ozon.ru')

        buttCatalog = driver.find_element_by_class_name("ui-a9")
        if not buttCatalog:
            logger.error('not find class of button catalog')
        buttCatalog.click()

        autoCat = driver.find_element_by_xpath("//a[span='Автотовары']")
        if not autoCat:
            logger.error('not find category autotovary')
        ActionChains(driver).move_to_element(autoCat).perform()

        autoCat1 = driver.find_element_by_xpath("//a[span='Масла и автохимия']")
        if not autoCat1:
            logger.error('not find sub_category in main cat')

        ActionChains(driver).move_to_element(autoCat1).perform()

        aTag = autoCat1.get_attribute('class')
        parentDiv = driver.find_element_by_xpath("//div/a[@class='%s']/parent::div" % aTag)
        classCatBlok = parentDiv.get_attribute('class')
        return driver.page_source, classCatBlok

    def parsePage(self, text: str, classCat):
        soup = bs4.BeautifulSoup(text, 'lxml')
        container = soup.select('div[class="%s"]' % classCat)
        if not container:
            logger.error('no find class of bloks with category')

        for blok in container:
            mainCategory = blok.select_one('a').text
            subContainer = blok.select_one('div')
            for catBlok in subContainer:
                catUrl = catBlok.get('href')
                catName = catBlok.text

                self.result.append(ParseResult(
                    main_category=mainCategory,
                    category_name=catName,
                    url=catUrl,
                ))

    def saveResult(self):
        path = 'test.txt'
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f, dialect='excel-tab')
            for item in self.result:
                line = [item.main_category,item.category_name,item.url]
                writer.writerow(line)

    def run(self):
        self.result = []
        driver = webdriver.Firefox()
        text,classCat = self.loadPage(driver)
        self.parsePage(text=text, classCat=classCat)
        logger.info(f'Получили {len(self.result)} элементов')
        driver.close()
        self.saveResult()


if __name__ == '__main__':
    parser = categoryParser()
    parser.run()
