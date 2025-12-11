"""
JSearch API Client for job search and job details retrieval.
Uses RapidAPI's JSearch endpoint.
"""

import os
import aiohttp
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

# Support both variable names for flexibility
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY") or os.getenv("JSEARCH_API_KEY")
RAPIDAPI_HOST = "jsearch.p.rapidapi.com"
BASE_URL = "https://jsearch.p.rapidapi.com"


def get_headers() -> dict:
    """Get headers required for JSearch API requests."""
    return {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }


async def search_jobs(
    query: str,
    page: int = 1,
    num_pages: int = 1,
    country: str = "us",
    date_posted: str = "all",
    employment_types: Optional[str] = None,
    job_requirements: Optional[str] = None,
    work_from_home: bool = False,
    radius: Optional[int] = None,
    exclude_job_publishers: Optional[str] = None
) -> dict:
    """
    Search for jobs using JSearch API.
    
    Args:
        query: Free-form job search text (e.g., "developer jobs in chicago")
        page: Page index (1-50), default 1
        num_pages: Number of pages to fetch (1-50), default 1
        country: ISO-3166-1 alpha-2 country code, default "us"
        date_posted: Filter by posting age ("all", "today", "3days", "week", "month")
        employment_types: Comma-separated types ("FULLTIME", "CONTRACTOR", "PARTTIME", "INTERN")
        job_requirements: Comma-separated requirements ("under_3_years_experience", 
                         "more_than_3_years_experience", "no_experience", "no_degree")
        work_from_home: Return only remote jobs, default False
        radius: Search radius in km from location
        exclude_job_publishers: Comma-separated publishers to exclude
    
    Returns:
        dict containing job search results
    """
    if not RAPIDAPI_KEY:
        logger.error("RAPIDAPI_KEY not found in environment variables")
        return {"status": "error", "message": "API key not configured", "data": []}
    
    url = f"{BASE_URL}/search"
    
    params = {
        "query": query,
        "page": str(page),
        "num_pages": str(num_pages),
        "country": country,
        "date_posted": date_posted
    }
    
    if employment_types:
        params["employment_types"] = employment_types
    if job_requirements:
        params["job_requirements"] = job_requirements
    if work_from_home:
        params["work_from_home"] = "true"
    if radius:
        params["radius"] = str(radius)
    if exclude_job_publishers:
        params["exclude_job_publishers"] = exclude_job_publishers
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=get_headers(), params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Job search successful: found {len(data.get('data', []))} jobs")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"Job search failed: {response.status} - {error_text}")
                    return {"status": "error", "message": f"API error: {response.status}", "data": []}
    except Exception as e:
        logger.error(f"Job search exception: {str(e)}")
        return {"status": "error", "message": str(e), "data": []}


async def get_job_details(
    job_id: str,
    country: str = "us"
) -> dict:
    """
    Get detailed information for a specific job.
    
    Args:
        job_id: ID of the job to fetch details for (supports batching up to 20 IDs)
        country: ISO-3166-1 alpha-2 country code, default "us"
    
    Returns:
        dict containing job details
    """
    if not RAPIDAPI_KEY:
        logger.error("RAPIDAPI_KEY not found in environment variables")
        return {"status": "error", "message": "API key not configured", "data": []}
    
    url = f"{BASE_URL}/job-details"
    
    params = {
        "job_id": job_id,
        "country": country
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=get_headers(), params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Job details fetch successful for job_id: {job_id}")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"Job details fetch failed: {response.status} - {error_text}")
                    return {"status": "error", "message": f"API error: {response.status}", "data": []}
    except Exception as e:
        logger.error(f"Job details exception: {str(e)}")
        return {"status": "error", "message": str(e), "data": []}


def extract_job_card_data(job: dict) -> dict:
    """
    Extract relevant fields from a job object for displaying as a card.
    
    Args:
        job: Full job object from JSearch API
    
    Returns:
        dict with relevant fields for frontend display
    """
    # Format salary if available
    salary = None
    if job.get("job_min_salary") and job.get("job_max_salary"):
        period = job.get("job_salary_period", "yearly")
        salary = f"${job['job_min_salary']:,.0f} - ${job['job_max_salary']:,.0f} {period}"
    elif job.get("job_salary"):
        salary = job.get("job_salary")
    
    return {
        "job_id": job.get("job_id", ""),
        "job_title": job.get("job_title", "Unknown Title"),
        "employer_name": job.get("employer_name", "Unknown Company"),
        "job_description": job.get("job_description", "")[:500] + "..." if len(job.get("job_description", "")) > 500 else job.get("job_description", ""),
        "job_location": job.get("job_location") or job.get("job_city", ""),
        "job_salary": salary,
        "job_employment_type": job.get("job_employment_type", ""),
        "job_apply_link": job.get("job_apply_link", ""),
        "job_posted_at": job.get("job_posted_at", ""),
        "job_is_remote": job.get("job_is_remote"),
        "employer_logo": job.get("employer_logo"),
        "job_highlights": job.get("job_highlights")
    }


def extract_job_cards_from_response(response: dict) -> List[dict]:
    """
    Extract job cards from JSearch API response.
    
    Args:
        response: Full response from JSearch API
    
    Returns:
        List of job card data dictionaries
    """
    jobs = response.get("data", [])
    return [extract_job_card_data(job) for job in jobs]
