# ### packages

#webdriver
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

#others
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time


from google.cloud import translate_v2 as translate
import os

# # 

# ### get selenium




#open up chrome webdriver
driver = webdriver.Chrome(ChromeDriverManager().install())
driver.get('http://web.whatsapp.com')
driver.maximize_window()


#wait until the user scan the QR code and the new chat appears
timeout = 100
element_present = EC.presence_of_element_located((By.XPATH, '//div[@title="New chat"]'))
WebDriverWait(driver, timeout).until(element_present)
driver.find_element_by_xpath('//div[@title="New chat"]').click()


# # 

# ### find recent contacts




response_content = driver.page_source
soup = BeautifulSoup(response_content, 'lxml')

#recent contacts xml
rcontacts_xml = soup.find('div', id='pane-side')

#create a list of these contacts
random_class = rcontacts_xml.find('span', dir='auto').get('class')[0]
rcontacts_xml = rcontacts_xml.find_all('span', dir='auto', class_=random_class)
rcontacts_list = [rcontact_xml.get('title') for rcontact_xml in rcontacts_xml]


# # 

# # collect contacts




contacts_dict = {}
contacts_list = []
contacts_length = 0
dummy_length = 1

while contacts_length != dummy_length:
    
    dummy_length = len(contacts_list)
    response_content = driver.page_source
    soup = BeautifulSoup(response_content, 'lxml')
    contacts_xml = soup.find_all('span', dir='auto', class_=random_class)
    
    for contact_xml in contacts_xml:
        contact = contact_xml.get('title') 
        if contact is not None and contact not in rcontacts_list and contact not in contacts_dict.keys():
            contacts_dict[contact] = {'contact': contact}
            contacts_list.append(contact)
            
    contacts_list.sort()
    contacts_length = len(contacts_list)
    
    last_contact = contacts_list[-3]
    xpath = '//span[@title="' +  last_contact + '"]'
    element = driver.find_elements_by_xpath(xpath)
    driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'start' });", element[0])
    time.sleep(1)

driver.find_element_by_xpath('//span[@data-testid="back"]').click()


# # 

# # first name




#first names dictionary to include gender, translated name, frequency, and other features if needed
first_names = {}
for contact in contacts_dict.keys():
    frequency = 1
    
    #add first name to the first names dictionary
    first_name = contacts_dict[contact]['contact'].split()[0]
    if first_name in first_names.keys():
        frequency = first_names[first_name]['frequency'] 
        frequency = frequency + 1
    first_names[first_name] = {'frequency': frequency}
    
    
    #add the first name to the orignal contacts dictionary
    contacts_dict[contact]['first_name'] = first_name


# # 

# ### translate first_names






#PATH TO GOOGLE TRANSLATOR CREDS. 
#SEE https://www.youtube.com/watch?v=YapTts_An9A&ab_channel=JieJenn
path_to_creds = r"ADD GOOGLE API CREDS FILE JSON format"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = path_to_creds

def translate_name(name):
    translate_client = translate.Client()
    target = 'ar'
    result = translate_client.translate(
        name,
        source_language = 'en',
        target_language='ar')
    
    translated_name = result['translatedText']
    translated_name = translated_name.strip().replace("عبد ", "عبد")
    return translated_name


# # 

# ### translate names




counter = 0
for name in first_names.keys():
    time.sleep(1)
    counter = counter + 1

    #if the first name is English, it will translate it
    isArabic = re.match(r'[\u0600-\u06ff]+', name)
    
    #if the name is arabic
    if isArabic:
        name_translated = name
        
    #if the name is in englihs, translate it
    #if you don't have google api key, there are two options
        #first option is to get the key, it is for free
        #second option is to use the googletrans package instead of the google translation api
    else:
        name_translated = translate_name(name)
        
    first_names[name]['translated'] = name_translated


# # 

# ### gender classification




gender_names = pd.read_csv('names_gender.csv')
#sources are as follows
#1: https://github.com/Eslam2014/arabic_names_with_gender
#2: https://github.com/zakahmad/ArabicNameGenderFinder
#3: others

names = list(gender_names.name)
#search within the names genders file if you can find the name, get its corrosponding gender
for first_name in first_names.keys():
    translated_name = first_names[first_name]['translated']
    if translated_name in names:
        first_names[first_name]['gender']= gender_names[gender_names.name == translated_name]['gender'].values[0]

#remark: if a name is not in the list, there exist some free apis that can help!


# # 

# ### adding gender and translated first name to contacts dictionary




for contact in contacts_dict.keys():
    first_name = contacts_dict[contact]['first_name']
    contacts_dict[contact] = {**contacts_dict[contact], **first_names[first_name]}


# # 

# # contacts selections




#IN CASE YOU WANT TO SELECT SPECIFIC, SPECIFY THEM HERE
selected_contacts = contacts_dict


# # 

# # send messages


for contact in selected_contacts.keys():
    
    #NAVEGATE TO THE CHAT
    time.sleep(0.25)  
    #open a new chat
    driver.find_element_by_xpath('//div[@title="New chat"]').click()
    time.sleep(0.25)
    #search for the contact name
    driver.switch_to.active_element.send_keys(contact)
    time.sleep(0.25)
    #enter the chat
    driver.switch_to.active_element.send_keys(Keys.ENTER)
    #send the message
    time.sleep(0.25)
    message_box = driver.switch_to.active_element
    
    first_name_translated = selected_contacts[contact]['translated']
    gender = selected_contacts[contact]['gender']
    
    #IF GENDER IS NOT AVAILABLE
    if gender == 'Male':
        line1 = 'العزيز {},'.format(first_name_translated)
        line2 = "حبيت اهنئك بحلول عيد الفطر المبارك. كل عام وأنت بخير وعساكم من عواده 🎉🎊"
        line3 = "ماجد آل هليل"
        
    elif gender == 'Female':
        line1 = 'العزيزة {}'.format(first_name_translated)
        line2 = "حبيت اهنئك بحلول عيد الفطر المبارك. كل عام وأنتي بخير وعساكم من عواده 🎉🎊"
        line3 = "ماجد آل هليل"

    #FORMAT THE MESSAGE
    html_message = "<p>{}</p><p>{}</p><p></p><p>{}</p>".format(line1, line2, line3)
    
    #SEND THE MESSAGE
    driver.execute_script("arguments[0].innerHTML = '{}'".format(html_message),message_box)
    message_box.send_keys("." + Keys.BACKSPACE + Keys.ENTER)
    

