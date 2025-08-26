from datetime import date
from enum import Enum
from typing import Optional

import httpx
from fastapi import APIRouter
from fastmcp import FastMCP
from pydantic import BaseModel

router = APIRouter(prefix="/vcell", tags=["virtual cell"])
mcpRouter = FastMCP(name="VCell MCP")



VCELL_API_BASE_URL = "https://vcell.cam.uchc.edu/api/v0"


class CategoryEnum(str, Enum):
    all = "all"
    public = "public"
    shared = "shared"
    tutorials = "tutorial"
    educational = "educational"


class OrderByEnum(str, Enum):
    date_desc = "date_desc"
    date_asc = "date_asc"
    name_desc = "name_desc"
    name_asc = "name_asc"


class BiomodelRequestParams(BaseModel, use_enum_values=True):
    bmName: Optional[str] = ""  # Name of the biomodel to search for
    bmId: Optional[str] = ""  # Biomodel ID
    category: Optional[CategoryEnum] = CategoryEnum.all  # Category of the biomodel
    owner: Optional[str] = ""  # Owner of the biomodel
    savedLow: Optional[date] = None  # Lower bound of the save date range
    savedHigh: Optional[date] = None  # Upper bound of the save date range
    startRow: Optional[int] = 1  # Starting row of the result set (default is 1)
    maxRows: Optional[int] = 1000  # Maximum number of rows to return (default is 100)
    orderBy: Optional[OrderByEnum] = (
        OrderByEnum.date_desc
    )  # Order of results (default is "date_desc")


@mcpRouter.tool(name ="Grab BioModels.", title="Grab BioModels.", description="Get BioModels that relate to the search keyword given.", tags={"biology", "physiology", "virtual cell", "vcell"})
async def fetch_biomodel_mcp(bio_model_keyword: str) -> dict:
    return await fetch_biomodels(bio_model_keyword)


@router.get("/biomodel")
async def fetch_biomodels(bio_model_keyword: str) -> dict:
    """
    Fetch a list of biomodels from the VCell API based on query.
    Args:
        bio_model_keyword (str): The query string which searches VCell for a BioModel name that has this keyword.

    Returns:
        dict: A dictionary containing a list of biomodels with metadata, the list will at most contain 5 biomodels.
    """
    # Transform None to "" (optional, only if needed for empty fields)
    # params_dict = {
    #     k: (v if v is not None else "") for k, v in params.dict().items()
    # }



    # Construct the query string using urlencoded parameters (params_dict)
    # query_string = urlencode(params_dict)

    # Construct the full URL
    url = f"{VCELL_API_BASE_URL}/biomodel?bmName={bio_model_keyword}&bmId=&category=all&owner=&savedLow=&savedHigh=&startRow=1&maxRows=5&orderBy=date_desc"

    # Log the URL being queried

    # Perform the API request
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        raw_data = response.json()

    # Extract biomodels list (assuming API returns a list directly)
    biomodels = raw_data if isinstance(raw_data, list) else raw_data.get("data", [])



    # Build response with metadata
    return {
        "search_params": bio_model_keyword,
        "models_count": len(biomodels),
        "unique_model_keys (bmkey)": [
            model.get("bmKey") for model in biomodels if model.get("bmKey")
        ],
        "data": biomodels,
    }

async def get_vcml_file(biomodel_id: str, truncate: bool = False) -> str:
    """
    Fetches the VCML file content for a given biomodel.

    Args:
        biomodel_id (str): ID of the biomodel.
        truncate (bool): Whether to truncate the VCML file.
    Returns:
        str: VCML content of the biomodel.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{VCELL_API_BASE_URL}/biomodel/{biomodel_id}/biomodel.vcml"
        )
        response.raise_for_status()
        if truncate:
            return response.text[:500]
        else:
            return response.text

async def get_sbml_file(biomodel_id: str) -> str:
    """
    Fetches the SBML file content for a given biomodel.

    Args:
        biomodel_id (str): ID of the biomodel.

    Returns:
        str: SBML content of the biomodel.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{VCELL_API_BASE_URL}/biomodel/{biomodel_id}/biomodel.sbml"
        )
        response.raise_for_status()
        return response.text

async def get_diagram_url(biomodel_id: str) -> str:
    """
    Gets diagram image URL for a given biomodel.

    Args:
        biomodel_id (str): ID of the biomodel.

    Returns:
        str: URL pointing to the biomodel's diagram image.
    """
    return f"{VCELL_API_BASE_URL}/biomodel/{biomodel_id}/diagram"
