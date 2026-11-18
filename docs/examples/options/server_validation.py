from imgproxykit import Client, Transform
from imgproxykit.options import Quality

client = Client('http://localhost:8080')
source_url = 'https://picsum.photos/id/237/1600/1200'

too_high = Transform(Quality(200))  # (1)!
url = client.url(source=source_url, transform=too_high)

print('Built locally:', url)
