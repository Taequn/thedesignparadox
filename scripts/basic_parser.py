import googlemaps
import pandas as pd
import requests
import bs4 as bs
import time
import json
from googleapiclient.discovery import build
from urllib.parse import urlparse

class BasicParser:
    def __init__(self, niche, location, rating_limit, rating_min, radius):
        self.__check_values(niche, location, rating_limit, rating_min)

        self.df = pd.DataFrame()
        #read api_keys
        self.gmaps_api=None
        self.niche = niche
        if(';' in location):
            self.location = location.split(';')
            self.city = self.location[0].split(',')[1]
        else:
            self.location = [location]
            self.city = location.split(',')[0]



        self.rating_limit = int(rating_limit)
        self.rating_min = int(rating_min)
        self.radius = int(radius)

        #### API KEYS ####
        with open('../config/api_keys.json') as json_file:
            data = json.load(json_file)
            self.gmaps_api = data['g_api']
            self.scraping_bee_api = data['scrap_api']
            self.cse = data['cse_api']
            self.traffic_api = data['traffic_api']

        self.gmaps = googlemaps.Client(key=self.gmaps_api)
        self.sleep_time = 0.5
        self.pages = 0

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

    def __parse_places_results(self, results):
        df = pd.DataFrame(columns=['name', 'formatted_address', 'rating', 'user_ratings_total', 'ID'])

        for place in results['results']:
            try:
                if (int(place['user_ratings_total']) > self.rating_limit or int(
                        place['user_ratings_total']) < self.rating_min):
                    continue
            except KeyError:
                continue

            print("GMAPS PARSER: Parsing place " + str(len(df)) + " of " + str(len(results['results'])))
            place_id = place['place_id']
            website = self.__get_website(place_id)
            monthly_traffic = self.__get_traffic(website)
            time.sleep(self.sleep_time)

            # socials = self.__get_socials_from_website(website)
            # fb_link = socials['Facebook'] if 'Facebook' in socials else None
            # ig_link = socials['Instagram'] if 'Instagram' in socials else None

            df = df.append({'name': place['name'], 'formatted_address': place['formatted_address'],
                            'rating': place['rating'],
                            'user_ratings_total': place['user_ratings_total'],
                            'ID': place['place_id'],
                            'website': website,
                            'monthly_traffic': monthly_traffic}, ignore_index=True)

        return df

    def __google_search(self, search_term, api_key, cse_id, **kwargs):
        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
        return res

    def __google_platform(self, name, platform):
        try:
            query = name + " " + self.city + " " + platform
        except Exception as e:
            print(e)
            return None

        res = self.__google_search(query, self.gmaps_api, self.cse, num=3)

        try:
            for item in res['items']:
                if(platform in item['link']):
                    return item['link']
        except Exception as e:
            print(e)
            return None

        return None

    def __get_website(self, place_id):
        place = self.gmaps.place(place_id)
        try:
            result = place['result']['website']
        except KeyError:
            result = None
        return result

    def __get_socials_from_website(self, link):
        socials = dict()
        socials['Facebook'] = None
        socials['Instagram'] = None

        if link is None:
            return socials

        try:
            page = requests.get(link)
            soup = bs.BeautifulSoup(page.content, 'html.parser')
            for i in soup.find_all('a'):
                if('href' in i.attrs):
                    if('facebook.com' in i['href']):
                        socials['Facebook'] = i['href']
                    elif('instagram.com' in i['href']):
                        socials['Instagram'] = i['href']
        except Exception as e:
            print(e)
            return socials

        return socials

    def __get_locations(self):
        df = self.df
        df['openLocations'] = df.groupby('website')['website'].transform('count')

    def __get_facebook_id(self, link):
        if link is None:
            return None

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

    def __get_facebook_likes(self, link):
        if link is None:
            return None

        page = requests.get(link)
        soup = bs.BeautifulSoup(page.content, 'html.parser')
        for i in soup.find_all('meta'):
            if('content' in i.attrs):
                if('likes' in i['content']):
                    position = i['content'].find('likes')
                    end_at = i['content'][:position]
                    start_from = end_at.rfind('.')
                    return end_at[start_from+1:]

        return None

    def __get_traffic(self, link):
        if not isinstance(link, str):
            return None

        domain = urlparse(link).netloc

        url = "https://endpoint.sitetrafficapi.com/pay-as-you-go/?key="+self.traffic_api+"&host="+domain
        request = requests.get(url)
        try:
            data = json.loads(request.text)
            resp = data['data']['estimations']['visitors']['monthly']
            if(resp == "0"):
                return "<5,000"
            else:
                return resp
        except Exception as e:
            print(e)
            return "ERROR"

    '''
    ###################################
    GET FUNCTIONS
    ###################################
    '''
    def get_dataframe(self):
        return self.df

    def get_places(self, attempts=0, loc=None):
        print("############################################")
        print("Beginning parsing: " + loc)

        place = self.gmaps.geocode(loc)
        time.sleep(self.sleep_time*2)
        lat = place[0]['geometry']['location']['lat']
        lng = place[0]['geometry']['location']['lng']
        location = str(lat) + "," + str(lng)

        result = []
        parsed_places = self.gmaps.places(self.niche, location=location, radius=self.radius)
        result.append(parsed_places)
        df = self.__parse_places_results(parsed_places)
        print(loc+": Finished the first page")
        self.pages += 1

        while "next_page_token" in parsed_places:
            print(loc+": Starting the next page")
            parsed_places = self.gmaps.places(page_token=parsed_places["next_page_token"])
            df = df.append(self.__parse_places_results(parsed_places))
            print(loc+": Finished the next page")
            self.pages += 1

        print("Found " + str(len(df)) + " places at " + loc)
        if(len(df) == 0):
            if(attempts < 3):
                print("Error getting places: trying again")
                return self.get_places(attempts=attempts+1)
            else:
                raise Exception("Did not find any places: try again! Google API issue!")

        print("############################################")
        return df

    def get_facebook_page(self, file_to_read=None):
        if(file_to_read is not None):
            df = pd.read_csv(file_to_read)
        else:
            df = self.df

        print("############################################")
        print("Beginning parsing facebook pages")

        #Init columns
        df['Facebook'] = ""
        df['Instagram']= ""
        df['Facebook ID'] = ""
        df['Facebook Likes'] = ""
        df['Facebook Ads Library'] = ""
        df['Ads'] = ""

        for i in range(len(df)):
            name = df.iloc[i]['name']
            website = df.iloc[i]['website']
            print("FACEBOOK PARSER: " + name)
            print("POSITION: " + str(i) + "/" + str(len(df)))

            fb_link = self.__google_platform(website, "facebook")
            df.at[i, 'Facebook'] = fb_link
            df.at[i, 'Instagram'] = self.__google_platform(website, "instagram")
            df.at[i, 'Facebook Likes'] = self.__get_facebook_likes(fb_link)

            id = self.__get_facebook_id(fb_link)
            df.at[i, 'Facebook ID'] = id

            if(id is not None):
                print("Found FB ID: " + id)
                ads_library_url = "https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&view_all_page_id=" + id + "&sort_data[direction]=desc&sort_data[mode]=relevancy_monthly_grouped&search_type=page&media_type=all"
            else:
                print("Did not find FB ID")
                ads_library_url = None
                ads_running = None

            df.at[i, 'Facebook Ads Library'] = ads_library_url
            print("\n")

        df = df[df['Facebook'] != ""]
        df = df.drop_duplicates(subset=['Facebook'])
        df = df.reset_index(drop=True)
        self.df = df

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

    '''
    ###################################
    RUN FUNCTION
    ###################################
    '''
    def run_locations(self):
        big_df = pd.DataFrame()
        for loc in self.location:
            print("DOING LOCATION: " + loc.upper())
            df = self.get_places(loc=loc)
            big_df = big_df.append(df)
            print(big_df)
        big_df = big_df.drop_duplicates(subset=['name']) #remove duplicates by name
        big_df = big_df.reset_index(drop=True) #reset index after appending

        self.df = big_df



    def run(self):
        self.run_locations()
        self.get_facebook_page()
        if(self.pages == 3):
            print("############################################")
            print("WARNING: 60 places were parsed, choose one more location")
            print("############################################")

# TODO:
# — Добавить ранжировать по рейтингу
# — ID спрятать.
# —
if __name__ == "__main__":
    parse = BasicParser("bjj gym", "The Bronx, New York City, USA; Harlem, New York City, USA", 150, 0, 1000)
    parse.run()
    parse.save_dataframe("bjj_gym.csv")





























































