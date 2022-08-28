import json
import bs4 as bs
import time
import pandas as pd
from scrapingbee import ScrapingBeeClient

class BeeScrapper():
    def __init__(self, filename):
        self.df = self.__read_pd(filename)

        self.scraper_wait_time = "6000"
        self.scraper_termination_time = 20
        with open('../config/api_keys.json') as json_file:
            data = json.load(json_file)
            self.scraping_bee_api = data['scrap_api']
            self.scraper = ScrapingBeeClient(self.scraping_bee_api)

    '''
    ###################################
    # HELPER METHODS
    ###################################
    '''
    def __read_pd(self, filename):
        if not filename.endswith('.csv'):
            filename += '.csv'

        path = '../output/' + filename
        read_in = pd.read_csv(path)
        #check if read_in has "Facebook Ads Library" in the column name
        if "Facebook Ads Library" in read_in.columns:
            return read_in
        else:
            raise Exception("File does not have Facebook Ads Library in the column name")

    '''
    ###################################
    # GET METHODS
    ###################################
    '''
    def get_rows(self):
        df = self.df

        for index, row in self.df.iterrows():
            print("#############################################")
            print("{}/{}".format(index, len(df)))
            name = row["name"]
            print("Analyzing {}".format(name))

            if row['Facebook Ads Library'] != "" or row['Facebook Ads Library'] != " " or row['Facebook Ads Library'] is not None:
                link = row['Facebook Ads Library']
                ads = self.get_ads(link)
                if ads == "Timed out":
                    print("Timed out")
                    continue
                if ads is None:
                    print("Failed to find ads")
                    continue
                df.at[index, 'Ads'] = ads
                print("Found " + str(ads) + " ads")

            else:
                df.at[index, 'Facebook Ads Library'] = "No ID"
                print("No ID")

        self.df = df


    def get_ads(self, link):
        if(link is None):
            return None
        url = str(link)
        start_time = time.time()
        while start_time + self.scraper_termination_time > time.time():
            try:
                response = self.scraper.get(url,
                                            params={'wait': self.scraper_wait_time, "block_resources": "False", "premium_proxy": "True"
                                                    })
                html = response.content
                soup = bs.BeautifulSoup(html, 'html.parser')
                divs = soup.find_all('div', attrs={'aria-level': '3'})
                for div in divs:
                    return div.text
            except Exception as e:
                print(e)
                return None
        return "Timed out"

    def get_dataframe(self):
        return self.df

    '''
    ###################################
    # SAVE METHODS
    ###################################
    '''

    def save_dataframe(self, filename):
        path = 'output/' + filename + '.csv'
        self.df.to_csv(path, index=False)


if __name__ == "__main__":
    bee = BeeScrapper('output_spyfu')
    bee.get_rows()
    bee.save_dataframe('output_bee')





































































