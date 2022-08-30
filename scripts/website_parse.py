import json
import requests
import pandas as pd
from urllib.request import Request, urlopen

class WebsiteAnalysis():
    def __init__(self, filename, location):
        self.df = self.__read_pd(filename)
        self.location = location
        self.wait_time = 0.5
        self.upper_click_range = 80000

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

    def __snov_auth(self):
        params = {
            'grant_type':'client_credentials',
            'client_id': self.snov_api,
            'client_secret': self.snov_secret,
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

        df["emailsFound"] = ""
        df["monthlyOrganicClicks"] = ""
        df["monthlyPaidClicks"] = ""
        df["totalClicks"] = ""
        df["top5keywords"] = ""

        for i in range(len(df)):
            try:
                if df.at[i, "name"]=="" or len(df.at[i, "name"])<5:
                    print("Encountered an empty line. Skipping...")
                    continue
                elif df.at[i, "website"]=="" or len(df.at[i, "website"])<5:
                    print("Encountered an empty line. Skipping...")
                    continue

                name = df.at[i, "name"]
                website = df.at[i, "website"]
                print("######" + str(i) + " / " + str(len(df)) + "######")
                print("Working on SEO analysis for " + df.at[i, "name"])
                data = self.get_spyfu_data(website)
                print("Parsed SEO data for " + website)
                df.at[i, "monthlyOrganicClicks"] = int(data["monthlyOrganicClicks"])
                df.at[i, "monthlyPaidClicks"] = int(data["monthlyPaidClicks"])
                df.at[i, "totalClicks"] = int(data["monthlyOrganicClicks"]) + int(data["monthlyPaidClicks"])

            except Exception as e:
                print(e)
                continue

            df.at[i, "top5keywords"] = self.get_spyfu_keywords(website, top_n=5)

            if int(data["monthlyOrganicClicks"]) > self.upper_click_range:
                df.at[i, "monthlyOrganicClicks"] = ""
                df.at[i, "monthlyPaidClicks"] = ""
                df.at[i, "totalClicks"] = ""
                df.at[i, "ratio"] = ""
                df.at[i, "top5keywords"] = ""
            else:
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
        url = Request('https://www.spyfu.com/apis/domain_stats_api/v2/GetLatestDomainStats?domain='+name+'&countryCode=US&api_key=' + self.key,
                      headers={'User-Agent': 'Mozilla/5.0'})

        response = urlopen(url)
        try:
            data = json.loads(response.read())
            return data['results'][0]
        except Exception as e:
            print(e)
            return None

    def get_spyfu_keywords(self, name, top_n=5):
        url = Request('https://www.spyfu.com/apis/url_api/organic_kws?q='+name+'&r=10&api_key=' + self.key,
                        headers={'User-Agent': 'Mozilla/5.0'})
        response = urlopen(url)
        data = json.loads(response.read())
        dictionary = dict()
        for item in data:
            dictionary[item['term']] = item['position']

        sorted_dictionary = sorted(dictionary.items(), key=lambda kv: kv[1], reverse=True)
        print(sorted_dictionary[:top_n])
        return sorted_dictionary[:top_n]

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
    parser = WebsiteAnalysis('beauty shop — Boston, USA.csv', 'Boston, USA')
    print(parser.get_spyfu_data('http://lolabeautyboutique.com/'))








































































