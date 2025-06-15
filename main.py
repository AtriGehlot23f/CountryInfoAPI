from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from bs4 import BeautifulSoup

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

WIKI_BASE_URL = "https://en.wikipedia.org/wiki/"

async def fetch_wikipedia_page(country: str) -> str:
    url = WIKI_BASE_URL + country.replace(" ", "_")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10)
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail=f"Wikipedia page not found for '{country}'")
            return response.text
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Error fetching Wikipedia page: {str(e)}")

def extract_headings(html: str) -> list[tuple[int, str]]:
    soup = BeautifulSoup(html, "html.parser")
    content_div = soup.find("div", {"id": "mw-content-text"})
    if not content_div:
        raise HTTPException(status_code=500, detail="Wikipedia page content not found")

    headings = []
    for tag in content_div.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        level = int(tag.name[1])
        text = tag.get_text(separator=" ", strip=True)
        if text:
            headings.append((level, text))
    return headings

def generate_markdown_outline(country: str, headings: list[tuple[int, str]]) -> str:
    md_lines = ["## Contents", "", f"# {country}", ""]
    for level, text in headings:
        md_lines.append("#" * level + " " + text)
    return "\n".join(md_lines)

@app.get("/api/outline")
async def outline(country: str = Query(..., description="Country name")):
    html = await fetch_wikipedia_page(country)
    headings = extract_headings(html)
    markdown = generate_markdown_outline(country, headings)
    return {"country": country, "markdown_outline": markdown}
