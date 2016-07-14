import urllib2, sys, re
import xlwt
import requests, json
import operator
from operator import attrgetter
from bs4 import BeautifulSoup
import urllib
import time

TOTAL_NO_OF_PRODUCT_PER_CATEGORY = 2000
ALCHEMY_API_KEY = "" #Alchemy api key
DATA = []	# Main array in which product will be populated
hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.17 (KHTML, like Gecko)  Chrome/24.0.1312.57 Safari/537.17'}

# Function takes categegoy url and populate product into DATA array in required format
def populateTopProductsByCategory(categoryUrl, categoryName):
	print("Getting items for " + categoryName + " form url:" + categoryUrl)
	req = urllib2.Request(categoryUrl,headers=hdr)
	text = urllib2.urlopen(req).read()
	soup = BeautifulSoup(text, "html.parser")
	data = soup.findAll('h2', attrs={'class':'bc-big-row-title'})
	if not data:
		data = soup.findAll('div', attrs= {'class' : 'bc-navy-cate-inner'})
	noOfItemForEachCategory = TOTAL_NO_OF_PRODUCT_PER_CATEGORY/len(data)
	for li in data:
		link = li.find('a', href=True)
		if(link['href']):
			populateProductsFromURL(link['href'], noOfItemForEachCategory, categoryName)

# Function takes sub-categegoy url, limit(upto how many products should br included) and populate product into DATA array in required format
def populateProductsFromURL(url, limit, categoryName):
	print(url + "\n")
	page = 1
	req = urllib2.Request(getValidUrl(url), headers=hdr)
	text = urllib2.urlopen(req).read()
	soup = BeautifulSoup(text, "html.parser")
	div = soup.find('div', attrs = {'class' : 'ui-pagination-navi'})
	nextPageUrl = div.findAll('a', href=True)
	while (limit > 0):
		if(page!=1):
			req = urllib2.Request(getValidUrl(url), headers=hdr)
			text = urllib2.urlopen(req).read()
			soup = BeautifulSoup(text, "html.parser")
		productLinks = soup.findAll('a',attrs={'class':'product'}, href=True)
		for productLink in productLinks:
			if(limit == 0):
				break;
			populateItemDetail(productLink['href'], categoryName)
			limit -= 1
		page += 1
		url = nextPageUrl[page - 1]['href']

# create object for one product
def populateItemDetail(url, categoryName):
	print(url)
	if(url):
		try :
			req = urllib2.Request(getValidUrl(url), headers=hdr)
			text = urllib2.urlopen(req).read()
			soup = BeautifulSoup(text, "html.parser")
			name = str(soup.find('h1', attrs = {'class' : 'product-name'}).text.encode('utf8').strip())
			price = float(getOnePrice(soup.find('span', attrs = {'id' : 'j-sku-price'}).text.encode('utf8').strip()).encode('utf8').strip())
			pictures = getImageUrlArray(soup.find('ul', attrs = {'id' : 'j-image-thumb-list'}))
			description = getDescription(soup.find('ul', attrs = {'class' : 'product-property-list'}))
			feedback = getFeedback(soup.find('iframe')['thesrc'])
			DATA.append({"name" : name, "price" : price, "pictures" : pictures, "description" : description, "category" : categoryName, "rating" : feedback['rating'], "reviewAnalysis" : feedback["reviewAnalysis"]})
			print(str(len(DATA)) + " Items Done")
		except :
			print("Unable to get data retry in 1 second")
			time.sleep(1)
			req = urllib2.Request("http://www.aliexpress.com/category/44/consumer-electronics.html?spm=2114.01010108.2.3.Bn0rkU",headers=hdr)
			text = urllib2.urlopen(req).read()
			soup = BeautifulSoup(text, "html.parser")
			populateItemDetail(url, categoryName)

# Return object containing rating, reviews, and response from alchemy api after sentimentents analysis
def getFeedback(url):
	# reviews = []
	reqData = {}
	if(url):
		req = urllib2.Request(getValidUrl(url), headers=hdr)
		text = urllib2.urlopen(req).read()
		soup = BeautifulSoup(text, "html.parser")
		rating = getRating(soup.findAll('span', attrs = {'class' : 'star-view'}))
		# feedbackItem = soup.findAll('dt', attrs = { 'class' : 'buyer-feedback'})
		# for feedback in feedbackItem:
		# 	message1 = feedback.find('span')
		# 	message2 = ""
		# 	if(message1):
		# 		message2 = message1.get_text()
		# 	reviews.append(message2.encode("utf-8"))
		if(ALCHEMY_API_KEY != ""):
			r = requests.post("https://gateway-a.watsonplatform.net/calls/html/HTMLGetTextSentiment",data= { "apikey" : ALCHEMY_API_KEY, "html" : soup.text, "outputMode" : "json" }).text
			response = json.loads(r)
			reqData = response['docSentiment']
	return {"rating": rating, "reviewAnalysis" : reqData}

# Create array for product description
def getDescription(descriptionUl):
	des = []
	if(descriptionUl):
		for li in descriptionUl.findAll('li'):
			des.append({'title' : str(li.find('span', attrs = {'class' : 'propery-title'}).text.encode('utf8').strip()), 'value' : str(li.find('span', attrs = {'class' : 'propery-des'}).text.encode('utf8').strip()) })
	return des

# Calculate average rating from first page of review(contains 10 reviews in each page)
def getRating(ratingViews):
	if(ratingViews):
		totalRating = 0
		for rate in ratingViews:
			totalRating += getRatingByImageWidth(rate.find('span')['style'])
		return totalRating/len(ratingViews)
	else:
		return 0

# Get rating based on width of start images
def getRatingByImageWidth(x):
    return {
        'width:100%': 5,
        'width:80%': 4,
        'width:60%': 3,
        'width:40%': 2,
        'width:20%': 1,
    }[x]

# Append http in url
def getValidUrl(url):
	return "http:" + url

# get price from string of different format like "2,334 - 1,555"
def getOnePrice(price):
	price = price.replace(",", "")
	if "-" in price:
		index = price.index('-')
		return price[:index]
	else :
		return price

# get images of product inside array
def getImageUrlArray(imageUl):
	images = []
	if(imageUl):
		for li in imageUl.findAll('li'):
			images.append(str(li.find('img', {"src":True})['src']))
	return images

def startScrapping():
	populateTopProductsByCategory("http://www.aliexpress.com/category/44/consumer-electronics.html?spm=2114.01010108.2.3.Bn0rkU", "Consumer Electronics")
	populateTopProductsByCategory("http://www.aliexpress.com/category/1509/jewelry-accessories.html?spm=2114.20020108.1.70.OEnrwm", "Jewelry & Accessories")
	populateTopProductsByCategory("http://www.aliexpress.com/category/66/health-beauty.html?spm=2114.20020108.1.152.0LclhE", "Health and Beauty")
	print("Done scrapping sorting now\n")
	DATA.sort(key = lambda x: x['price'],reverse=True)
	print("Writing data in json format\n")
	with open('aliexpress.txt', 'w') as outfile:
		json.dump(DATA, outfile)
	print("Data written in json format in aliexpress.txt\n")

startScrapping()
