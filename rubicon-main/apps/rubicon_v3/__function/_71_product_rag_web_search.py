# line 2 ~ 7 테스트 시 주석 해제
import sys

sys.path.append("/www/alpha/")
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import re
import json
import hashlib
import asyncio
import aiohttp
import httpx
import django_rq
import urllib
import requests
import pandas as pd
from django.db import connection
import inspect

from bs4 import BeautifulSoup
from markdownify import MarkdownConverter
from concurrent.futures import ThreadPoolExecutor
from django.core.cache import cache

from alpha import __log
from alpha.settings import GOOGLE_API_KEY, SEARCH_ENGINE_ID, VITE_OP_TYPE

from apps.rubicon_v3.__function import (
    _22_orchestrator_intelligence,
    __embedding_rerank as embedding_rerank,
)

from apps.rubicon_v3.models import Intelligence_V2, Web_Cache
from apps.rubicon_v3.__function.__utils import clean_chunk
from apps.rubicon_v3.__function._71_product_rag_web_search_filter import text_cleaner
from apps.rubicon_v3.__function import __django_rq_functions as rq_function
from apps.rubicon_v3.__function.definitions import intelligences, sub_intelligences
from apps.rubicon_v3.__function.__custom_content_scorer import two_stage_score
from apps.rubicon_v3.__function.__embedding_rerank import rerank_db_results
from apps.__common import multi_threading
from scrapy.http import HtmlResponse
import concurrent.futures
from apps.rubicon_v3.__function.__embedding_rerank import (
    baai_embedding,
    rerank_db_results,
)

google_search_mapping = {
    "KR": {
        "DOT.COM": "samsung.com/sec/",
        "SERVICE": "www.samsungsvc.co.kr/",  # TODO:'samsungsvc.co.kr'
        "NAVER_BLOG": "blog.naver.com",
        "TISTORY": "tistory.com",
    },
    "GB": {
        "DOT.COM": "samsung.com/uk/",
        "SERVICE": "samsung.com/uk/",
        "NAVER_BLOG": "samsung.com/uk/",
        "TISTORY": "samsung.com/uk/",
    },
}

# EXCLUDED_KEYWORDS = ["Apple", "Huawei", "Xiaomi", "\"SK Magic\"", "Lenovo", "BOSS", "캐리어", "화웨이", "샤오미", "레노버", "애플", "WD", "HDD"]
# EXCLUDED_KEYWORDS = ["Apple", "LG", "Huawei", "Xiaomi", "\"SK Magic\"", "Lenovo", "BOSS", "캐리어", "화웨이", "샤오미", "레노버", "애플", "엘지", "WD", "HDD"]
EXCLUDED_KEYWORDS = []


# @cache_page(60 * 15) # for 15 minutes
# async def get_content_from_web_cache(md5_hash):
#     cache = Web_Cache.objects.get(md5_hash=md5_hash)
#     return cache


def insert_into_db(
    keywords_query: str,
    query: str,
    query_type: str,
    country_code: str,
    result: dict,
) -> None:
    """
    If the module retrieved new web search data,
    insert new web cache data into rubicon_v3_web_cache table.
    Args:
        keywords_query: Google search keywords.
        query: User's original input query.
        query_type: Type of input query. top_query for example.
        country_code:
        result: Google search result from RubiconSpider class.

    """
    title = result.get("title", "")
    url = result.get("url", "")
    content = result.get("content", "")

    queue = django_rq.get_queue("high")

    if url == "" or content == "":
        return False

    if query_type == "top_query":
        queue.enqueue(
            rq_function.insert_to_web_cache,
            keywords_query,
            country_code,
            title,
            url,
            content,
        )
    else:
        queue.enqueue(
            rq_function.insert_to_web_cache, query, country_code, title, url, content
        )

    return True


class RemoveTagsConverter(MarkdownConverter):
    # 1) Remove image tags
    def convert_img(self, el, text, convert_as_inline=True):
        # Completely remove <img> tags
        return ""

    # 2) Remove script tags
    def convert_script(self, el, text, convert_as_inline=True):
        # Completely remove <script> tags
        return ""


def markdownify_remove_tags(html: str) -> str:
    """Convert HTML to Markdown while removing <img> and <script> tags"""
    return RemoveTagsConverter().convert(html)


#####


# Asynchronous function to fetch Google search results
async def get_google_search_result(
    date_restrict,
    session,
    query_type,
    keywords_query,
    query,
    country,
    sites=["samsung.com"],
):
    url = "https://www.googleapis.com/customsearch/v1"

    site_query = f"( site:{' OR site:'.join(sites)} )"

    if query_type == "top_query":
        query = keywords_query

    params = {
        "key": GOOGLE_API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "dateRestrict": date_restrict,
        "q": f"{site_query} {query}",
    }
    # excluded_keyword = [f"-{x}" for x in EXCLUDED_KEYWORDS]
    # excluded_keyword_query = " ".join(excluded_keyword)

    # if query_type == "top_query":
    #     if country == "KR":
    #         params["q"] = f"{keywords_query + ' 종류 라인업'} {site_query} {excluded_keyword_query}"
    #     else:
    #         params["q"] = f"{keywords_query + ' types lineup'} {site_query} {excluded_keyword_query}"
    # else:
    #     params["q"] = f"{query} {site_query} {excluded_keyword_query}"

    # __log.debug(params)
    # if session.get is async, await it
    if inspect.iscoroutinefunction(session.get):
        resp = await session.get(url, params=params)
        # some clients have .json() as coroutine
        if inspect.iscoroutinefunction(resp.json):
            data = await resp.json()
        else:
            data = resp.json()
    else:
        resp = session.get(url, params=params)
        data = resp.json()

    return data.get("items", [])


# Class for parsing asynchronous search results
class RubiconSpider:
    def __init__(self, urls=None, max_workers=5, timeout=10):
        self.urls = urls or []
        self.max_workers = max_workers
        self.timeout = timeout
        self.results = []

    async def scrape_all(self) -> list[dict]:
        """Async wrapper that runs scrape_single_url in threads."""
        sem = asyncio.Semaphore(self.max_workers)
        tasks = [
            asyncio.create_task(self._scrape_with_sem(sem, url)) for url in self.urls
        ]
        # Wait for all tasks; errors are caught below
        return await asyncio.gather(*tasks)

    async def _scrape_with_sem(self, sem: asyncio.Semaphore, url: str) -> dict:
        async with sem:
            try:
                # run blocking scrape in a ThreadPool
                return await asyncio.wait_for(
                    asyncio.to_thread(self.scrape_single_url, url), timeout=self.timeout
                )
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                return {"url": url, "title": "", "content": "", "error": str(e)}

    def scrape_single_url(self, url):
        """Scrape a single URL and return parsed data."""
        try:
            # TODO: Update User-Agent with Rubicon's contact email that ensures this crawler is not a bot.
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            # For Naver Blog, parse the mobile page for convenience
            url = url.replace("://blog.naver.com", "://m.blog.naver.com")

            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            # Create Scrapy response object
            scrapy_response = HtmlResponse(
                url=url, body=response.content, encoding=response.encoding or "utf-8"
            )

            return self.parse(scrapy_response)

        except Exception as e:
            raise Exception(f"Failed to scrape {url}: {str(e)}")

    def parse(self, response):
        """Parse response using Scrapy selectors."""
        title = response.css("title::text").get()
        content = self.extract_clean_content(response)

        return {
            "url": response.url,
            "title": self.text_parser(title),
            "content": self.text_parser(content),
        }

    def get_content_selectors(self, response):
        if "samsung.com/sec/" in response.url:
            content_selectors = ["div#container"]
            content_filter = """
                .//text()[
                    not(parent::script) and 
                    not(parent::style) and 
                    not(parent::noscript) and
                    not(parent::meta) and
                    not(ancestor::head) and
                    not(ancestor::span) and
                    not(ancestor::button) and
                    not(ancestor::a) and
                    not(ancestor::*[contains(@class, "layer-header")]) and
                    not(ancestor::*[contains(@class, "LatestItm-result")]) and
                    not(ancestor::*[contains(@class, "caution-note")]) and
                    not(ancestor::*[contains(@class, "zoomView")]) and                       
                    normalize-space(.) != ""
                ]
            """
        elif "blog.naver.com" in response.url:
            content_selectors = ["div._postView"]
            content_filter = """
                .//text()[
                    not(parent::script) and 
                    not(parent::style) and 
                    not(parent::noscript) and
                    not(parent::meta) and
                    not(ancestor::head) and
                    not(ancestor::a) and
                    not(ancestor::button) and
                    not(ancestor::*[contains(@class, "post_function_t1")]) and
                    not(ancestor::*[contains(@class, "blog_authorArea")]) and                       
                    normalize-space(.) != ""
                ]
            """
        elif "samsungsvc.co.kr/" in response.url:
            content_selectors = ['div[class="sec-box page-cont"]', "div.sec-box"]
            content_filter = """
                .//text()[
                    not(parent::script) and 
                    not(parent::style) and 
                    not(parent::noscript) and
                    not(parent::meta) and
                    not(ancestor::head) and
                    not(ancestor::a) and
                    not(ancestor::button) and                       
                    normalize-space(.) != ""
                ]
            """
        elif "tistory.com" in response.url:
            content_selectors = ["body"]
            content_filter = """
                .//text()[
                    not(parent::script) and 
                    not(parent::style) and 
                    not(parent::noscript) and
                    not(parent::meta) and
                    not(ancestor::head) and
                    not(ancestor::button) and
                    not(ancestor::header) and
                    not(ancestor::a) and
                    not(ancestor::*[contains(@class, "article-header")]) and
                    not(ancestor::*[contains(@class, "article-related")]) and
                    not(ancestor::*[contains(@class, "revenue_unit_item")]) and
                    not(ancestor::*[contains(@class, "box-category")]) and
                    not(ancestor::*[contains(@class, "box-recent")]) and
                    not(ancestor::*[contains(@class, "another_category")]) and
                    not(ancestor::*[contains(@class, "article-page")]) and
                    not(ancestor::*[contains(@class, "article-tag")]) and
                    not(ancestor::*[contains(@class, "#menubar menu_toolbar")]) and
                    not(ancestor::*[contains(@class, "search")]) and
                    not(ancestor::*[contains(@class, "inner_aside")]) and        
                    normalize-space(.) != ""
                ]
            """  # Exclude unnecessary elements for Tistory main page
        elif "samsung.com/uk/" in response.url:
            content_selectors = ["div#content"]
            content_filter = (
                content_filter
            ) = """
                .//text()[
                    not(parent::script) and 
                    not(parent::style) and 
                    not(parent::noscript) and
                    not(parent::meta) and
                    not(ancestor::head) and
                    not(ancestor::button) and
                    not(ancestor::*[contains(@class, "hideInAem")]) and                       
                    normalize-space(.) != ""
                ]
            """
        else:
            # Set up the default template for future target URLs
            content_selectors = ["body"]
            content_filter = """
                .//text()[
                    not(parent::script) and 
                    not(parent::style) and 
                    not(parent::noscript) and
                    not(parent::meta) and
                    not(ancestor::head) and
                    not(ancestor::button) and                       
                    normalize-space(.) != ""
                ]
            """

        return content_selectors, content_filter

    def extract_clean_content(self, response):
        """Extract clean text content."""
        content_selectors, content_filter = self.get_content_selectors(response)

        for selector in content_selectors:
            content_div = response.css(selector)
            if content_div:
                # remove JS, CSS, etc...
                text_nodes = content_div.xpath(content_filter).getall()

                if text_nodes:
                    return " ".join(text_nodes).strip()

        return ""

    def text_parser(self, text):
        """Clean and format text."""
        if text:
            # Remove extra whitespace and normalize
            cleaned = " ".join(text.split())
            return cleaned.replace("\n", " ").replace("\t", " ").strip()
        return ""


def get_quantile(df: pd.DataFrame, column_name: str, quantile: float):
    """
    Calculates the 75th percentile (third quartile) of a specified column in a pandas DataFrame.
    Args:
      df: The pandas DataFrame.
      column_name: The name of the column.
    Returns:
      The 75th percentile value of the column.
      Returns None if the column does not exist in the DataFrame.
    """
    if column_name not in df.columns:
        print(f"Error: Column '{column_name}' not found in the DataFrame.")
        return None
    return df[column_name].quantile(quantile)


# Execute and filter Google search results
async def fetch_for_keyword(
    client: httpx.AsyncClient,
    keyword_val: str,
    restricted,
    timeout: float,
    query_type: str,
    query: str,
    country: str,
    sites: list[str],
    k: int,
) -> list[dict]:
    # --- perform the google‐search + filter logic ---
    if (use_intelligence := query_type) in [  # example; replace with your real flag
        sub_intelligences.PRODUCT_FEATURE,
        sub_intelligences.PRODUCT_SPECIFICATION,
        sub_intelligences.PRODUCT_FUNCTION,
        sub_intelligences.PRODUCT_REVIEW,
        sub_intelligences.SAMSUNG_COMPARISON,
        sub_intelligences.COMPETITOR_COMPARISON,
        sub_intelligences.PERSONALIZED_COMPARISON,
        sub_intelligences.GENERAL_RECOMMENDATION,
        sub_intelligences.CONDITIONAL_RECOMMENDATION,
        sub_intelligences.PERSONALIZED_RECOMMENDATION,
        sub_intelligences.CONSUMABLES_ACCESSORIES_RECOMMENDATION,
    ] and not restricted:
        responses = await get_google_search_result(
            "y1", client, query_type, keyword_val, query, country, sites
        )
        if len(responses) < 6:
            responses = await get_google_search_result(
                "y2", client, query_type, keyword_val, query, country, sites
            )
        if len(responses) < 6:
            responses = await get_google_search_result(
                "y4", client, query_type, keyword_val, query, country, sites
            )
    else:
        responses = await get_google_search_result(
            "y10", client, query_type, keyword_val, query, country, sites
        )

    # __log.debug(responses)
    filtered_data = []
    filtered_snippet = []
    filtered_name = []
    filtered_name_parts = []
    for row in responses:
        filtered_data.append(row.get("link", "Unknown"))
        filtered_snippet.append(row.get("snippet", "Unknown"))
        filtered_name.append(row.get("title", "Unknown"))
        filtered_name_parts.append(
            [part.strip() for part in filtered_name[-1].split("|")]
        )

    # ----------------------------------------------------------------------------------------------
    new_filtered_data = []
    if country == "KR":
        for idx, (url, name, name_part, snippet) in enumerate(
            zip(
                filtered_data,
                filtered_name,
                filtered_name_parts,
                filtered_snippet,
            )
        ):
            do_filter = False

            if "all" in url:
                do_filter = True
            if "shop" in url:
                do_filter = True
            if "promotion" in url:
                do_filter = True
            if "event" in url:
                do_filter = True
            if "buy" in url:
                do_filter = True
            if "https://www.samsung.com/sec/" == url:
                do_filter = True
            if "b2c" in url:
                do_filter = True
            if "https://www.samsung.com/sec/" in url and "/specs/" in url:
                do_filter = True
            if "tistory.com/" in url:  # Exclude Tistory main page, collect others
                if not url.split("tistory.com/")[1]:
                    do_filter = True
            if query_type == "product":
                if "www.samsungsvc.co.kr" in url:
                    do_filter = True
            if query_type == "function":
                if "www.samsung.com/sec/" in url:
                    do_filter = True
            if do_filter == False:
                new_filtered_data.append(
                    {
                        "url": url,
                        "name": name,
                        "name_part": name_part,
                        "snippet": snippet,
                        "index": idx,
                    }
                )

    if country == "GB":
        for idx, (url, name, name_part, snippet) in enumerate(
            zip(
                filtered_data,
                filtered_name,
                filtered_name_parts,
                filtered_snippet,
            )
        ):

            do_filter = False

            if (
                "samsung.com/uk/business/" in url
            ):  # Exclude Samsung.com UK business pages from collection
                do_filter = True

            if not do_filter:

                new_filtered_data.append(
                    {
                        "url": url,
                        "name": name,
                        "name_part": name_part,
                        "snippet": snippet,
                        "index": idx,
                    }
                )

    url_title_dict = {item["url"]: item["name"] for item in new_filtered_data}

    if query_type in ("product", "function"):
        url_list = [item["url"] for item in new_filtered_data]
        name_list = [item["name"] for item in new_filtered_data]
        name_part_list = [item["name_part"] for item in new_filtered_data]

        if len(name_list) == 0:
            result_dict = [{"url": [], "markdown": "No urls"}]
        else:
            final_ranked_results = []
            for idx, parts in enumerate(name_part_list):
                _, ranked_scores = embedding_rerank.rerank_list(query, parts)
                if ranked_scores:
                    final_ranked_results.append(
                        {
                            "name": name_list[idx],
                            "score": ranked_scores[0]["score"],
                        }
                    )
            final_ranked_results = sorted(
                final_ranked_results, key=lambda x: x["score"], reverse=True
            )
            ranked_names = [item["name"] for item in final_ranked_results]
            url_map = {item["name"]: item["url"] for item in new_filtered_data}
            filtered_data = [url_map[name] for name in ranked_names]

    elif query_type == "code":
        url_list = [item["url"] for item in new_filtered_data]
        if len(url_list) == 0:
            result_dict = [{"url": [], "markdown": "No urls"}]
        else:
            filtered_data = [url for url in url_list if query.lower() in url.lower()]
    else:
        name_list = [item["name"] for item in new_filtered_data]
        if len(name_list) == 0:
            result_dict = [{"url": [], "markdown": "No urls"}]
        else:
            ranked_name, ranked_name_with_score = embedding_rerank.rerank_list(
                query, name_list
            )
            url_map = {item["name"]: item["url"] for item in new_filtered_data}
            filtered_data = [url_map[name] for name in ranked_name]

    if len(filtered_data) > k:
        filtered_data = list(filtered_data)[:k]
    else:
        result_dict = [{"url": [], "markdown": "No urls"}]
    try:
        spider = RubiconSpider(urls=filtered_data)
        results = await spider.scrape_all()

        # Insert new search results into the DB
        for result in results:
            insert_into_db(
                keyword_val,
                query,
                query_type,
                country,
                result,
            )

        return [
            {
                "url": r.get("url", ""),
                "title": r.get("title", ""),
                "markdown": r.get("content", ""),
                "source": "web",
            }
            for r in results
        ]
    except Exception as e:
        print(f"Error in url_to_text: {e}")
        return []


# Execute and filter Google search results for each keyword in parallel
async def run_all_searches(
    keywords: list[str],
    restricted: bool,
    timeout: float,
    query_type: str,
    query: str,
    country: str,
    sites: list[str],
    k: int,
) -> list[dict]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = [
            fetch_for_keyword(
                client,
                kw,
                restricted,
                timeout=timeout,
                query_type=query_type,
                query=query,
                country=country,
                sites=sites,
                k=k,
            )
            for kw in keywords
        ]
        # wait for all to finish
        results_per_keyword = await asyncio.gather(*tasks)
    # flatten list of lists
    total_search_results = [item for sublist in results_per_keyword for item in sublist]
    return total_search_results


def graph_db_symantic_search(search_query, country_code, intelligence, sub_intelligence):
    # __log.debug(request_dict)
    target = "graph_db"

    with connection.cursor() as cursor:
        embedding = baai_embedding(search_query, "-")

        query = f"""
            SELECT 
                id,
                title,
                clean_content::text,
                content_embed <=> '{str(embedding[0])}' AS distance
            FROM rubicon_v3_web_clean_cache
            WHERE active is true
            and country_code = '{country_code}' 
            and source = '{target}'
            and not(%s = any(intelligence_filter))
            and not(%s = any(sub_intelligence_filter))
            ORDER BY 4
            LIMIT 60;
        """
        #              source = '{target}' and active = true and country_code = '{country_code}'

        cursor.execute(query, [intelligence, sub_intelligence])
        result = cursor.fetchall()

    columns = ["id", "title", "clean_content", "distance"]
    searched_df = pd.DataFrame(result, columns=columns)
    searched_df["similarity_score"] = searched_df["distance"].apply(
        lambda distance: 1 - distance
    )

    return searched_df


def make_graph_db_reference(country_code, search_query, intelligence, sub_intelligence):
    temp_list = []
    return_text = ""
    searched_df = graph_db_symantic_search(search_query, country_code, intelligence, sub_intelligence)
    if searched_df is None or not searched_df.empty:
        rerank_model_result = rerank_db_results(
            search_query, searched_df, "clean_content", 3
        )
        return rerank_model_result
    else:
        return None


def get_result_by_search_v2(
    intelligence,
    sub_intelligence,
    query_type,
    keywords_query,
    keywords,
    query,
    restricted,
    country,
    sites=["samsung.com"],
    k=3,
):
    __log.debug(
        f"query: {query}, keywords_query: {keywords_query}, intelligence: {intelligence}, sub_intelligence: {sub_intelligence}"
    )
    """Filter and sort Google search results"""

    timeout = 10

    results = []
    result_dict = []
    total_search_results = []
    temp_cache_result = pd.DataFrame()
    cache_result = pd.DataFrame()
    # Priority 1: Check if there is a web cache similar to the combined keyword or rewritten query
    try:
        # raise ValueError("Skip web cache search")

        # Original cache extraction code
        # cache = Web_Cache.objects.filter(
        #     query=keywords_query, country_code=country
        # ).all()

        # For top_query, use the keyword query
        embedding = embedding_rerank.baai_embedding(keywords_query, "")[0]

        with connection.cursor() as cursor:
            # Extract 20 cache items based on embedding
            sql = f"""
            SELECT title, 
                query, 
                clean_content,
                url,
                created_on,
                source,
                content_embed <#> %s::vector similarity
            FROM rubicon_v3_web_clean_cache 
            where country_code = %s
            and source = 'web'
            and active = True
            and clean_content != 'Not found'
            and not(%s = any(intelligence_filter))
            and not(%s = any(sub_intelligence_filter))
            ORDER BY content_embed <#> %s::vector
            LIMIT 20;
            """
            cursor.execute(sql, [embedding, country, intelligence, sub_intelligence, embedding])
            k_cache_search_result = cursor.fetchall()

            # Only use 1 perplexity cache for top_query
            sql = f"""
            SELECT title, 
                query, 
                clean_content,
                url,
                created_on,
                source,
                content_embed <#> %s::vector similarity
            FROM rubicon_v3_web_clean_cache 
            where country_code = %s
            and source = 'reference'
            and active = True
            and not(%s = any(intelligence_filter))
            and not(%s = any(sub_intelligence_filter))
            ORDER BY content_embed <#> %s::vector
            LIMIT 10;
            """
            cursor.execute(sql, [embedding, country, intelligence, sub_intelligence, embedding])
            k_perplexity_search_result = cursor.fetchall()

            k_cache_search_result = (
                pd.DataFrame(
                    k_cache_search_result,
                    columns=[
                        "title",
                        "query",
                        "clean_content",
                        "url",
                        "created_on",
                        "source",
                        "similarity",
                    ],
                )
                .sort_values(["url", "created_on"])
                .drop_duplicates("url", keep="last")
            )

            k_perplexity_search_result = pd.DataFrame(
                k_perplexity_search_result,
                columns=[
                    "title",
                    "query",
                    "clean_content",
                    "url",
                    "created_on",
                    "source",
                    "similarity",
                ],
            )

            k_perplexity_search_result["similarity"] = (
                k_perplexity_search_result["similarity"] * -1
            )

            k_cache_search_result["similarity"] = (
                k_cache_search_result["similarity"] * -1
            )

            k_perplexity_search_result = (
                k_perplexity_search_result.loc[
                    k_perplexity_search_result["similarity"] > 0.55
                ]
                .reset_index(drop=True)
                .head(8)
            )

            if not k_perplexity_search_result.empty:
                rerank_df = rerank_db_results(
                    keywords_query,
                    k_perplexity_search_result,
                    "clean_content",
                    100,
                    -1,
                    skip_threshold=True,
                    multiple_cols=True,
                )
                rerank_df = (
                    rerank_df.groupby(["title"])["reranker_score"]
                    .max()
                    .reset_index()
                    .sort_values("reranker_score", ascending=False)
                    .head(3)
                )
                k_perplexity_search_result = k_perplexity_search_result.merge(
                    rerank_df, how="inner", on="title"
                ).drop("reranker_score", axis=1)

        k_cache_search_result = (
            k_cache_search_result.loc[
                k_cache_search_result["similarity"]
                >= get_quantile(k_cache_search_result, "similarity", 0.5)
            ]
            .sort_values("similarity", ascending=False)
            .reset_index(drop=True)
        )

        # Add perplexity documents to the top
        cache_result = pd.concat(
            [k_perplexity_search_result, k_cache_search_result], ignore_index=True
        )

        if not cache_result.empty:

            cache_result = (
                cache_result.sort_values(["url", "created_on"])
                .drop_duplicates("url", keep="last")
                .sort_values(["source", "similarity"], ascending=[True, False])
                .reset_index(drop=True)
            )

        # If the number of web cache items is small or rerank score is low, perform a new search
        if get_quantile(cache_result, "similarity", 0.75) <= 0.5:
            __log.debug(f"no cache, len{len(cache_result)}")
            temp_cache_result = cache_result.copy()
            raise ValueError("no cache")

        # Return title, url, markdown
        result_dict = []
        for i, row in cache_result.iterrows():
            result_dict.append(
                {
                    "title": row["title"],
                    "url": row["url"],
                    "markdown": row["clean_content"],
                    "source": row["source"],
                }
            )

        print("Google Search retrieved from web cache")
        return result_dict

    # As the second priority, perform a new Google search
    except ValueError:
        print("New Google Search")
        total_search_results = asyncio.run(
            run_all_searches(
                keywords,
                restricted,
                timeout=5.0,
                query_type="product",
                query=query,
                country="KR",
                sites=["samsung.com"],
                k=int(k / len(keywords)),
            )
        )

        # Remove duplicates based on url
        existing_urls = []
        filtered_total_search_results = []
        for item in total_search_results:
            if item["url"] not in existing_urls:
                existing_urls.append(item["url"])
                filtered_total_search_results.append(item)
            else:
                continue

    # If there are results from either web cache or Google search
    if filtered_total_search_results or not temp_cache_result.empty:
        final_result_ls = []
        for i, row in temp_cache_result.iterrows():
            final_result_ls.append(
                {
                    "title": row["title"],
                    "url": row["url"],
                    "markdown": row["clean_content"],
                    "source": row["source"],
                }
            )
        for row in filtered_total_search_results:
            final_result_ls.append(
                {
                    "title": row["title"],
                    "url": row["url"],
                    "markdown": row["markdown"],
                    "source": row["source"],
                }
            )
        return final_result_ls
    # If result_dict exists normally, use it after reranking
    else:
        return []


# Final output function
def get_google_search_results(
    keywords: list,
    query: str,
    intelligence: str,
    sub_intelligence: str,
    query_type: str,
    search_item,
    country_code: str = "KR",
):
    """Retrieve and organize Google search results"""
    # __log.debug(f'search_item: {search_item}')
    if "restricted" not in search_item:
        search_item["restricted"] = False

    if "restricted_query" in search_item:
        keywords_query = search_item["restricted_query"]
    else:
        keywords_query = " ".join(keywords)
    # __log.debug(f'keywords_query: {keywords_query}')

    use_intelligence = sub_intelligence

    if query_type == "top_query":
        k = 8
    else:
        k = 1

    try:
        if search_item["restricted"] == True:
            if query_type == "product":
                site_selected = ["DOT.COM"]
            else:
                site_selected = ["SERVICE"]
        elif query_type == "product":
            site_selected = ["DOT.COM"]
        elif use_intelligence == "Shallow":
            site_selected = ["SERVICE", "NAVER_BLOG", "TISTORY"]
        else:
            site_selected = list(
                Intelligence_V2.objects.filter(
                    sub_intelligence=use_intelligence
                ).values_list("intelligence_meta", flat=True)
            )[0].get(_22_orchestrator_intelligence.MetaColumns.WEB_SEARCH, "")

        # if restricted == True:
        #     site_selected = ["DOT.COM", "SERVICE"]
    except:
        site_selected = ["DOT.COM", "SERVICE"]

    search_sites = [google_search_mapping[country_code][key] for key in site_selected]
    search_sites = list(set(search_sites))

    google_search_results = get_result_by_search_v2(
        intelligence,
        sub_intelligence,
        query_type,
        keywords_query,
        keywords,
        query,
        search_item["restricted"],
        country_code,
        search_sites,
        k,
    )
    google_search_len = len(google_search_results)
    iter_google_search_results = iter(google_search_results)

    # Get related documents stored as web clean cache from graph DB
    graph_db_result = make_graph_db_reference(country_code, keywords_query, intelligence, sub_intelligence)
    if graph_db_result is None or graph_db_result.empty:
        google_search_content = []
    else:
        google_search_content = [
            {
                "title": rows["title"],
                "text_data": rows["clean_content"],
                "id": "",
                "image_url": "",
                "index_name": google_search_mapping[country_code]["DOT.COM"],
                "blob_path": "",
                "priority": "high",
                "source": "graph_db",
            }
            for i, rows in graph_db_result.iterrows()
        ]

    iter_count = min(k, google_search_len - 1) if google_search_len > 1 else 1
    for _ in range(iter_count):
        value = next(iter_google_search_results)

        # __log.debug(value)

        answer = str(value.get("markdown"))
        url = value.get("url")
        title = value.get("title")
        source = value.get("source", "web")

        if source in ["reference", "graph_db"]:
            priority = "high"
        else:
            priority = "low"
        # __log.debug(source)

        google_search_content.append(
            {
                "title": title,
                "text_data": answer,
                "id": "",
                "image_url": "",
                "index_name": search_sites,
                "blob_path": url,
                "priority": priority,
                "source": source,
            }
        )

    return google_search_content


if __name__ == "__main__":
    # (, '웰컴 쿨링 기능이 뭐야', 'Product Description', 'top_query', 'KR')
    # search_result = get_google_search_results(
    #     ['삼성', '웰컴 쿨링 기능'],
    #     "웰컴쿨링 기능이 뭐야?",
    #     'Product Description',
    #     "top_query",
    #     "KR",
    # )
    # M-S926NZYEKOO AI 기능 무료 사용 기간
    search_result = get_google_search_results(
        ["삼성", "무빙스타일 리모컨 배터리 충전", "리모컨 배터리 충전 방법"],
        "형 솔라셀 에어컨 리모컨",
        "Usage Manual",
        "Usage Explanation",
        "function",
        {
            "query": "형 솔라셀 에어컨 리모컨",
            "intelligence": "Usage Manual",
            "sub_intelligence": "Usage Explanation",
            "type": "function",
            "restricted": True,
        },
        "KR",
    )

    __log.debug(search_result)
