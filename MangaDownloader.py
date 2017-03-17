#!/usr/bin/env python3
from getpass import getpass
import shutil
import sys
from time import sleep
from itertools import cycle
import re
from bs4 import BeautifulSoup
import os
import json
import argparse
import urllib.request
import urllib.error
from zipfile import *
import cfscrape
from http.cookiejar import LWPCookieJar

about='''
Crunchyroll MangaDownloader v0.3.2.4 (Crunchymanga v0.3.2.4 for short).
All credit goes to Miguel A(Touman).
You can use this script as suits you. Just do not forget to leave the credit.

If you are in any doubt whatsoever about how to use this script do not hesitate to tell me. Contact me at 7ouman@gmail.com and I'll try to reply as soon as possible.

Beautifulsoup and cfscrape (with its dependencies) are the only external libraries used.

https://github.com/7ouma/CrunchyManga
'''


def xor_crypt(data, key):
    """
    Simple XOR encryption algorithm. XOR encryption is reversible
    :param data: Data to crypt/decrypt
    :param key: The key
    :return: encrypted/decrypted data
    """
    return ''.join(chr(ord(char) ^ ord(key)) for (char, key) in zip(data, cycle(key)))


def zipdir(path, zip):
    for root, dirs, files in os.walk(path):
        for file in files:
            zip.write(os.path.join(root, file))


class Manga:
    def __init__(self):
        self.title = ""
        self.url = ""
        self.volume = "0"


class Config:
    def __init__(self):
        self.dir = "Manga"
        self.zip = False
        self.d_volumes = True
        self.overwrite = False
        self.delete_files = True
        self.json = None

    def write(self):
        f = open("config.json", 'wb')
        f.write(self.json)
        f.close()

    def read(self):
        try:
            with open("config.json") as config_file:
                self.json = json.load(config_file)
                if self.json["dir"]:
                    self.dir = self.json["dir"]
                if self.json["zip"]:
                    self.zip = self.json["zip"]
                if self.json["download_volumes"]:
                    self.d_volumes = self.json["download_volumes"]
                if self.json["overwrite_folders"]:
                    self.overwrite = self.json["overwrite_folders"]
                if self.json["delete_files_after_zip"]:
                    self.delete_files = self.json["delete_files_after_zip"]

        except (OSError, IOError):
            print("Error: {err}".format(err=e))


class MangaDownloader:
    def __init__(self):
        self.folder = os.getcwd()
        self.config = Config()
        self.scraper = cfscrape.create_scraper()
        self.UserAgent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36"

        self.config.read();

    def zip_folder(self, manga):
        previous_folder = os.curdir

        if manga.volume == "0":
            filename = manga.filename
        else:
            filename = manga.filevol

        os.chdir(self.filedir)

        print("\nCreating {filename}.zip\n".format(filename=filename))

        zip_archive = ZipFile(filename+".zip", "w")

        zipdir(filename, zip_archive)

        zip_archive.close()

        os.chdir(previous_folder)

        if self.config.delete_files:
            shutil.rmtree(os.path.join(self.filedir, filename))

    def download_pages(self, pages):
        count = len(pages)
        current = 1
        for page in pages:
            sys.stdout.write("\rPage {cur} of {tot}".format(i, count))
            sys.stdout.flush()

            descarga = self.download_image(pages[i])
            if descarga is not None:
                if (i+1) <= 9:
                    image = "00" + str(i+1) + ".jpg"
                elif (i+1) <= 99:
                    image = "0" + str(i+1) + ".jpg"
                else:
                    image = str(i+1) + ".jpg"
                f = open(image, 'wb')
                f.write(xor_crypt(descarga, "B"))
                f.close()
                i += 1
            else:
                return 0
        return 1

    def download_image(self, img):
        n_try = 1
        while n_try <=9:
            try:
                descarga = urllib.request.urlopen(img).read()
                n_try = 10
                return descarga
            except (urllib.error.URLError, KeyboardInterrupt):
                if n_try < 9:
                    for c in range(31):
                        sys.stdout.write( '\rFailed to download image. Trying again in %d ' %( 30-c ) )
                        sys.stdout.flush()
                        sleep(1)
                else:
                    sys.stdout.write('\rError downloading the chapter. Try again later.')
                    sys.stdout.flush()
                    os.chdir(self.folder)
                    return None
            n_try += 1

    def manga_folder(self, manga_cover =""):
        invalid_characters = ["\\", "/", "?", ":", "*", "\"", "<", ">", "|"]
        os.chdir(self.folder)

        for i in invalid_characters:
            self.manga_title = self.manga_title.replace(i, "")
        loop = True
        while loop:
            if self.dir == "default":
                if os.path.isdir("Manga"):
                    os.chdir("Manga")
                else:
                    os.mkdir("Manga")
                    os.chdir("Manga")
                loop = False
            else:
                if os.path.isdir(self.dir):
                    os.chdir(self.dir)
                    loop = False
                else:
                    print("\n{folder} doesn't exist. Using default folder.".format(folder=self.dir))
                    self.dir = "default"

        if os.path.isdir(self.manga_title):
            os.chdir(self.manga_title)
        else:
            os.mkdir(self.manga_title)
            os.chdir(self.manga_title)
        self.filedir = os.getcwd()
    ##
        self.filevol = self.manga_title + " - Vol." + self.manga_vol
        if not self.manga_vol == "0":
            
            if os.path.isdir(self.filevol):
                os.chdir(self.filevol)
            else:
                os.mkdir(self.filevol)
                os.chdir(self.filevol)
            if not manga_cover == "":
                descarga = self.download_image(manga_cover)
                if descarga is not None:
                    image = "Cover - Vol." + self.manga_vol + ".jpg"
                    f = open(image, "wb")
                    f.write(xor_crypt(descarga, "B"))
                    f.close()
    ##
        self.filename = self.manga_title + " - " + self.manga_numcap
        if self.overwrite and os.path.isdir(self.filename):
            os.chdir(self.filename)
            return True
        elif not os.path.isdir(self.filename):
            os.mkdir(self.filename)
            os.chdir(self.filename)
            return True
        else:
            return False

    def manga_url(self, url):
        if not url.replace(" ","") == "":
            
            if re.search(r"^(https://)",url):
                url = url.replace("https://","http://")
            elif re.search(r"^(http://)",url):pass
            else:
                url = "http://"+url
            self.url = url.replace(" ","")

    def download(self,url=""):
        if url == "":
            url = self.url
        else:
            url = url
        try:
                with open('cookies.txt'): pass
        except (OSError, IOError):
                cookies = LWPCookieJar('cookies.txt')
                cookies.save()      
        cookies = self.scraper
        cookies.cookies = LWPCookieJar('cookies.txt')
        cookies.cookies.load()
        html = self.scraper.get(url).content
        cookies.cookies.save()
        return html

    def login(self, username, password):
        try:
            with open('cookies.txt'): pass
        except IOError:
            cookies = LWPCookieJar('cookies.txt')
            cookies.save()
        url = 'https://www.crunchyroll.com/login'
        cookies = self.scraper
        cookies.cookies = LWPCookieJar('cookies.txt')
        page = self.scraper.get(url).content
        page = BeautifulSoup(page)
        hidden = page.findAll("input",{"type":"hidden"})
        hidden = hidden[1].get("value")
        logindata = {'formname' : 'login_form', 'fail_url' : 'http://www.crunchyroll.com/login', 'login_form[name]' : username, 'login_form[password]' : password, 'login_form[_token]': hidden, 'login_form[redirect_url]': '/'}
        req = self.scraper.post(url, data = logindata)
        url = "http://www.crunchyroll.com"
        html = self.scraper.get(url).content
        if re.search(username+ '(?i)', html):
                print("You have been successfully logged in.\n\n")
                cookies.cookies.save()
        else:
                print("Failed to verify your username and/or password. Please try again.\n\n")
                cookies.cookies.save()

    def CrunchyManga(self):
        cc = 1
        regex = r"\[{1} *(\d+(?:\.\d{1,2})?(?: *\- *\d+(?:\.\d{1,2})?)?)(\ *,{1} *(\d+(?:\.\d{1,2})?(?: *\- *\d+(?:\.\d{1,2})?)?))* *\]{1}$"
        chapters_ = re.search(regex,self.url)
        ch_dwn = None
        if chapters_:
            url = self.url.split ("[")
            ch_dwn = url[1]
            self.url = url[0]            
        print("Analyzing link %s..."%self.url)
        if re.match(r"^(http:\/\/)(w{3}\.)?(crunchyroll\.com\/comics_read(\/(manga|comipo|artistalley))?\?(volume\_id|series\_id)\=[0-9]+&chapter\_num\=[0-9]+(\.[0-9])?)",self.url): #Crunchyroll por episodios.
            try:
                html= self.download()
                soup = BeautifulSoup(html)
                self.manga_title = soup.find("span", {"itemprop": "title"}).text
                self.manga_title = self.manga_title.replace(':', ' ')
                manga = soup.find("object",{"id":"showmedia_videoplayer_object"}).find("embed",{"type":"application/x-shockwave-flash"}).get("flashvars")
                manga = manga.split("=")
                n = len(manga)-2
                serie_id = manga[1][:manga[1].find('&chapterNumber')]
                numero_cap = manga[2][:manga[2].find('&server')]
                if re.match(r"([0-9]+)(\.[0-9]{1,2})",numero_cap):
                    ch = re.match(r"([0-9]+)(\.[0-9]{1,2})",numero_cap)
                    ch = ch.groups()
                    if ch[1].__len__() == 2:
                        numero_cap = numero_cap + "0"
                    x = numero_cap[-2:]
                    if x == "00":
                        self.manga_numcap = numero_cap[:-3]
                    else:
                        self.manga_numcap = numero_cap[:-1]
                else:
                    self.manga_numcap = numero_cap
                section_id = manga[n][:manga[n].find('&config_url')]
            except Exception as e:
                print("The link is certainly from Crunchyroll, but it seems that it's not correct. Verify it and try again.")
                return
            cr_auth = "http://api-manga.crunchyroll.com/cr_authenticate?auth=&session_id="+section_id+"&version=0&format=json"
            html = self.download(cr_auth)
            try:
                soup = json.loads(html)
                cr_auth=""
                for item in soup["data"]["auth"]:
                    cr_auth=cr_auth+item            
            except:
                cr_auth = "null"            
            url_serie = "http://api-manga.crunchyroll.com/chapters?series_id="+serie_id
            html= self.download(url_serie)
            soup = json.loads(html)
            chapter_id = ""
            for item in soup["chapters"]:
                if item["number"] == str(numero_cap):
                    chapter_id = item["chapter_id"]
            if chapter_id == "":
                print("\nThe chapter {chapter} is not currently unavailable, try again later.\n".format(chapter=self.manga_numcap))
                return
            else:
                chapter_url = "http://api-manga.crunchyroll.com/list_chapter?session_id="+section_id+"&chapter_id="+chapter_id+"&auth="+cr_auth
                try:
                    html= self.download(chapter_url)
                    soup = json.loads(html)
                    c=0
                    pages = {}
                    for item in soup["pages"]:
                        try:
                            pages[c] = item["locale"].pop("enUS").pop("encrypted_composed_image_url")
                        except:      
                            pages[c] = item["image_url"]
                        c=c+1
                except Exception as e:
                    print("\n\nYou have to be premium user in order to download this chapter.")
                    return
                print("\nDownloading {title} - {num}...".format(title=self.manga_title, num=self.manga_numcap))
                x = self.folder()
                if not x:
                    print("The folder {title} - {num} already exists and overwrite folders is deactivated.".format(title=self.manga_title, num=self.manga_numcap))
                    os.chdir(self.folder)
                else:              
                    descarga = self.download_pages(pages)
                    os.chdir(self.folder)
                    if self.zip and descarga == 1:
                        self.zip_manga()
        elif re.match(r"^(http:\/\/)(w{3}\.)?(crunchyroll\.com\/comics_read)(\/(manga|comipo|artistalley))?(\?volume\_id\=[0-9]+)$",self.url): #Crunchyroll por volumenes
            volume = re.match(r"^(http:\/\/)(w{3}\.)?(crunchyroll\.com\/comics_read)(\/(?:manga|comipo|artistalley))?(\?volume\_id\=([0-9]+))$",self.url) 
            try:
                html= self.download()
                soup = BeautifulSoup(html)
                manga = soup.find("object",{"id":"showmedia_videoplayer_object"}).find("embed",{"type":"application/x-shockwave-flash"}).get("flashvars")
                manga = manga.split("=")
                n = len(manga)-2
                serie_id = manga[1][:manga[1].find('&chapterNumber')]
                section_id = manga[n]
            except:
                print("The link is certainly from Crunchyroll, but it seems that it's not correct. Verify it and try again.")
                return
            url_serie = "http://api-manga.crunchyroll.com/chapters?series_id="+serie_id
            html= self.download(url_serie)
            soup = json.loads(html)
            self.manga_title = soup["series"].pop("locale").pop("enUS").pop("name")
            chapter = []
            chapter_id = []
            volume = volume.groups()
            volume = volume[5]
            for item in soup["chapters"]:
                if item.pop("volume_id") == volume:
                    chapter_id.append(item.pop("chapter_id")) 
                    chapter.append(item.pop("number"))
                    self.manga_vol = item.pop("volume_number")
            cr_auth = "http://api-manga.crunchyroll.com/cr_authenticate?auth=&session_id="+section_id+"&version=0&format=json"
            html = self.download(cr_auth)
            try:
                soup = json.loads(html)
                cr_auth=""
                for item in soup["data"]["auth"]:
                    cr_auth=cr_auth+item
            except:
                print("To download volumes you need a premium account. Standard accounts can only download the latest chapter.")
                return
            c = 0
            cv = True
            rr = 0
            if self.manga_vol == "0":
                print("Downloading individual chapters")
            while c < len(chapter):
                x = chapter[c][-2:]
                if x == "00":
                    chapter[c] = chapter[c][:-3]
                else:
                    chapter[c] = chapter[c][:-1]
                self.manga_numcap = chapter[c]
                if self.manga_vol == "0":
                    print("\n%s: Chapters %d/%d"%(self.manga_title, c + 1, len(chapter)))
                    print("\nDownloading %s - %s"%(self.manga_title, self.manga_numcap))
                else:
                    print("\n%s Vol.%s: Chapters %d/%d"%(self.manga_title, self.manga_vol, c + 1, len(chapter)))
                    print("\nDownloading %s Vol.%s ch.%s"%(self.manga_title, self.manga_vol, self.manga_numcap))
                chapter_url = "http://api-manga.crunchyroll.com/list_chapter?session_id="+section_id+"&chapter_id="+chapter_id[c]+"&auth="+cr_auth
                html= self.download(chapter_url)
                soup = json.loads(html)
                c2=0
                pages = {}
                manga_cover = ""
                if cv == True:
                    if not self.manga_vol == "0":
                        manga_cover = soup["volume"].pop("encrypted_image_url")
                    cv = False
                for item in soup["pages"]:
                    try:
                        pages[c2] = item["locale"].pop("enUS").pop("encrypted_composed_image_url")
                    except:      
                        pages[c2] = item["image_url"]
                    c2=c2+1
                x = self.manga_folder(manga_cover)
                if not x:
                    print("The folder %s - %s already exists and overwrite folders is deactivated."%(self.manga_title, self.manga_numcap))
                    os.chdir(self.folder)
                else:
                    descarga = self.download_pages(pages)
                    if self.manga_vol == "0" and self.zip and descarga == 1:
                        self.zip_manga()
                    os.chdir(self.folder)
                    rr +=1
                c = c+1
            if self.zip and self.manga_vol != "0" and rr > 0:
                self.zip_manga()
        elif re.match(r"^(http:\/\/)(w{3}\.)?(crunchyroll\.com\/comics\/(manga|comipo|artistalley)\/[a-z0-9\-]+\/)(volumes)$",self.url): #Crunchyroll por serie entera
            html= self.download(self.url)
            soup = BeautifulSoup(html)
            serie_id = soup.find("span",{"id":"sharing_add_queue_button"}).get("group_id")
            if ch_dwn is not None:
                temp = self.d_volumes
                self.d_volumes = False
                ch_dwn = ((ch_dwn.replace(" ","")).replace("]","")).split(",")
            if self.d_volumes:
                i = 0
                vol_id = []
                try:
                    if soup.find("li",{r"class":"queue-item volume-simul"}).get("volume_id"):
                        volumen_id = soup.findAll("li",{r"class":re.compile("queue-item volume-")})
                        while i < len(volumen_id):
                            if i == len(volumen_id)-1:
                                vol_id.append(volumen_id[0].get("volume_id"))
                            else:
                                vol_id.append(volumen_id[i+1].get("volume_id"))
                            i+=1
                except:
                    volumen_id = soup.findAll("li",{r"class":re.compile("queue-item volume-")})
                    for vols in volumen_id:
                        vol_id.append(vols.get("volume_id") )
                i=0
                for vols in vol_id:
                    print("Downloading all volumes and individual chapters available. Volumes: %d/%d"%(i+1,len(vol_id)))
                    self.url = "http://www.crunchyroll.com/comics_read/manga?volume_id="+vols
                    self.CrunchyManga()
                    i+=1
            else:       
                volumen_id = soup.find("li",{r"class":re.compile("queue-item volume-")}).get("volume_id")
                url_vol = "http://www.crunchyroll.com/comics_read/manga?volume_id="+volumen_id
                html= self.download(url_vol)
                soup = BeautifulSoup(html)
                section_id = soup.find("object",{"id":"showmedia_videoplayer_object"}).find("embed",{"type":"application/x-shockwave-flash"}).get("flashvars")
                section_id = section_id.split("=")
                n = len(section_id)-2
                section_id = section_id[n]
                url_serie = "http://api-manga.crunchyroll.com/chapters?series_id="+serie_id
                html= self.download(url_serie)
                soup = json.loads(html)
                self.manga_title = soup["series"].pop("locale").pop("enUS").pop("name")
                chapter = []
                chapter_id = []
                for item in soup["chapters"]:
                    chapter_id.append(item.pop("chapter_id"))
                    chapter.append(item.pop("number"))
                
                if ch_dwn is not None:
                    ch = []
                    ch_id = []
                    
                    for i in ch_dwn:
                        c = 0
                        if re.search("-",i):
                            x = i.split("-")
                            x1 = x[0]
                            x2 = x[1]
                            if float(x1) > float(x2):
                                x1 = x[1]
                                x2 = x[0]
                            for i2 in chapter:
                                if float(i2) >= float(x1) and float(i2) <= float(x2):
                                    ch.append (i2)
                                    ch_id.append(chapter_id[c])
                                c+=1
                        else:
                            for i2 in chapter:
                                if float(i) == float(i2):
                                    ch.append (i2)
                                    ch_id.append(chapter_id[c])
                                c+=1
                        
                    chapter = ch
                    chapter_id = ch_id
                cr_auth = "http://api-manga.crunchyroll.com/cr_authenticate?auth=&session_id="+section_id+"&version=0&format=json"
                html = self.download(cr_auth)
                try:
                    soup = json.loads(html)
                    cr_auth=""
                    for item in soup["data"]["auth"]:
                        cr_auth=cr_auth+item
                except:
                    print("To download complete series you need a premium account. Standard accounts can only download the latest chapter.")
                    return
                c = 0
                while c < len(chapter):
                    x = chapter[c][-2:]
                    if x == "00":
                        chapter[c] = chapter[c][:-3]
                    else:
                        chapter[c] = chapter[c][:-1]
                    self.manga_numcap = chapter[c]
                    print("\n\n%s chapters %d of %d: Downloading chapter %s"%(self.manga_title, c + 1, len(chapter), self.manga_numcap))
                    chapter_url = "http://api-manga.crunchyroll.com/list_chapter?session_id="+section_id+"&chapter_id="+chapter_id[c]+"&auth="+cr_auth
                    html= self.download(chapter_url)
                    soup = json.loads(html)
                    c2=0
                    pages = {}
                    for item in soup["pages"]:
                        try:
                            pages[c2] = item["locale"].pop("enUS").pop("encrypted_composed_image_url")
                        except:      
                            pages[c2] = item["image_url"]
                        c2=c2+1
                    x = self.folder()
                    cc = 1
                    if not x:
                        print("\nThe folder %s - %s already exists and overwrite folders is deactivated."%(self.manga_title, self.manga_numcap))
                    else:
                        descarga = self.download_pages(pages)
                        cc +=1
                    os.chdir(self.folder)
                    if self.zip and cc > 1 and descarga == 1:
                        self.zip_manga()
                    c = c+1
                if temp:
                    self.d_volumes = True
        else:
            print("ERROR: The link is not from Crunchyroll/Manga")
        os.chdir(self.folder)
    
    def MassDownload(self):
        c = 1
        try:
            with open('links.txt'): pass
        except (OSError, IOError):
            links_file = open('links.txt','w')
            links_file.close()
            print("The file \"links.txt\" has been created. Please edit it with your links(One per line).")
            return

        links_file = open('links.txt','r')
        all_links = links_file.readlines()

        n_len = len(all_links)

        if n_len > 0:
            for link in all_links:
                print(" *** Loading link {cur}/{tot}".format(cur=c, tot=n_len))
                link = link.strip("\n")
                link = link.strip()
                print("---> {url}".format(url=link))
                #self.manga_url(link)
                #self.CrunchyManga()
                c = c + 1

        else:
            print("The file \"links.txt\" is empty. Please edit it with your links(One per line).")


    def AllMangas(self):
        html = self.download("http://www.crunchyroll.com/comics/manga/alpha?group=all")
        soup = BeautifulSoup(html, "html.parser")
        series = soup.findAll("ul",{"class":"clearfix medium-margin-bottom"})

        manga_list = []

        for item in series:
            serie2 = item.findAll("li")
            for item2 in serie2:
                name = item2.find("a").text
                name = name.strip("\n")
                name = name.strip()
                url = "http://www.crunchyroll.com" + item2.find("a").get("href")
                manga_list.append({'name':name, 'url':url})

        current = 1
        manga_count = len(manga_list)

        print(manga_list)

        for manga in manga_list:
            print(" *** Downloading all mangas from crunchyroll {cur}/{tot}\n---> {name}".format(cur=current, tot=manga_count, name=manga['name'], url=manga['url']))
            #self.manga_url(manga['url'])
            #self.CrunchyManga()
            current += 1


MangaDL = MangaDownloader()

def download(mangadl, url):
    mangadl.manga_url(arg.url)
    mangadl.CrunchyManga()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-u","--url", type=str, help="Crunchyroll Link. if you get an error, try using double quotation marks (\")")
    parser.add_argument("-l","--login", nargs=2, help="Crunchyroll login: -l User password. if your password has a blank, use double quotation marks (\"). Example: \"This is a password.\"")
    arg = parser.parse_args()

    if arg.login:
        username = arg.login[0]
        password = arg.login[1]
        MangaDL.login(username, password)

    if arg.url:
        download(MangaDL, arg.url)

    else:
        while True:
            selection = 0
            print("\nOptions:")
            print("1.- Download\n2.- Mass Download\n3.- Login \n"
                  "4.- Download ALL MANGAS from CrunchyRoll \n5.- About \n9.- Exit")
            try:
                selection = int(input("> "))

            except:
                print("ERROR: Invalid selection.")

            else:
                if selection == 1:
                    download(MangaDL, input("Link: "))

                elif selection == 2 :
                    MangaDL.MassDownload()

                elif selection == 3:
                    username = input("User: ")
                    password = getpass()
                    MangaDL.login(username, password)

                elif selection == 4:
                    MangaDL.AllMangas()

                elif selection == 5:
                    print(about)

                elif selection == 9:
                    exit(0)

                else:
                    print("ERROR: Invalid selection.")

