from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import openai

# Set your OpenAI API key
apiKey=None
with open("api.txt","r") as apiFile:
    api_key=apiFile.read()
    openai.api_key = apiKey

def generate_ingredients(dish_name):
    # Create a prompt for the OpenAI API
    prompt = f"List only the ingredients needed to cook {dish_name}, without quantities or any additional information."

    try:
        # Call the OpenAI ChatCompletion API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Use the appropriate model
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,  # Limit tokens to focus on just ingredients
            temperature=0.5,  # Adjust as needed for creativity
        )

        # Extract and return the ingredients text from the response
        ingredients_text = response['choices'][0]['message']['content'].strip()
        return ingredients_text

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def askFood():
    dish_name = input("Enter the name of the dish: ")
    ingredients=generate_ingredients(dish_name)
    return ingredients

    


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def search_product(driver, product):
    url = f"https://www.amazon.com/s?k={product}"
    driver.get(url)
    
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 's-result-item')]"))
    )
    
    product_items = driver.find_elements(By.XPATH, "//div[contains(@class, 's-result-item')]")
    
    products = []
    for item in product_items:
        try:
            name = item.find_element(By.XPATH, ".//span[contains(@class, 'a-text-normal')]").text
            price_whole = item.find_element(By.XPATH, ".//span[@class='a-price-whole']").text
            price_fraction = item.find_element(By.XPATH, ".//span[@class='a-price-fraction']").text
            price = float(f"{price_whole}.{price_fraction}")
            
            img_element = item.find_element(By.XPATH, ".//img[@class='s-image']")
            img_url = img_element.get_attribute('src')
            
            link_element = item.find_element(By.XPATH, ".//a[@class='a-link-normal s-no-outline']")
            product_link = link_element.get_attribute('href')
            
            products.append({"name": name, "price": price, "image_url": img_url, "product_link": product_link})
        except:
            continue
    
    return sorted(products, key=lambda x: x['price'])[:5]  # Return top 5 cheapest products

def main():
    driver = setup_driver()
    
    # Get input from user
    response = askFood()
    if askFood:
        products=response.split(", ")
        try:
            cost=0
            for product in products:
                results = search_product(driver, product)
                
                if results:
                    # Prepare data for output
                    output_data = {
                        "search_term": product,
                        "cheapest_product": results[0],
                        "top_5_cheapest_products": results
                    }
                    
                    # Write to a JSON file
                    filename = f"{product}_prices.json"
                    with open(filename, "w", encoding="utf-8") as file:
                        json.dump(output_data, file, indent=2)
                    
                    print(f"Data for '{product}' has been written to {filename}")
                    
                    # Print the cheapest product to console
                    cheapest = results[0]
                    price=float(f"{cheapest['price']}")
                    cost+=price
                    print(f"\nCheapest product for '{product}':")
                    print(f"Name: {cheapest['name']}")
                    print(f"Price: ${price}")
                    print(f"Product Link: {cheapest['product_link']}")
                    print(f"Image URL: {cheapest['image_url']}")
                else:
                    print(f"No results found for '{product}'")
            print(f"Total Cost: ${cost}")
        
        except Exception as e:
            print(f"An error occurred: {e}")
        
        finally:
            driver.quit()

if __name__ == "__main__":
    main()