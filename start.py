from scripts.basic_parser import BasicParser
from scripts.drive_upload import GoogleDriveUploader
from scripts.website_parse import WebsiteAnalysis
import datetime
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

class MainMenu:
    def __init__(self):
        self.niche = None
        self.location = None
        self.rating_limit = None
        self.rating_min = None
        self.radius = None
        self.choice = -1


        #SPYFU
        self.filename = None
        self.replace = False

    '''
    ##############################################
    # SPYFU PARSER METHODS #
    ##############################################
    '''
    #Set the name of the file to be uploaded to Google Drive
    def set_spyfu_variables(self):
        print("#############################################")
        print("# Welcome to The SpyFu Parser! #")
        print("#############################################")

        confirmed = False
        while not confirmed:

            if(self.filename is None):
                print("Enter the file you want to analyze:")
                filename = input("Enter a filename: ")
                if filename == "":
                    print("Invalid filename")
                    continue
                if not filename.endswith(".csv"):
                    filename += ".csv"

                self.filename = filename


            if(self.choice != 3): #if they are not doing both
                print("Do you want to replace the existing file? (y/n)")
                choice = input("Enter your choice (y/n): ")
                if choice == "y":
                    self.replace = True
                elif choice == "n":
                    self.replace = False
                else:
                    print("Invalid choice")
                    continue
            else:
                self.replace = True

            confirmed = True

        self.location = self.filename.split(" — ")[1]

    '''
    ##############################################
    # BASIC GOOGLE MAPS PARSER METHODS #
    ##############################################
    '''
    def set_search(self):
        print("Enter the niche you want to search for:")
        niche = input("Enter a niche: ")
        print("Enter the location you want to search for:")
        location = input("Enter a location: ")
        print("Enter the rating limit you want to search for:")

        integer = False
        while not integer:
            rating_limit = input("Enter a rating limit (integer): ")
            try:
                rating_limit = int(rating_limit)
                integer = True
            except Exception as e:
                print(e)
                print("Invalid input")
                continue

        integer = False
        while not integer:
            rating_min = input("Enter a rating minimum (integer): ")
            try:
                rating_min = int(rating_min)
                integer = True
            except Exception as e:
                print(e)
                print("Invalid input")
                continue

        self.niche = niche
        self.location = location
        self.rating_limit = rating_limit
        self.rating_min = rating_min

    def __set_radius(self):
        confirmed = False
        while not confirmed:
            print("Enter the radius you want to search for:")
            radius = input("Enter a radius (km): ")
            try:
                radius = int(radius)
                self.radius = radius * 1000
                confirmed = True
            except Exception as e:
                print(e)
                continue

    def set_variables(self):
        print("#############################################")
        print("# Welcome to The Basic Google Maps Parser! #")
        print("#############################################")

        confirmed = False
        while not confirmed:
            self.set_search()
            self.__set_radius()

            print("\n#############################################")
            print("Niche: " + self.niche)
            print("Location: " + self.location)
            print("Rating limit: " + str(self.rating_limit))
            print("Rating minimum: " + str(self.rating_min))
            print("Radius: " + str(self.radius))
            print("#############################################\n")
            choice = input("Is this correct? (y/n): ")
            if choice == "y":
                confirmed = True
            elif choice == "n":
                print("Starting over...")
                continue
            else:
                print("Invalid choice. Starting over...")
                continue
    
    def set_variables_manually(self, niche, location, max, min, radius, choice):
        self.niche = niche
        self.location = location
        self.rating_limit = max
        self.rating_min = min
        self.radius = radius
        self.choice = choice

    '''
    ##############################################
    # RUN FUNCTIONS #
    ##############################################
    '''
    def run_maps_parser(self, auto=True):
        if(auto):
            self.set_variables()
        parser = BasicParser(self.niche, self.location, self.rating_limit, self.rating_min, self.radius)
        parser.run()
        parser.save_dataframe("output/output.csv")
        print("Dataframe saved to output/output.csv")
        uploader = GoogleDriveUploader()
        #name of the file is date — location — niche — rating limit — type
        filename = datetime.datetime.now().strftime("%Y-%m-%d") + " — " + self.location + " — " + self.niche + " — " \
                   + str(self.rating_limit) + " — " + str(self.radius) + ".csv"
        self.filename = filename
        uploader.upload_file("output/output.csv", filename, "10rZTP5jXSyOCIllT_6hxqGTTVCvcWXy3")

    def run_spyfu_parser(self):
        self.set_spyfu_variables()
        uploader = GoogleDriveUploader()
        #def download_file(file_name, folder, download_name):
        uploader.download_file(self.filename, "10rZTP5jXSyOCIllT_6hxqGTTVCvcWXy3", "output_spyfu.csv")

        parser = WebsiteAnalysis('output_spyfu.csv', self.location)
        parser.get_traffic_analysis()
        parser.save_dataframe("output_spyfu")

        uploader.upload_file("output/output_spyfu.csv", self.filename, "10rZTP5jXSyOCIllT_6hxqGTTVCvcWXy3",
                             replace=self.replace)

    def run_parsers(self):
        print("#############################################")
        print("# Welcome to The Design Paradox App! #")
        print("#############################################")

        print("Choose a parser:")
        print("1. Basic Google Maps Parser")
        print("2. SpyFu Parser")
        print("3. Both")
        confirmed = False
        while not confirmed:
            choice = input("Enter your choice (1, 2, 3): ")

            try:
                choice = int(choice)
                if choice == 1 or choice == 2 or choice == 3:
                    confirmed = True
                    self.choice = choice
                else:
                    print("Invalid choice")
                    continue
            except Exception as e:
                print(e)
                print("Try again!")
                continue


    def run(self, auto=True):
        if auto:
            self.run_parsers()
        if(self.choice == 1):
            self.run_maps_parser(auto)
        elif(self.choice == 2):
            self.run_spyfu_parser()
        elif(self.choice == 3):
            self.run_maps_parser(auto)
            self.run_spyfu_parser()

#Todo:
# — Implement Google Sheets API to upload data to Google Sheets
# - Change the way save and open works (inconsistency between output included and excluded)
if __name__ == "__main__":
    list_of_niches = ['Wellness center', 'Hair salon', 'SPA', 'Nail salon',
    'Sport clothes', 'Yoga clothes', 'Home accessories', 'Furniture',
    'Pet food', 'Fishing store', 'hunting store', 'Cosmetics',
    'Grooming', 'Camping', 'Gym', 'Cooking classes', 'Yoga classes',
    'HIIT classes', 'Music classes', 'Art classes', 'Pilates classes',
    'Weight loss', 'Art and craft shop', 'CBD shop', 'Essential oils shop',
    'Food supplements', 'Dance classes', 'Barber shop', 'Martial arts classes',
    'Wedding salon']

    locations = "Bronx, NYC, USA; Brooklyn, NYC, USA; Manhattan, NYC, USA; Queens, NYC, USA; Staten Island, NYC, USA"
    parser = MainMenu()
    for niche in list_of_niches:
        parser.set_variables_manually(niche, locations, 5000, 20, 40000, 3)
        parser.run(auto=False)