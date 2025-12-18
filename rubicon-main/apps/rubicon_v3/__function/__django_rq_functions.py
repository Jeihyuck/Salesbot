from alpha import __log
from django.core.cache import cache
from apps.rubicon_v3.models import Web_Cache


def insert_to_web_cache(query, country_code, title, url, content):
    """
    웹 캐시에 데이터를 삽입합니다.

    Args:
        query (str): query
        url (str): URL
        content (str): 콘텐츠
    """
    # Remove url if the url already exists in the database.
    # Since url column is not a PK.
    __log.debug(f"Deleting data from web cache if {url} exists...")
    Web_Cache.objects.filter(url=url).delete()

    __log.debug(f"Inserting data to web cache for query: {query}")
    Web_Cache.objects.create(
        query=query,
        country_code=country_code,
        title=title,
        url=url,
        content=content,
    )
