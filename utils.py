import requests


def scrape_uk_sanctions(url):
    filename = url.split("/")[-1]
    sl = requests.get(url, stream=True)
    f = open(filename, "wb")
    for chunk in sl.iter_content(chunk_size=1024):
        if chunk:
            f.write(chunk)
    f.close()
    return
