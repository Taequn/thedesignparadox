import json
import requests
from googleapiclient.discovery import build
import pandas as pd

class WebsiteAnalysis():
    def __init__(self, filename, location):
        self.df = self.__read_pd(filename)
        self.location = location
        self.wait_time = 2

        with open('config/api_keys.json') as json_file:
            data = json.load(json_file)
            self.api = data['spyfu_api']
            self.key = data['spyfu_key']
            self.g_api = data['g_api']
            self.cse = data['cse_api']
            self.snov_api = data['snov_api']
            self.snov_secret = data['snov_secret']

        self.snov_token = self.__snov_auth()

    '''
    ###################################
    # HELPER METHODS
    ###################################
    '''
    def __read_pd(self, filename):
        path = 'output/' + filename
        return pd.read_csv(path)

    def __google_search(self, search_term, api_key, cse_id, **kwargs):
        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
        return res

    def __snov_auth(self):
        params = {
            'grant_type':'client_credentials',
            'client_id': self.snov_api,
            'client_secret': self.snov_api
        }

        res = requests.post('https://api.snov.io/v1/oauth/access_token', data=params)
        resText = res.text.encode('ascii','ignore')

        return json.loads(resText)['access_token']


    '''
    ###################################
    # GET METHODS
    ###################################
    '''
    def get_traffic_analysis(self):
        df = self.df

        df["website"] = ""
        df["emailsFound"] = ""
        df["monthlyOrganicClicks"] = ""
        df["monthlyPaidClicks"] = ""
        df["totalClicks"] = ""
        df["ratio"] = ""
        df["top5keywords"] = ""

        for i in range(len(df)):
            #if the line is empty
            try:
                if df.at[i, "name"]=="" or len(df.at[i, "name"])<5:
                    print("Encountered an empty line. Skipping...")
                    continue
            except Exception as e:
                print(e)
                continue

            name = df.at[i, "name"]
            print("######" + str(i) + " / " + str(len(df)) + "######")
            print("Working on SEO analysis for " + df.at[i, "name"])
            website = self.get_website(name)
            df.at[i, "website"] = website
            data = self.get_spyfu_data(website)
            print("Parsed SEO data for " + website)
            df.at[i, "monthlyOrganicClicks"] = int(data["monthlyOrganicClicks"])
            df.at[i, "monthlyPaidClicks"] = int(data["monthlyPaidClicks"])
            df.at[i, "totalClicks"] = int(data["monthlyOrganicClicks"]) + int(data["monthlyPaidClicks"])

            ratio = int(data["monthlyPaidClicks"])/int(data["monthlyOrganicClicks"])
            ratio = round(ratio, 2)
            df.at[i, "ratio"] = ratio
            df.at[i, "top5keywords"] = self.get_spyfu_keywords(website, top_n=5)

            try:
                df.at[i, "emailsFound"] = self.get_snov_emails(website)
            except Exception as e:
                print(e)
                df.at[i, "emailsFound"] = 0
                continue
            print("Parsed the number of emails for " + name)
            print("#############################")

        self.df = df

    def get_spyfu_data(self, name):
        url = "https://www.spyfu.com/apis/domain_stats_api/v2/GetLatestDomainStats?domain="+name+"&countryCode=US&api_key=" + self.key
        response = requests.get(url)
        data = json.loads(response.text)
        return data['results'][0]

    def get_spyfu_keywords(self, name, top_n=5):
        url = "https://www.spyfu.com/apis/url_api/organic_kws?q="+name+"&r=10&api_key=" + self.key
        response = requests.get(url)
        data = json.loads(response.text)
        dictionary = dict()
        for item in data:
            dictionary[item['term']] = item['position']

        sorted_dictionary = sorted(dictionary.items(), key=lambda kv: kv[1], reverse=True)
        print(sorted_dictionary[:top_n])
        return sorted_dictionary[:top_n]

    def get_website(self, name):
        ignore = ["facebook.com", "instagram.com"]
        query = name + " " + self.location + " website"
        res = self.__google_search(query, self.g_api, self.cse, num=3)
        for item in res['items']:
            if not any(word in item['link'] for word in ignore):
                print("Found the website: " + item['link'])
                return item['link']

    def get_snov_emails(self, website):
        params = {'access_token': self.snov_token,
                  'domain': website,
                  }
        res = requests.post('https://api.snov.io/v1/get-domain-emails-count', data=params)

        return json.loads(res.text)["result"]

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
    pass





































































