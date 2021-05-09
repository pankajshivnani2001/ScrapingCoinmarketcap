#!/usr/bin/env python
# coding: utf-8

# In[27]:


from bs4 import BeautifulSoup
import requests
import csv
import os


def get_coins():
    soup = create_soup("https://coinmarketcap.com/coins")
    
    coin_names = []
    coin_symbols = []
    coin_urls = []
    
    coin_tags = soup.select(".sc-16r8icm-0.dnwuAU")
    for x in coin_tags:
        p_tags = x.find_all("p")
        name = p_tags[0].text
        symbol = p_tags[1].text
        coin_names.append(name)
        coin_symbols.append(symbol)

        a_tags = x.find_all("a", href = True)
        for a_tag in a_tags:
            tag = "coinmarketcap.com" + a_tag["href"]
            coin_urls.append(tag)
            
    
    #Beautiful Soup seems to render the page differently. On analyzing the soup structure using .prettify() function
    #we see that top 10 coins have different class and the rest belong to some other class. 
    #So we change the coin_tags to get tags with that class.
    
    coin_tags = soup.select(".sc-14kwl6f-0.fletOv")
    for i in coin_tags:
        coin_symbols.append(i.find("span", attrs = {"class":"crypto-symbol"}).text)
        coin_urls.append("coinmarketcap.com" + i.find("a", attrs = {"class":"cmc-link"})["href"])
        coin_names.append(i.find("span", attrs = {"class":"circle"}).find_next().text)

    
    #Fetching just the top 50 coins
    coin_names = coin_names[:50]
    coin_symbols = coin_symbols[:50]
    coin_urls = coin_urls[:50]
    
    #Writing to the coins.csv file.
    with open('coins.csv', mode='w+') as coins_file:
        writer = csv.writer(coins_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        col_names = ['SNO', 'Name', "Symbol", "URL"]

        writer.writerow(col_names)
        for i in range(1, 51):
            row = [str(i), coin_names[i-1], coin_symbols[i-1], coin_urls[i-1]]
            writer.writerow(row)
    
                 
def get_coin_data(coin_symbol):
    #Fetching the URL from coins.csv file
    url = fetch_url('coins.csv', coin_symbol)
    
    if url == None:
        print("No Such Coin Found")
        return
    else:
        soup2 = create_soup(url)
        
        data_dict = {}
        
        #Fetching name, symbol, watchlist, website and supply chain %
        name_symbol_tag = soup2.select(".sc-1q9q90x-0.iYFMbU.h1___3QSYG")
        name = name_symbol_tag[0].text
        symbol = name_symbol_tag[0].find_next("small").text
        name = name[:len(name) - len(symbol)]

        watchlist_tag = soup2.select(".namePill___3p_Ii")
        watchlist = watchlist_tag[2].text

        website_tag = soup2.select(".button___2MvNi")
        website = website_tag[0].text

        supply_chain_percent_tag = soup2.select(".supplyBlockPercentage___1g1SF")
        supply_chain_percent = supply_chain_percent_tag[0].text

        data_dict["Symbol"] = symbol
        data_dict["Name"] = name
        data_dict["Watchlist"] = watchlist
        data_dict["Website"] = website
        data_dict["Supply Chain %"] = supply_chain_percent
        
        #Fetching price, volume/market cap, market dominance, rank, market cap, all time high and low data 
        #from the table on the website
        th = soup2.select("th")
        td = soup2.select("td")
        for i in range(len(th)):
            if th[i].text == (name + " Price"):
                data_dict["Price"] = td[i].text
                
            if th[i].text == "Volume / Market Cap":
                data_dict["Volume / Market Cap"] = td[i].text
                
            if th[i].text == "Market Dominance":
                data_dict["Market Dominance"] = td[i].text
                
            if th[i].text == "Market Rank":
                data_dict["Market Rank"] = td[i].text
                
            if th[i].text == "Market Cap":
                data_dict["Market Cap"] = td[i].find_next("span").text
                
            if th[i].find_next("div").text == "All Time High":
                data_dict["All Time High Date"] = th[i].find_next("small").text
                data_dict["All Time High Price"] = td[i].find_next("span").text
                
            if th[i].find_next("div").text == "All Time Low":
                data_dict["All Time Low Date"] = th[i].find_next("small").text
                data_dict["All Time Low Price"] = td[i].find_next("span").text
        
 

        #Fetching basic info about the coin.
        #The id for this information's tag seems to have three different type- 
        #1 -> #what-is-<coin_name>-<coin_symbol>
        #2 -> #what-is-<coin_name>
        #3 -> The third type of id is used when the coin name is made of more than 1 word like Ethereum Classic. In that case 
        #there is a hyphen between the words.
        if len(name.split(" ")) > 1:
            name = name.replace(" ", "-")
        what_tag_id = "#what-is-" + name.lower() + "-" + symbol.lower()
        what_tag = soup2.select(what_tag_id)

        if len(what_tag) == 0:
            what_tag_id = "#what-is-" + name.lower()
            what_tag = soup2.select(what_tag_id)
            if len(what_tag) == 0:
                data_dict["What is <coin-name>?"] = "N/A"

            else:
                what_tag = what_tag[0]
                what = ""
                while what_tag.find_next("p"):
                    if what_tag.find_next_sibling().name != "p":
                        break
                    what += what_tag.find_next("p").text
                    what_tag = what_tag.find_next("p")      
                data_dict["What is <coin-name>?"] = what

        else:
                    what_tag = what_tag[0]
                    what = ""
                    while what_tag.find_next("p"):
                        if what_tag.find_next_sibling().name != "p":
                            break
                        what += what_tag.find_next("p").text
                        what_tag = what_tag.find_next("p")      
                    data_dict["What is <coin-name>?"] = what
        
        
        #Fetching the Founder info of the coin.
        founder_tag_id = "#who-are-the-founders-of-" + name.lower()
        founder_tag = soup2.select(founder_tag_id)
        if len(founder_tag) == 0:
            data_dict["Who Are The Founders"] = "N/A"
        else:
            founder_tag = founder_tag[0]
            founder = ""
            while founder_tag.find_next("p"):
                if founder_tag.find_next_sibling().name != "p":
                    break
                founder += founder_tag.find_next("p").text
                founder_tag = founder_tag.find_next("p")
            data_dict["Who Are The Founders"] = founder

        
        #Fetching the unique things about the coin.
        unique_tag_id = "#what-makes-" + name.lower() + "-unique"
        unique_tag = soup2.select(unique_tag_id)
        if len(unique_tag) == 0:
            data_dict["What Makes it Unique"] = "N/A"
        else:
            unique_tag = unique_tag[0]
            unique = ""
            ct = 0
            while True:
                if unique_tag.find_next_sibling().name != "p":
                    break
                unique += unique_tag.find_next("p").text
                unique_tag = unique_tag.find_next("p")

            data_dict["What Makes it Unique"] = unique
        
        
        
        col_names = ['Symbol', 'Name', 'Watchlist', 'Website', 'Supply Chain %', 'Price', 'Volume / Market Cap',
                    'Market Dominance', 'Market Rank', 'Market Cap', 'All Time High Date', 'All Time High Price',
                    'All Time Low Date', 'All Time Low Price', 'What is <coin-name>?', 'Who Are The Founders',
                    'What Makes it Unique']
        
        #Storing in the File
        write_to_file("coins_data.csv", col_names, data_dict)
        

#Function to create a soup object
def create_soup(url):
    webpage = requests.get(url)
    soup = BeautifulSoup(webpage.text, 'lxml')
    return soup


#Function to fetch the url
def fetch_url(filename, symbol):
    url = ""
    with open(filename, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            if row["Symbol"] == symbol:
                url = row["URL"]
    
    if url == "":
        print("No Such Coin Found")
        return None
    else:
        url = "https://" + url
        return url
    

#Funtion to write a python dictionary to a csv file
def write_to_file(filename, col_names, data_dict):
    if os.path.isfile(filename):
        with open(filename, mode='a', encoding = "utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames = col_names)
            writer.writerow(data_dict)  
            csv_file.close()
    else:
        with open(filename, mode='w+', encoding = "utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=col_names)
            writer.writeheader()
            writer.writerow(data_dict)
            csv_file.close()
            
            

