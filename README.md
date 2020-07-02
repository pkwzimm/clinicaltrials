# clinicaltrials
Selenium-based web scraper to fetch clinical trial records from clinicaltrials.gov.  Can either have date arguments or default to previous 31 days.

# Usage instructions
usage1 (default dates): python clinicaltrials.py
usage2 (custom dates): python clinicaltrials.py {startdate} {enddate}
usage note: dates must be in YYYY-MM-DD format

# Setup
1. Install Python3
2. Install [Chromium](https://www.chromium.org/developers/how-tos/get-the-code) (and pay attention to the version number) 
3. Install [Chromedriver](https://chromedriver.chromium.org/downloads) (make sure the version matches the version of chrome/chromium you downloaded, or this will not work)
4. Build a virtual environment for the scraper, installing:
   * Python3
   * Selenium
   * Pandas
   * Dateutil
5. Create a throwaway gmail account (called something like "YOURDEV@gmail.com")
6. [Enable "Less Secure Apps"](https://support.google.com/accounts/answer/6010255?hl=en) on that gmail account so that you can use an EC2 machine (or your local) to send emails.
7. Decide if you're going to set up an EC2 server (Any of the ubuntu distros should work, but I built this on Ubuntu 18, so that's the only one it's been tested on) or just run it local (go for it).
8. Go into the code and comment / uncomment the relevant lines (66 & 67) to set up the download location (whatever your chrome default is - your local machine probably sets it somewhere like "/Downloads", EC2 will download to whatever directory you're running the script from.
9. Replace YOUR_DEV_EMAIL_HERE, YOUR PASSWORD_HERE, RECIPIENT_EMAIL, and CC_RECIPIENT_EMAIL with the actual info you're going to use.

