#selenium-based web scraper to fetch clinical trial records.  Can either have date arguments or default to previous 31 days.
#usage1 (default dates): python clinicaltrials.py
#usage2 (custom dates): python clinicaltrials.py {startdate} {enddate}
#usage note: dates must be in YYYY-MM-DD format

from selenium import webdriver
from selenium.webdriver.common.keys import Keys #to be able to input data in search fields
from selenium.webdriver.chrome.options import Options #options (for running headless)
import re
import datetime as DT
from datetime import datetime
import pandas as pd
from pandas import DataFrame
from selenium.webdriver.common.keys import Keys #to be able to input data in search fields
from selenium.webdriver.support.ui import Select #to handle dropdowns
import os
import time
import csv
import sys
import email, smtplib, ssl #for emailing results
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from dateutil.relativedelta import relativedelta

# instantiate a chrome options object so you can set the size and headless preference
chrome_options = Options()
chrome_options.add_argument("--headless") #FOR DEBUG COMMENT OUT SO YOU CAN SEE WHAT YOU'RE DOING
browser = webdriver.Chrome(chrome_options=chrome_options) #open up your browser (Ubuntu version, with headless flags)

#conditional loop for sysarg dates
if len(sys.argv) > 1: #system arguments exist
    startdate = datetime.strptime(sys.argv[1], '%Y-%m-%d')
    enddate = datetime.strptime(sys.argv[2], '%Y-%m-%d')
    print('startdate =' + str(startdate.month) + '-'+ str(startdate.day) + '-' + str(startdate.year))
    print('enddate =' + str(enddate.month) + '-'+ str(enddate.day) + '-' + str(enddate.year))
else:
    #get yesterday's date (use yesterday instead of today because today isn't done yet.  This also helps account for some time zone errors.
    today = DT.date.today()
    enddate = today - DT.timedelta(days=1)
    startdate = today - relativedelta(months=1)

#build the URL with dates input correctly.  If you want a narrower search, run a manual advanced search on clinicaltrials.gov and replace the first URL string with the relevant tags (such as not currently recruiting = "&recrs=b"
url = 'https://clinicaltrials.gov/ct2/results?cond=&term=&type=&rslt=&age_v=&gndr=&intr=&titles=&outc=&spons=&lead=&id=&cntry=US&state=&city=&dist=&locn=&rsub=&strd_s=&strd_e=&prcd_s=&prcd_e=&sfpd_s=' + str(startdate.month) + '%2F' + str(startdate.day) + '%2F' + str(startdate.year) + '&sfpd_e=' + str(enddate.month) + '%2F' + str(enddate.day) + '%2F' + str(enddate.year) + '&rfpd_s=&rfpd_e=&lupd_s=&lupd_e=&sort='

#navigate to the page and get search results as a csv
browser.get(url) #fetch url
print("Navigating to URL...")
dl_link = browser.find_element_by_id("save-list-link")
dl_link.click()
studies = Select(browser.find_element_by_id("number-of-studies"))
studies.select_by_value('10000')
dl_fields = Select(browser.find_element_by_id("which-fields"))
dl_fields.select_by_value('all')
dl_format = Select(browser.find_element_by_id("which-format"))
dl_format.select_by_value('csv')
dl_button = browser.find_element_by_id("submit-download-list")
dl_button.click()
print("Downloading list of clinical trials...")

#wait 10s for download
time.sleep(10)

#load CSV into pandas dataframe
#dl_filename = '/home/USERNAME/Downloads/SearchResults.csv' #LOCAL VERSION
dl_filename = 'SearchResults.csv'  #EC2 VERSION
df = pd.read_csv(dl_filename)
df = df[['NCT Number','Title','Status','Start Date','Completion Date','First Posted','Sponsor/Collaborators','URL']]
url_list = df['URL'].tolist()

print("Test load into dataframe...")
print(df.head(2)) #debugging to test if df is loaded correctly.

contact_names = []
email_list = []
contact_firstnames = []
firstemails = []

#iterate over all the URLS in URL list to pull details
for u in url_list:
    u_search = u.replace('show','ct2/show/record') #show tabular view
    browser.get(u_search)  # fetch url
    print("Collecting contacts from " + str(u_search))
    contacts = browser.find_elements_by_xpath("//a[@id='contacts']/following-sibling::table/tbody/tr/td[1]")
    contact_names_item = []
    contact_firstnames_item = []
    email_item = []
    for contact in contacts:
        contact_big = contact.text
        contact_big = contact_big.replace('Contact: ','')
        contact_firstname_raw = re.search('^.*?(?=\s)', contact_big)
        contact_names_item.append(contact_big)
        contact_firstnames_item.append(contact_firstname_raw[0])
    contact_names.append(str(contact_names_item).strip('[]'))
    contact_firstnames.append(str(contact_firstnames_item).strip('[]'))
    emails = browser.find_elements_by_xpath("//a[@id='contacts']/following-sibling::table/tbody/tr/td/a[starts-with(@href, 'mailto')]")
    for email in emails:
        email_raw = email.text
        email_raw = email_raw.replace("'", "")
        email_item.append(email_raw)
    email_list.append(str(email_item).strip('[]'))
    try:
        firstemail = emails[0].text
    except IndexError:
        firstemail = ""
    firstemails.append(firstemail)

#convert the lists into pandas dataframes
print("Loading contacts into dataframe...")
url_list_df = DataFrame(url_list,columns=['URL'])
contact_names_df = DataFrame(contact_names,columns=['Contact Names'])
contact_firstnames_df = DataFrame(contact_firstnames,columns=['Contact First Names'])
email_list_df = DataFrame(email_list,columns=['Emails'])
firstemails_df = DataFrame(firstemails,columns=['First Email'])

#merge the dataframes using index keys
details_df = url_list_df.merge(contact_names_df,how='inner', left_index=True, right_index=True)
details_df = details_df.merge(contact_firstnames_df,how='inner', left_index=True, right_index=True)
details_df = details_df.merge(email_list_df,how='inner', left_index=True, right_index=True)
details_df = details_df.merge(firstemails_df,how='inner', left_index=True, right_index=True)

#merge the original dataframe with the new one
df = df.merge(details_df,how='inner', left_on=['URL'], right_on=['URL'])
print("Merging dataframes...")

#output to csv file
csv_filename = 'ctgov_' + str(startdate.month) + '-'+ str(startdate.day) + '-' + str(startdate.year) + '_to_' + str(enddate.month) + '-'+ str(enddate.day) + '-' + str(enddate.year) + '.csv'
df.to_csv(csv_filename, index = False,quotechar='"',quoting=csv.QUOTE_ALL)
print("Exporting csv...")

#email results
subject = "Clinicaltrials.gov scrape: " + str(startdate.month) + '-'+ str(startdate.day) + '-' + str(startdate.year) + ' to ' + str(enddate.month) + '-'+ str(enddate.day) + '-' + str(enddate.year)
sender_email = "YOUR_DEV_EMAIL_HERE"
receiver_email = "RECIPIENT_EMAIL"
cc = "CC_RECIPIENT_EMAIL"  #comment out for testing so other people don't get spammed
body = 'Here is the latest clinicaltrials.gov scrape for trials listed as Not Yet Recruiting'

# Create a multipart message and set headers
message = MIMEMultipart()
message["From"] = sender_email
message["To"] = receiver_email
message["Subject"] = subject
message["CC"] = cc

message.attach(MIMEText(body))
attachment = MIMEBase('application', "octet-stream")
attachment.set_payload(open(csv_filename, "rb").read())
encoders.encode_base64(attachment)
attachment.add_header('Content-Disposition', 'attachment; filename="' + str(csv_filename) + '"')
message.attach(attachment)

print("Attaching csv and emailing results...")

# Log in to server using secure context and send email
context = ssl.create_default_context()
with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
    server.login(sender_email, "YOUR_PASSWORD_HERE") #yes, I know raw passwords are a bad idea.  This is a throwaway one only used for this purpose.
    text = message.as_string()
    server.sendmail(sender_email, [receiver_email, cc], text)
    server.quit()

#cleanup
os.remove(dl_filename)
browser.close() #close the browser else you'll have a browser window open for every single station in the loop
ps = 'sudo pkill -9 chrome' #set up command for killing chrome leftovers
os.system(ps) #kill chrome leftovers
print("Cleanup...")
