import requests as req

robot_url = 'https://books.toscrape.com/robots.txt'


try:
    response = req.get(robot_url,timeout=5)
    response.raise_for_status()

    if(response.status_code == 404):
        print(f'Status Code: {response.status_code}')
    print(f'Content: {response.text}')

except req.exceptions.RequestException as e:
     print(f"An error occurred: {e}")



