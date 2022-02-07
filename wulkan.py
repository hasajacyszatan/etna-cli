import requests
from os import system
from bs4 import BeautifulSoup as zupka
# from collections import defaultdict
from datetime import date
from math import floor, ceil
import re
class wulkanClient:
  def __init__(self, loginName, Password, powiat):
    self.powiat = powiat
    # dane logowania
    self.login = {
      'LoginName': loginName,
      'Password': Password
    }
    self.cookies = {
      'efebCookieReaded': '1',
      'biezacyRokSzkolny': '2021',
    }
    self.permissions = {}
    self.jsonHeaders = {'content-type': 'application/json'}
    # self.activate()
  def load(self, permissions, cookies, okresID):
    self.cookies = cookies
    self.permissions = permissions
    self.okresID = okresID
  def req(self, url, data = {}):
    return requests.post(url, cookies=self.cookies, headers=self.jsonHeaders, data=data)
  def activate(self):
    a_session = requests.Session()
    # Zwraca pliki cookie ASP.NET_SessionId, ARR_cufs.vulcan.net.pl, ARR_3S_ARR_CufsEOL, UonetPlus_SLACookie, ARR_3S_ARR_EFEB
    # nie wystarczą one do zalogowania się do dziennika ale są wymaga żeby zdobyć następne
    response = a_session.post('https://cufs.vulcan.net.pl/'+self.powiat+'/Account/LogOn?ReturnUrl=%2F'+self.powiat+'%2FFS%2FLS%3Fwa%3Dwsignin1.0%26wtrealm%3Dhttps%253a%252f%252fuonetplus.vulcan.net.pl%252f'+self.powiat+'%252fLoginEndpoint.aspx%26wctx%3Dhttps%253a%252f%252fuonetplus.vulcan.net.pl%252f'+self.powiat+'%252fLoginEndpoint.aspx', data=self.login, cookies=self.cookies)
    self.cookies.update(response.cookies.get_dict())

    # zwraca parametry requesta potrzebne do zalogowania 
    zupkaZDanych = zupka(response.text, 'html.parser')
    data = dict()
    for i in zupkaZDanych.find_all('input', {'type': 'hidden'}):
      data.update({i.get('name'): i.get('value')})
    
    # zwraca ARR_3S_ARR_EFEB, UonetPlus_SLACookie, NET_SessionId, Vulcan.CUFS.WebFrontEndCookie, FederatedApplication9991aa22
    # z użyciem tych plików mozna sie już zalogować z sukcesem do dziennika
    a_session.post('https://uonetplus.vulcan.net.pl/'+self.powiat+'/LoginEndpoint.aspx', cookies=self.cookies, data=data)
    self.cookies.update(a_session.cookies.get_dict())
    permissions = a_session.get('https://uonetplus.vulcan.net.pl/'+self.powiat+'/Start.mvc/Index', cookies=self.cookies, data=data).text
    for i in permissions.split('\n'):
      if " permissions: '" in i:
        permissions = i.replace("',", '').replace("       permissions: '","")
    self.permissions = {"permissions": permissions}
    # dodaje idBiezacyUczen i idBiezacy dziennik i inne esze mesze
    uczenData = requests.post('https://uonetplus-uczen.vulcan.net.pl/'+self.powiat+'/001003/UczenDziennik.mvc/Get', headers=self.jsonHeaders, cookies=self.cookies).json()["data"][0]
    uczenDict = {
      'idBiezacyUczen': str(uczenData['IdUczen']),
      'idBiezacyDziennik': str(uczenData['IdDziennik']),
      'idBiezacyDziennikPrzedszkole': str(uczenData['IdPrzedszkoleDziennik']),
      'idBiezacyDziennikWychowankowie': str(uczenData['IdWychowankowieDziennik'])
    }
    for i in uczenData['Okresy']:
      if i['IsLastOkres']:
        self.okresID = i['Id']
    self.cookies.update(uczenDict)
  # funkcje getSprawdziany oraz getPlanLekcji przyjmują argument data (klasa datetime.date) jeśli go nie ma odczytują najnowsze dane
  def getSprawdziany(self, data=None):
    try:
      data.day
    except:
      data = date.today()

    data = '{"data":"'+data.strftime("%Y-%m-%dT00:00:00")+'","rokSzkolny":'+data.strftime("%Y")+'}'
    return self.req('https://uonetplus-uczen.vulcan.net.pl/'+self.powiat+'/001003/Sprawdziany.mvc/Get', data=data).json()
  def getPlanLekcji(self, data=None):
    try:
      data.day
    except:
      data = date.today()
    data = '{"data":"'+data.strftime("%Y-%m-%dT00:00:00")+'","rokSzkolny":'+data.strftime("%Y")+'}'
    return self.req('https://uonetplus-uczen.vulcan.net.pl/'+self.powiat+'/001003/Sprawdziany.mvc/Get', data=data).json()

  def getPrzedmioty(self):
    return self.req('https://uonetplus-uczen.vulcan.net.pl/'+self.powiat+'/001003/LekcjeZrealizowane.mvc/GetPrzedmioty').json()
  
  def getOceny(self):
    data = '{"okres":'+str(self.okresID)+'}'
    return self.req('https://uonetplus-uczen.vulcan.net.pl/'+self.powiat+'/001003/Oceny.mvc/Get', data=data).json()
  
  def GetDaneUcznia(self):
    return self.req('https://uonetplus-uczen.vulcan.net.pl/'+self.powiat+'/001003/Uczen.mvc/Get').json()
  
  def GetUwagiIOsiagniecia(self):
    return self.req('https://uonetplus-uczen.vulcan.net.pl/'+self.powiat+'/001003/UwagiIOsiagniecia.mvc/Get').json()
  
  def getZebrania(self):
    return self.req('https://uonetplus-uczen.vulcan.net.pl/'+self.powiat+'/001003/Zebrania.mvc/Get').json()
  def getOgloszenia(self):
    return self.req('https://uonetplus.vulcan.net.pl/'+self.powiat+'/Start.mvc/GetStudentDirectorInformations', data=self.permissions).json()
  def getSzczesliwyNumerek(self):
    return self.req('https://uonetplus.vulcan.net.pl/'+self.powiat+'/Start.mvc/GetKidsLuckyNumbers', data=self.permissions).json()
  def getOstatnieOceny(self):
    return self.req('https://uonetplus.vulcan.net.pl/'+self.powiat+'/Start.mvc/GetLastNotes', data=self.permissions).json()
  def getProstyPlanLekcji(self):
    kidsLessonPlan = self.req('https://uonetplus.vulcan.net.pl/'+self.powiat+'/Start.mvc/GetKidsLessonPlan', data=self.permissions).json()
    lekcje = []
    lekcjefinalne = []
    for i in kidsLessonPlan['data'][0]['Zawartosc']:
      lekcje.append(re.search("</span> <span '>(.*)</span>", i['Nazwa']))
      if "Jutro".upper() in i['Nazwa'].upper():
        break
    for obj in lekcje:
        if not obj is None:
          # print(obj.group(0))
          lekcjefinalne.append(obj.group(0).replace("</span> <span '>", "").replace("</span>", ''))
          # .replace("</span> <span '>", "").replace("</span>", '')
    return lekcjefinalne
  def getWiadomosci(self, limit = 25,dataOd=date.today().replace(day=date.today().day-1), dataDo=date.today()):
    params = (
    # ('_dc', '1639584476943'),
    ('dataOd', dataOd.strftime("%Y-%m-%d 00:00:00")),
    ('dataDo', dataDo.strftime("%Y-%m-%d 00:00:00")),
    ('page', '1'),
    ('start', '0'),
    ('limit', limit),
    )
    response = requests.get('https://uonetplus-uzytkownik.vulcan.net.pl/'+self.powiat+'/Wiadomosc.mvc/GetInboxMessages', params=params, cookies=self.cookies).json()
    return response
  # Nie działa cholera wie czemu
  def getWiadomosc(self, messageId):
    data = {
        'messageId': messageId
    }
    cookies = {
        '_ga': 'GA1.3.1429533272.1639754919',
        '_gid': 'GA1.3.1614133155.1639754919',
    }
    headers = {
        'authority': 'uonetplus-uzytkownik.vulcan.net.pl',
        'sec-ch-ua': '"Microsoft Edge";v="95", "Chromium";v="95", ";Not A Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36 Edg/95.0.1020.30',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'x-v-requestverificationtoken': 'X0W8CksKf9ep8RDUjn5GDHBVQlmfMqqBdGO71jf4fdUiw0c2A3JGP9RCT39d3o4EZi3iFk-I1jLKtG7Yt1Vdl99-s4msUaoGKV9G0ff8XHtiX1Ni0',
        'x-requested-with': 'XMLHttpRequest',
        'x-v-appguid': '4a0f9ce595891b225574eac6049fd2b3',
        'sec-ch-ua-platform': '"Windows"',
        'accept': '*/*',
        'origin': 'https://uonetplus-uzytkownik.vulcan.net.pl',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://uonetplus-uzytkownik.vulcan.net.pl/'+self.powiat+'/',
        'accept-language': 'pl',
    }
    response = requests.post('https://uonetplus-uzytkownik.vulcan.net.pl/'+self.powiat+'/Wiadomosc.mvc/GetInboxMessageDetails', cookies=self.cookies.update(cookies), data=data, headers=headers)
    return response
  def getPrzedmiotyZrealizowane(self ,dataOd=date.today().replace(day=date.today().day-1), dataDo=date.today()):
    # data = '{"poczatek":"2021-12-17T17:13:58","koniec":"2022-01-16T17:13:58","idPrzedmiot":-1}'
    data = {
      'poczatek': dataOd.strftime("%Y-%m-%dT00:00:00"),
      'koniec': dataDo.strftime("%Y-%m-%dT00:00:00")
    }
    response = self.req('https://uonetplus-uczen.vulcan.net.pl/'+self.powiat+'/001003/LekcjeZrealizowane.mvc/GetZrealizowane', data=data)
    return response.json()
  def getSzkolaINauczyciele(self):
    response = self.req('https://uonetplus-uczen.vulcan.net.pl/'+self.powiat+'/001003/SzkolaINauczyciele.mvc/Get')
    return response
  def getListaOsob(self):
    if date.today().month > 6:
      wiadomosci = self.getWiadomosci(dataOd = date.today().replace(month = date.today().month - 4))
    else:
      wiadomosci = self.getWiadomosci(dataOd = date.today().replace(year = date.today().year - 1).replace(month = date.today().month+4))
    adresaci = []
    for i in wiadomosci['data']:
      if len(i['Adresaci']) > len(adresaci):
        adresaci = i["Adresaci"]
    return adresaci