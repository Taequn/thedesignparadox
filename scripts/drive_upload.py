from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

class GoogleDriveUploader:
    def __init__(self):
        self.settings_path = "config/settings.yaml"
        self.gauth = GoogleAuth(settings_file=self.settings_path)
        self.drive = GoogleDrive(self.gauth)

    def upload_file(self, file_to_upload, file_name, folder):
        file = self.drive.CreateFile({'title': file_name, 'parents': [{'id': folder}]})
        file.SetContentFile(file_to_upload)
        file.Upload()
        print('Uploaded: ' + file_name)

    def download_file(self, file_name, folder, download_name):
        file_id = self.get_file_id(file_name, folder)
        if file_id is None:
            print("File not found")
            return
        file = self.drive.CreateFile({'id': file_id})
        file.GetContentFile('output/' + download_name)
        print('Downloaded: ' + file_name)

    def list_files(self, folder):
        files = self.drive.ListFile({'q': "'{}' in parents".format(folder)}).GetList()
        for file in files:
            print('title: %s, id: %s' % (file['title'], file['id']))

    def get_file_id(self, file_name, folder):
        files = self.drive.ListFile({'q': "'{}' in parents".format(folder)}).GetList()
        for file in files:
            if file['title'] == file_name:
                return file['id']
        return None

if __name__ == "__main__":
    pass






































































