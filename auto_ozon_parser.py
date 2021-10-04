import logging
import csv
import time

from selenium.common import exceptions as selenExep
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from xml.dom import minidom
from xml.dom.minidom import parse
import fileinput
import bs4


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Ozon')

class pageParser:

    def __init__(self):
        self.listUrl = []
        self.domain = 'https://www.ozon.ru'
        #self.xmlPath = '/Users/Vlad/PycharmProjects/Oz_pars/xml/'
        #self.pathCategory = '/Users/Vlad/PycharmProjects/Oz_pars/test.txt'
        #self.pathListGoods = '/Users/Vlad/PycharmProjects/Oz_pars/goods_link.txt'
        self.xmlPath = 'xml/'
        self.pathCategory = 'test.txt'
        self.pathListGoods = 'goods_link.txt'


    def tenPageLoad(self, url,):
        pageIter = 1
        driver = self.startDriver()
        url = self.domain + url
        catUrl = url
        with open(self.pathListGoods, 'w+') as f:
            f.seek(0)

        while True:
            driver.get(catUrl)
            xpathCod = '//div[@data-widget="searchResultsV2"]/div/div[30]/div/a/div/div[1]/img'
            try:
                WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, xpathCod)))
                searchContainer = driver.find_elements_by_class_name('widget-search-result-container')
            except selenExep.TimeoutException:
                driver.quit()
                return
            goodsBlocksCount = len(searchContainer)
            while True:
                xpathCod = '//div[@data-widget="searchResultsV2"]' + '[' + str(goodsBlocksCount) + ']' + '/div/div[last()]'
                locationLastBlock = driver.find_element_by_xpath(xpathCod).location_once_scrolled_into_view
                driver.execute_script("scrollBy(0,250);")

                xpathCod = '//div[@data-widget="searchResultsV2"]' + '[' + str(goodsBlocksCount + 1) + ']' \
                           + '/div/div[30]/div/a/div/div[1]/img'
                try:
                    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, xpathCod)))
                except selenExep.TimeoutException:
                    break

                searchContainer = driver.find_elements_by_class_name('widget-search-result-container')
                goodsBlocksCount1 = len(searchContainer)

                if goodsBlocksCount1 > goodsBlocksCount:
                    goodsBlocksCount = goodsBlocksCount1
                    continue
                else:
                    break
            goodsContainers = driver.find_elements_by_class_name('widget-search-result-container')
            for container in goodsContainers:
                self.parseCategory(container.get_attribute('outerHTML'))
            pageIter += 10
            catUrl = url + '/?page='+str(pageIter)


    def loadCategory(self, url):
        switch = False
        pageInt = 1
        driver = self.startDriver()
        refreshIter = 0
        while True:
            urlCategory = self.domain + url + "?page=" + str(pageInt)
            refreshIter += 1
            try:
                if (refreshIter/50).is_integer():
                    driver.quit()
                    driver = self.startDriver()
                driver.get(urlCategory)
            except selenExep.WebDriverException:
                driver.quit()
                driver = self.startDriver()
                logger.error(Exception)
                continue

            try:
                xpathCod = '//div[@data-widget="searchResultsV2"]/div/div[30]/div/a/div/div[1]/img'
                target = WebDriverWait(driver,3).until(EC.presence_of_element_located((By.XPATH, xpathCod)))
            except selenExep.TimeoutException:
                pass
            except selenExep.NoSuchWindowException:
                pass

            try:
                #searchContainer = driver.find_elements_by_class_name('widget-search-result-container')
                searchContainer = driver.find_elements_by_xpath('//div[@data-widget="searchResultsV2"]')
                if searchContainer.__len__() == 1:
                    goodsContainer = searchContainer[0]
                elif searchContainer.__len__() == 0:
                    goodsContainer = False
                elif searchContainer.__len__() > 1:
                    driver.quit()
                    self.tenPageLoad(url)
                    return
            except selenExep.NoSuchElementException:
                goodsContainer = False

            if goodsContainer:
                    pageInt += 1
                    self.parseCategory(goodsContainer.get_attribute('outerHTML'))
                    ActionChains(driver).key_down(Keys.ARROW_DOWN).perform()
            else:
                break
        driver.quit()
        return


    def parseCategory(self, text: str):
        soup = bs4.BeautifulSoup(text, 'lxml')

        findClass = soup.select_one('a').get_attribute_list('class')[0]
        urlContainer = soup.select('a.%s' %findClass)
        if not urlContainer:
            logger.error('no find urls blocks')

        urlGoodsFile = open(self.pathListGoods, 'a')
        for block in urlContainer:
            url = block.get('href')
            urlGoodsFile.write(url + '\n')
        urlGoodsFile.close()
        return

    def loadGoods(self):
        refreshIter = 0
        driver = self.startDriver()

        listUrlFile = open(self.pathListGoods)
        for url in listUrlFile:
            pageUrl = self.domain + url
            refreshIter += 1

            try:
                if (refreshIter/50).is_integer():
                    driver.quit()
                    driver = self.startDriver()
                driver.get(pageUrl.strip())
                WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.ID, 'section-description')))
                descriptionLink = driver.find_element_by_xpath("//a[text()='Перейти к описанию']")
                ActionChains(driver).move_to_element(descriptionLink).click().perform()
            except selenExep.TimeoutException:
                pass
            except selenExep.NoSuchElementException:
                logger.error(selenExep.NoSuchElementException)
                driver.refresh()
                pass
            except selenExep.WebDriverException:
                driver.quit()
                driver = self.startDriver()
                logger.error(str(Exception))

            try:
                fullDescription = driver.find_element_by_xpath("//button/div/div[text()='Показать полное описание']")
                ActionChains(driver).move_to_element(fullDescription).click().perform()
            except selenExep.MoveTargetOutOfBoundsException:
                driver.refresh()
            except selenExep.NoSuchElementException:
                # logger.info(selenExep.NoSuchElementException)
                pass
            except selenExep.NoSuchWindowException:
                pass

            self.parseGoods(driver.page_source, pageUrl)

        listUrlFile.close()

        with open(self.pathListGoods, 'w+') as f:
            f.seek(0)

        driver.quit()
        return

    def parseGoods(self, source, pageUrl):
        soup = bs4.BeautifulSoup(source, 'lxml')
        name = soup.find('h1')
        if name != None:
            name = soup.find('h1').text
        else:
            return

        if soup.find('ol'):
            category = soup.select_one('ol').select_one('a')
            catUrl = category.get('href')
            catName = category.text
        else:
            catUrl = 'None'
            catName = 'None'

        getPrice = soup.find('div', {'data-widget': 'webSale'})
        if getPrice != None:
            if getPrice.text.strip().split()[0].isdigit():
                price = soup.select_one('div[data-widget = "webSale"]').select_one('span').text
            elif getPrice.text.strip().split()[0] == 'Товар':
                price = 'Товар закончился'
        else:
            price = 'None'

        if soup.find('h2', text='Описание') != None:
            description = soup.select_one("div[data-widget = 'webDescription']").select_one('div').text
        else:
            description = 'None'

        self.xmlSave(pageUrl, name, catName, catUrl, price, description)
        return


    def xmlSave(self, pageUrl, name, catName, catUrl, price, description):
        doc = minidom.Document()
        root = doc.createElement('doc')
        root.setAttribute('href', pageUrl.strip())
        #itemNode = doc.createElement('item')

        nameNode = doc.createElement('title')
        nameNodeText = doc.createTextNode(name)
        nameNode.appendChild(nameNodeText)
        root.appendChild(nameNode)

        categoryNode = doc.createElement('category')
        categoryNode.setAttribute('href', catUrl)
        categoryNodeText = doc.createTextNode(catName)
        categoryNode.appendChild(categoryNodeText)
        root.appendChild(categoryNode)

        priceNode = doc.createElement('price')
        priceNodeText = doc.createTextNode(price.strip())
        priceNode.appendChild(priceNodeText)
        root.appendChild(priceNode)

        descriptionNode = doc.createElement('text')
        descriptionNodeCdata = doc.createCDATASection(description.strip())
        descriptionNode.appendChild(descriptionNodeCdata)
        root.appendChild(descriptionNode)

        #root.appendChild(itemNode)
        doc.appendChild(root)

        xml_str = doc.toprettyxml(indent='  ')
        fileName = pageUrl.strip().split(sep='/')
        if len(fileName[len(fileName)-2]) > 9:
            fileName = fileName[len(fileName)-2]
            fileName = fileName.split(sep='-')
            fileName = fileName[len(fileName)-1]
        else: fileName = fileName[len(fileName)-2]

        path = self.xmlPath + catName + ' ' + fileName + '.xml'
        with open(path, 'w+', encoding='utf-8') as f:
            f.write(xml_str)
        return

    def startDriver(self):
        firefox_profile = webdriver.FirefoxProfile()
        firefox_profile.set_preference('permissions.default.image', 2)
        driver = webdriver.Firefox(firefox_profile)
        #driver.implicitly_wait(5)
        return driver

    def run(self):
        with open(self.pathCategory, 'r', newline='') as f:
            listCategory = csv.reader(f)
            for row in listCategory:
                url = row[row.__len__()-1].split('\t')[row[row.__len__()-1].split('\t').__len__()-1]
                self.loadCategory(url)
                self.loadGoods()
                #self.parse_category(text=text)


if __name__ == '__main__':
    parser = pageParser()
    parser.run()
