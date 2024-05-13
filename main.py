from fastapi import FastAPI, Request, Response
from starlette.responses import JSONResponse
import requests
from urllib.parse import urlsplit, urlunsplit

PROXY_PREFIX = "http://127.0.0.1:8000/proxy?url="


DONT_COPY_HEADERS = [
    "date",
    "content-length",
    "content-encoding",
    "transfer-encoding",
    "connection",
    "host",
]

app = FastAPI()


def clean_headers(headers):
    proxy_headers = {}

    for header in headers:
        if header.lower() not in DONT_COPY_HEADERS:
            proxy_headers[header] = headers[header]
    return proxy_headers


def get_root_url(url):
    split_url = urlsplit(url)

    return f"{split_url.scheme}://{split_url.netloc}"


# You now have:
# split_url.scheme   "http"
# split_url.netloc   "127.0.0.1"
# split_url.path     "/asdf/login.php"
# split_url.query    "q=abc"
# split_url.fragment "stackoverflow"


def replace_urls(html, url):
    root_url = get_root_url(url)

    fixedHtml = html.replace('src="/', f'src="{PROXY_PREFIX}{root_url}/')
    fixedHtml = fixedHtml.replace("src='/", f"src='{PROXY_PREFIX}{root_url}/")

    fixedHtml = fixedHtml.replace('href="/', f'href="{PROXY_PREFIX}{root_url}/')
    fixedHtml = fixedHtml.replace("href='/", f"href='{PROXY_PREFIX}{root_url}/")

    fixedHtml = html.replace('src="https://', f'src="{PROXY_PREFIX}https://')
    fixedHtml = fixedHtml.replace("src='https://", f"src='{PROXY_PREFIX}https://")

    fixedHtml = fixedHtml.replace('href="http://', f'href="{PROXY_PREFIX}http://')
    fixedHtml = fixedHtml.replace("href='http://", f"href='{PROXY_PREFIX}http://")

    fixedHtml = fixedHtml.replace('href="https://', f'href="{PROXY_PREFIX}https://')
    fixedHtml = fixedHtml.replace("href='https://", f"href='{PROXY_PREFIX}https://")

    return fixedHtml


@app.get("/")
async def index():
    return {"success": True}


@app.get("/hc")
async def healthcheck():
    return {"success": True}


@app.get("/proxy")
async def proxy(req: Request):
    try:
        url = req.query_params["url"]
    except KeyError:
        return JSONResponse({"success": False, "msg": "URL not specified"}, 400)

    # try:
    if True:
        proxy_req_headers = clean_headers(req.headers)

        # print(proxy_resp_headers)
        resp = requests.get(url, headers=proxy_req_headers, verify=False)

        proxy_resp_headers = clean_headers(resp.headers)

        # print(proxy_resp_headers)

        try:
            proxy_resp_content = (
                replace_urls(resp.text, url)
                if resp.headers["Content-type"].startswith("text/html")
                else resp.text
            )
        except KeyError:
            try:
                proxy_resp_content = (
                    replace_urls(resp.text, url)
                    if resp.headers["content-type"].startswith("text/html")
                    else resp.text
                )
            except KeyError:
                proxy_resp_content = resp.text

        return Response(proxy_resp_content, headers=proxy_resp_headers)
    # except Exception as e:
    #     return JSONResponse({"success": False, "msg": str(e)}, 400)
