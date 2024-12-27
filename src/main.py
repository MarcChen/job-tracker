from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.binary_location = '/usr/bin/chromium'

# Set up ChromeDriver service
service = Service('/usr/bin/chromedriver')
driver = webdriver.Chrome(service=service, options=chrome_options)

# URL to visit
url = 'https://mon-vie-via.businessfrance.fr/offres/recherche?query=&missionsTypesIds=1&gerographicZones=4'
driver.get(url)

# Extract the page source and parse with BeautifulSoup
soup = BeautifulSoup(driver.page_source, "lxml")

# Find and print all H1 and H2 elements
print("H1 Elements:")
for h1 in soup.find_all('h1'):
    print(h1.get_text(strip=True))

print("\nH2 Elements:")
for h2 in soup.find_all('h2'):
    print(h2.get_text(strip=True))

# Close the browser
driver.quit()
