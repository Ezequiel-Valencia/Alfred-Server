import asyncio
import os
import requests
from datetime import datetime

from fastapi import HTTPException
from fastmcp import Client
from pydantic import BaseModel, Field
from typing import Callable, Any
from time import sleep
import xml.etree.ElementTree as ET


class PubMedResponse(BaseModel):
    pubmed_id: str
    title: str
    url: str
    authors: list[str]
    abstract: str


class EventEmitter:
    def __init__(self, event_emitter: Callable[[dict], Any] = None):
        self.event_emitter = event_emitter

    async def emit(self, description="Unknown State", status="in_progress", done=False):
        if self.event_emitter:
            await self.event_emitter(
                {
                    "type": "status",
                    "data": {
                        "status": status,
                        "description": description,
                        "done": done,
                    },
                }
            )


class Helper:
    def abstract(pubmed_id) -> dict:
        # Construct the PubMed API URL to fetch the abstract
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        url = f"{base_url}?db=pubmed&id={pubmed_id}&retmode=xml"

        try:
            # Make the request to the PubMed API to get the article details
            response = requests.get(url)
            response.raise_for_status()

            # Parse the XML response
            xml_data = response.text
            root = ET.fromstring(xml_data)

            # Find all the abstract elements
            abstract_elements = root.findall(".//AbstractText")

            if abstract_elements:
                abstract = "\n".join(
                    abstract_element.text.strip()
                    for abstract_element in abstract_elements
                )
                return {"abstract": abstract}
            else:
                return {"abstract": "Abstract Not Found"}

        except requests.exceptions.RequestException as e:
            raise HTTPException(500, {"error": str(e)})
        except ET.ParseError as e:
            raise HTTPException(500, {"error": "Error parsing XML response"})

    def keywords(pubmed_id):
        # Construct the PubMed API URL to fetch the article summary
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        url = f"{base_url}?db=pubmed&id={pubmed_id}&retmode=json"

        try:
            # Make the request to the PubMed API to get the article summary
            response = requests.get(url)
            response.raise_for_status()

            # Extract the keywords from the API response
            data = response.json()
            article_keywords = data["result"][pubmed_id]["keywords"]

            if article_keywords:
                return {"keywords": article_keywords}
            else:
                return {"keywords": "Keywords Not Found"}

        except requests.exceptions.RequestException as e:
            raise HTTPException(500, {"error": str(e)})


class Tools:
    def __init__(self):
        pass

    # Add your custom tools using pure Python code here, make sure to add type hints and descriptions

    async def search_papers(
        self, query: str, __event_emitter__: Callable[[dict], Any] = None
    ) -> list[PubMedResponse]:
        """
        Based on the query provided get a list of medical reserach papers with their abstract, title, authors, and url.
        It will only ever return at most three articles. Do not discuss about articles not in this list.
        """

        # Construct the PubMed API URL with the search term and page
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        url = f"{base_url}?db=pubmed&term={query}&retmode=json&retstart={1}&retmax=3"

        emitter = EventEmitter(__event_emitter__)

        try:
            await emitter.emit(f"Initiating PubMed serach for: {query}")
            # Make the request to the PubMed API to get the PubMed IDs
            response = requests.get(url)
            response.raise_for_status()

            # Extract the PubMed IDs from the API response
            data = response.json()
            pubmed_ids = data["esearchresult"]["idlist"]
            total_results = int(data["esearchresult"]["count"])
            total_pages = (total_results // 10) + 1

            article_details = []

            await emitter.emit(f"Got {len(pubmed_ids)} results.")
            # Retrieve article details using the PubMed API's esummary endpoint
            for pubmed_id in pubmed_ids:
                sleep(1)
                summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pubmed_id}&retmode=json"
                summary_response = requests.get(summary_url)
                summary_response.raise_for_status()

                summary_data = summary_response.json()
                article_title = summary_data["result"][pubmed_id]["title"]
                article_url = f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/"

                # Get the authors' information
                authors = summary_data["result"][pubmed_id]["authors"]
                author_names = [author["name"] for author in authors]
                papers_abstract = (Helper.abstract(pubmed_id))["abstract"]

                article_details.append(
                    PubMedResponse(
                        pubmed_id=pubmed_id,
                        title=article_title,
                        url=article_url,
                        authors=author_names,
                        abstract=papers_abstract,
                    )
                )
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "citation",
                            "data": {
                                "document": [papers_abstract],
                                "metadata": [{"source": article_url}],
                                "source": {"name": article_title},
                            },
                        }
                    )
            await emitter.emit(
                status="complete", description="Found PubMed articles", done=True
            )
            return article_details
        except requests.exceptions.RequestException as e:
            raise HTTPException(500, "Request exception.")

async def tester():
    client = Client("http://localhost:8000/mcp")
    async with client:
        await client.ping()

        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()

        print(tools)

    await client.close()

if __name__ == "__main__":


    asyncio.run(tester())

