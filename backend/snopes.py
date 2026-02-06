import feedparser

feed = feedparser.parse("https://www.snopes.com/feed/")
for entry in feed.entries[:5]:
    print(entry.title)
    print(entry.link)
    print(entry.published)
    print()
