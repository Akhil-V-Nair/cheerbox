import requests

url = "https://api.subdl.com/api/v1/subtitles?imdb_id=tt0816692&languages=en"

resp = requests.get(url, headers={"Accept": "application/json"})
print(resp.status_code)
print(resp.text[:500])
