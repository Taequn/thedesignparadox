import googlemaps
from datetime import datetime
import pandas as pd
from googlesearch import search
import requests
import bs4 as bs
import undetected_chromedriver as uc
import time

# gmaps = googlemaps.Client(key='')
# #find pizza places in New york
# pizza_places = gmaps.places('cooking class', location='New York City')
# #iterate through the results
# #Columns to use: name, formatted_address, rating, user_ratings_total
# #Create a dataframe with the columns
# df = pd.DataFrame(columns=['name', 'formatted_address', 'rating', 'user_ratings_total'])
# for place in pizza_places['results']:
#     df = df.append({'name': place['name'], 'formatted_address': place['formatted_address'], 'rating': place['rating'], 'user_ratings_total': place['user_ratings_total']}, ignore_index=True)
#
# df.to_csv('cooking_class_NY.csv')


def add_facebook_page(filename, query):
    df = pd.read_csv(filename)
    df['Facebook'] = ""

    for i in range(len(df)):
        name = df.iloc[i]['name']
        rating = df.iloc[i]['user_ratings_total']

        if rating > 100:
            continue

        look_for = name + " " + query + " facebook"
        print(name)

        for j in search(look_for, tld="com", num=3, stop=3):
            if("facebook.com" in j):
                print(j)
                df.at[i, 'Facebook'] = j
                break

    df = df[df['Facebook'] != ""]

    save_name = filename.split('.')[0] + "_facebook.csv"
    df.to_csv(save_name)

def get_facebook_id(filename):
    df = pd.read_csv(filename)
    df['Facebook ID'] = ""
    df['Ads Library'] = ""

    for index, row in df.iterrows():
        url = df['Facebook'][index]
        if url != "":
            try:
                page = requests.get(url)
                soup = bs.BeautifulSoup(page.content, 'html.parser')
                for i in soup.find_all('script'):
                    text = i.text
                    if('pageID' in text):
                        position = text.find('pageID')
                        #from position+8 to the quote
                        start_from = text[position+9:]
                        end_at = start_from.find('"')
                        page_id = start_from[:end_at]
                        print(page_id)
                        df.at[index, 'Facebook ID'] = str(page_id)
                        ads_library_url = "https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&view_all_page_id=" + page_id + "&sort_data[direction]=desc&sort_data[mode]=relevancy_monthly_grouped&search_type=page&media_type=all"
                        df.at[index, 'Ads Library'] = ads_library_url
                        break
            except Exception as e:
                print(e)
                df.at[index, 'Facebook ID'] = "ERROR"

    df.loc[df['Facebook ID'] == "", 'Ads Library'] = ""

    df = df.iloc[:, 2:]
    save_name = filename.split('.')[0] + "_facebook_id.csv"
    df.to_csv(save_name)

def parse_ad(filename):
    df = pd.read_csv(filename)
    df['Published Ads'] = ""

    driver = uc.Chrome(headless=True)
    for i in range(len(df)):
        try:
            url = df['Ads Library'][i]
            if len(url) < 5:
                continue
            name = df['name'][i]
            print("Parsing " + name)
            print(i, "/", len(df))
            driver.get(url)
            time.sleep(5)
            html = driver.page_source
            soup = bs.BeautifulSoup(html, 'html.parser')
            divs = soup.find_all('div', attrs={'aria-level': '3'})
            for div in divs:
                print(div.text)
                df.at[i, 'Published Ads'] = div.text
                break
        except Exception as e:
            print(e)
            continue
    driver.quit()

    save_name = filename.split('.')[0] + "_published_ads.csv"
    df.to_csv(save_name)



if __name__ == "__main__":
    #add_facebook_page('cooking_class_NY.csv', 'New York City')
    #get_facebook_id('cooking_class_NY_Facebook.csv')
    parse_ad('cooking_class_NY_Facebook_facebook_id.csv')







































