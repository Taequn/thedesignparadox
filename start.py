from scripts.basic_parser import BasicParser
from scripts.drive_upload import GoogleDriveUploader
import datetime

class MainMenu:
    def __init__(self):
        self.niche = None
        self.location = None
        self.rating_limit = None
        self.radius = None
        self.type = None

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

        self.niche = niche
        self.location = location
        self.rating_limit = rating_limit

    def set_type(self):
        confirmed = False
        while not confirmed:
            print("Enter the type of search you want to do:")
            print("1. Wider search with no radius limit")
            print("2. Search with radius limit")
            choice = input("Enter your choice (1 or 2): ")
            if choice == "1":
                self.type = "wide"
                confirmed = True
            elif choice == "2":
                self.type = "radius"
                confirmed = True
                self.__set_radius()
            else:
                print("Invalid choice")
                continue

    def __set_radius(self):
        confirmed = False
        while not confirmed:
            print("Enter the radius you want to search for:")
            radius = input("Enter a radius (m): ")
            try:
                self.radius = int(radius)
                confirmed = True
            except Exception as e:
                print(e)
                continue

    def set_variables(self):
        print("#############################################")
        print("# Welcome to The Design Paradox Parser! #")
        print("#############################################")

        confirmed = False
        while not confirmed:
            self.set_search()
            self.set_type()

            print("\n#############################################")
            print("Niche: " + self.niche)
            print("Location: " + self.location)
            print("Rating limit: " + str(self.rating_limit))
            if self.type == "wide":
                print("Type: Wider search with no radius limit")
            elif self.type == "radius":
                print("Type: Search with radius limit")
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

    def run(self):
        self.set_variables()
        parser = BasicParser(self.niche, self.location, self.rating_limit)
        if self.type == "wide":
            parser.get_places()
        else:
            parser.get_places_nearby(self.radius)

        parser.get_facebook_page()
        parser.save_dataframe("output/output.csv")
        print("Dataframe saved to output/output.csv")
        uploader = GoogleDriveUploader()
        #name of the file is date — location — niche — rating limit — type
        filename = datetime.datetime.now().strftime("%Y-%m-%d") + " — " + self.location + " — " + self.niche + " — " \
                   + str(self.rating_limit) + " — " + self.type + ".csv"
        uploader.upload_file("output/output.csv", filename, "10rZTP5jXSyOCIllT_6hxqGTTVCvcWXy3")





#To-do:
#1) Upload to google sheets and google drive
#2) Make basic UI

if __name__ == "__main__":
    menu = MainMenu()
    menu.run()


























































