from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

class GoogleDriveUploader:
    def __init__(self):
        self.gauth = GoogleAuth()
        self.__authenticate() #run credentials
        self.drive = GoogleDrive(self.gauth)

    def __authenticate(self):
        self.gauth.LoadCredentialsFile("config/mycreds.txt")
        if self.gauth.credentials is None:
            self.gauth.LocalWebserverAuth()
        elif self.gauth.access_token_expired:
            self.gauth.Refresh()
        else:
            self.gauth.Authorize()
        self.gauth.SaveCredentialsFile("config/mycreds.txt")

    def upload_file(self, file_to_upload, file_name, folder):
        file = self.drive.CreateFile({'title': file_name, 'parents': [{'id': folder}]})
        file.SetContentFile(file_to_upload)
        file.Upload()
        print('Uploaded: ' + file_name)


if __name__ == "__main__":
    pass































































