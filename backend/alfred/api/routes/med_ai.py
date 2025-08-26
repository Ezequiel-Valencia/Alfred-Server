import asyncio
import uuid
from time import sleep
from typing import Any

from fastapi import APIRouter, HTTPException
import requests
import xml.etree.ElementTree as ET
from fastmcp import FastMCP
from pydantic import BaseModel

router = APIRouter(prefix="/research", tags=["ai"])
mcpRouter = FastMCP(name="Biological MCP")

# https://medium.com/@anoopjohny2000/make-your-own-pubmed-search-application-ac4028e6698a
# https://pmc.ncbi.nlm.nih.gov/tools/developers/
# https://pubmed.ncbi.nlm.nih.gov/download/


class PubMedResponse(BaseModel):
    pubmed_id: str
    title: str
    url: str
    authors: list[str]
    abstract: str


@mcpRouter.tool(name ="Search Pub-Med.", title="Search Pub-Med.", description="Search PubMed, the largest corpus of medical publications for specific keywords. It will return the abstracts and links of each paper.", tags=set("biology"))
async def read_items_mcp(search_query: str) -> list[PubMedResponse]:
    return await search_papers(search_query)

@router.get("/pubMed", response_model=list[PubMedResponse])
async def read_items(search_query: str) -> list[PubMedResponse]:
    return await search_papers(search_query)

async def search_papers(query: str) -> list[PubMedResponse]:
    # Construct the PubMed API URL with the search term and page
    base_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
    url = f'{base_url}?db=pubmed&term={query}&retmode=json&retstart={1}&retmax=3'

    try:
        # Make the request to the PubMed API to get the PubMed IDs
        response = requests.get(url)
        response.raise_for_status()

        # Extract the PubMed IDs from the API response
        data = response.json()
        pubmed_ids = data['esearchresult']['idlist']
        total_results = int(data['esearchresult']['count'])
        total_pages = (total_results // 10) + 1

        article_details = []

        # Retrieve article details using the PubMed API's esummary endpoint
        for pubmed_id in pubmed_ids:
            sleep(1)
            summary_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pubmed_id}&retmode=json'
            summary_response = requests.get(summary_url)
            summary_response.raise_for_status()

            summary_data = summary_response.json()
            article_title = summary_data['result'][pubmed_id]['title']
            article_url = f'https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/'

            # Get the authors' information
            authors = summary_data['result'][pubmed_id]['authors']
            author_names = [author['name'] for author in authors]
            papers_abstract = (await abstract(pubmed_id))['abstract']

            article_details.append(PubMedResponse(pubmed_id=pubmed_id, title=article_title, url=article_url, authors=author_names, abstract=papers_abstract))

        return article_details
    except requests.exceptions.RequestException as e:
        raise HTTPException(500, "Request exception.")


async def abstract(pubmed_id) -> dict:
    # Construct the PubMed API URL to fetch the abstract
    base_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
    url = f'{base_url}?db=pubmed&id={pubmed_id}&retmode=xml'

    try:
        # Make the request to the PubMed API to get the article details
        response = requests.get(url)
        response.raise_for_status()

        # Parse the XML response
        xml_data = response.text
        root = ET.fromstring(xml_data)

        # Find all the abstract elements
        abstract_elements = root.findall('.//AbstractText')

        if abstract_elements:
            abstract = '\n'.join(abstract_element.text.strip() for abstract_element in abstract_elements)
            return {'abstract': abstract}
        else:
            return {'abstract': 'Abstract Not Found'}

    except requests.exceptions.RequestException as e:
        raise HTTPException(500, {'error': str(e)})
    except ET.ParseError as e:
        raise HTTPException(500,{'error': 'Error parsing XML response'})


async def keywords(pubmed_id):
    # Construct the PubMed API URL to fetch the article summary
    base_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi'
    url = f'{base_url}?db=pubmed&id={pubmed_id}&retmode=json'

    try:
        # Make the request to the PubMed API to get the article summary
        response = requests.get(url)
        response.raise_for_status()

        # Extract the keywords from the API response
        data = response.json()
        article_keywords = data['result'][pubmed_id]['keywords']

        if article_keywords:
            return {'keywords': article_keywords}
        else:
            return {'keywords': 'Keywords Not Found'}

    except requests.exceptions.RequestException as e:
        raise HTTPException(500, {'error': str(e)})


if __name__ == "__main__":
    related_articles = asyncio.run(search_papers("Liver disease."))
    for i in related_articles:
        print(i.title)
        print(i.abstract)
        print(i.authors)

