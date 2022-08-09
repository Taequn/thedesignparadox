import googlemaps
import pandas as pd
from googlesearch import search
import requests
import bs4 as bs
import time
from scrapingbee import ScrapingBeeClient
import json

class BasicParser:
    def __init__(self, niche, location, rating_limit, rating_min):
        self.__check_values(niche, location, rating_limit, rating_min)

        self.df = pd.DataFrame()
        #read api_keys
        self.gmaps_api=None
        self.niche = niche
        self.location = location
        self.rating_limit = int(rating_limit)
        self.rating_min = int(rating_min)

        self.scraper_wait_time = "5000"

        #### API KEYS ####
        with open('config/api_keys.json') as json_file:
            data = json.load(json_file)
            self.gmaps_api = data['g_api']
            self.scraping_bee_api = data['scrap_api']

            self.scraper = ScrapingBeeClient(self.scraping_bee_api)

    '''
    ###################################
    PRIVATE HELPER FUNCTIONS
    ###################################
    '''

    #check if all values are valid
    def __check_values(self, niche, location, rating_limit, rating_min):
        if niche is None:
            raise ValueError("Niche is None")
        if location is None:
            raise ValueError("Location is None")
        if rating_limit is None:
            raise ValueError("Rating limit is None")
        if rating_min is None:
            raise ValueError("Rating min is None")
        if rating_limit < rating_min:
            raise ValueError("Rating limit is less than rating min")

        return True

    def __parse_places_results(self, results, sleep_time=2, type="place"):
        if(type == "place"):
            df = pd.DataFrame(columns=['name', 'formatted_address', 'rating', 'user_ratings_total'])

            for place in results['results']:
                df = df.append({'name': place['name'], 'formatted_address': place['formatted_address'],
                                'rating': place['rating'],
                                'user_ratings_total': place['user_ratings_total']}, ignore_index=True)
        else:
            df = pd.DataFrame(columns=['name', 'rating', 'user_ratings_total'])

            for place in results['results']:
                df = df.append({'name': place['name'],
                                'rating': place['rating'],
                                'user_ratings_total': place['user_ratings_total']}, ignore_index=True)

        time.sleep(sleep_time)
        return df


    '''
    ###################################
    GET FUNCTIONS
    ###################################
    '''
    def get_dataframe(self):
        return self.df

    def get_places(self, attempts=0):
        print("############################################")
        print("Beginning parsing places")
        gmaps = googlemaps.Client(key=self.gmaps_api)
        parsed_places = gmaps.places(self.niche, location=self.location)
        df = self.__parse_places_results(parsed_places)
        print("Finished the first page")

        while "next_page_token" in parsed_places:
            parsed_places = gmaps.places(page_token=parsed_places["next_page_token"])
            df = df.append(self.__parse_places_results(parsed_places))
            print("Finished the next page")


        df = df.drop_duplicates(subset=['name']) #remove duplicates by name
        df = df[df['user_ratings_total'] <= self.rating_limit] #remove places with higher rating than the limit
        df = df[df['user_ratings_total'] >= self.rating_min] #remove places with lower rating than the min
        df = df.reset_index(drop=True) #reset index after appending

        print("Found " + str(len(df)) + " places")
        if(len(df) == 0):
            if(attempts < 3):
                print("Error getting places: trying again")
                return self.get_places(attempts=attempts+1)
            else:
                raise Exception("Did not find any places: try again! Google API issue!")

        print("############################################")
        self.df = df

    def get_places_nearby(self, radius=1000, attempts=0):
        print("############################################")
        print("Beginning parsing places")
        gmaps = googlemaps.Client(key=self.gmaps_api)
        place = gmaps.geocode(self.location)
        time.sleep(4)
        lat = place[0]['geometry']['location']['lat']
        lng = place[0]['geometry']['location']['lng']

        try:
            parsed_places = gmaps.places_nearby(location=str(lat) + "," + str(lng), radius=radius, keyword=self.niche)
            df = self.__parse_places_results(parsed_places, type="nearby")
            print("Finished the first page")

            while "next_page_token" in parsed_places:
                parsed_places = gmaps.places_nearby(page_token=parsed_places["next_page_token"])
                df = df.append(self.__parse_places_results(parsed_places, type="nearby"))
                print("Finished the next page")

        except Exception as e:
            print(e)
            return None

        df = df.drop_duplicates(subset=['name']) #remove duplicates by name
        df = df[df['user_ratings_total'] <= self.rating_limit] #remove places with higher rating than the limit
        df = df[df['user_ratings_total'] >= self.rating_min] #remove places with lower rating than the min
        df = df.reset_index(drop=True) #reset index after appending
        if(len(df) == 0):
            if(attempts < 3):
                print("Error getting places: trying again")
                return self.get_places_nearby(radius=radius, attempts=attempts+1)
            else:
                raise Exception("Did not find any places: try again! Google API issue!")


        print("Found " + str(len(df)) + " places")
        print("############################################")
        self.df = df

    def get_facebook_page(self, file_to_read=None):
        if(file_to_read is not None):
            df = pd.read_csv(file_to_read)
        else:
            df = self.df

        print("############################################")
        print("Beginning parsing facebook pages")

        df['Facebook'] = ""
        df['Facebook ID'] = ""
        df['Facebook Ads Library'] = ""
        df['Ads'] = ""
        total_time = (int(self.scraper_wait_time)/1000)*len(df)
        for i in range(len(df)):
            name = df.iloc[i]['name']
            print("TIME REMAINING: " + str(total_time - i*(int(self.scraper_wait_time)/1000)))

            look_for = name + " " + self.location + " facebook"
            print(name + " (" + str(i) + "/" + str(len(df)) + ")")

            for j in search(look_for, tld="com", num=3, stop=3):
                if("facebook.com" in j):
                    link = j
                    print("Found FB page: " + link)
                    df.at[i, 'Facebook'] = link
                    id = self.get_facebook_id(link)
                    df.at[i, 'Facebook ID'] = id

                    if(id is not None):
                        print("Found FB ID: " + id)
                        print("Analyzing Ads Library. It may take some time.")
                        ads_library_url = "https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&view_all_page_id=" + id + "&sort_data[direction]=desc&sort_data[mode]=relevancy_monthly_grouped&search_type=page&media_type=all"
                        ads_running = self.get_ads(ads_library_url)
                        try:
                            print("Found " + str(len(ads_running)) + " ads running")
                        except Exception as e:
                            print("Did not find any ads running")
                            ads_running = "ERROR"

                    else:
                        print("Did not find FB ID")
                        ads_library_url = None
                        ads_running = None
                    df.at[i, 'Facebook Ads Library'] = ads_library_url
                    df.at[i, 'Ads'] = ads_running
                    print("\n")
                    break

        df = df[df['Facebook'] != ""]
        self.df = df

    def get_facebook_id(self, link):
        page = requests.get(link)
        soup = bs.BeautifulSoup(page.content, 'html.parser')
        for i in soup.find_all('script'):
            text = i.text
            if('pageID' in text):
                position = text.find('pageID')
                start_from = text[position+9:]
                end_at = start_from.find('"')
                page_id = start_from[:end_at]
                return page_id
        return None

    def get_ads(self, link):
        url = link
        response = self.scraper.get(url,
                          params={'wait': self.scraper_wait_time, "block_resources": "False", "premium_proxy": "True"
                                  })
        html = response.content
        soup = bs.BeautifulSoup(html, 'html.parser')
        divs = soup.find_all('div', attrs={'aria-level': '3'})
        for div in divs:
            return div.text

        return None

    '''
    ###################################
    SAVE FUNCTIONS
    ###################################
    '''
    def save_dataframe(self, file_to_save):
        if(file_to_save is None):
            raise ValueError("File to save is None")
        if(len(self.df) == 0):
            raise ValueError("Dataframe is empty")

        try:
            self.df.to_csv(file_to_save)
        except Exception as e:
            print(e)
            raise Exception("Could not save dataframe")

if __name__ == "__main__":
    parse = BasicParser("Cooking classes", "New York City", 100)
    parse.get_places_nearby(5000)
    parse.get_facebook_page()
    parse.get_dataframe().to_csv("output/test.csv")


























































