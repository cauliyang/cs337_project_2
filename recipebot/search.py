from typing import Literal

import yt_dlp
from ddgs import DDGS
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    title: str = Field(..., description="The title of searching item")
    url: str = Field(..., description="The url of searching item")
    source: str = Field(..., description="Where the searching item is searched")
    id: str | None = Field(None, description="The id of searching item")
    duration: int | None = Field(None, description="The duration of searching item")
    view_count: int | None = Field(None, description="The view count of searching item")
    reponse: dict[str, str] | None = Field(None, description="The response of searching item")


def search_youtube(query, max_results=5):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,  # Don't download, just get metadata
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search_results = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)

        videos = []
        for video in search_results["entries"]:
            videos.append(
                SearchResult(
                    title=video["title"],
                    url=f"https://www.youtube.com/watch?v={video['id']}",
                    source="YTB",
                    id=video["id"],
                    duration=video.get("duration"),
                    view_count=video.get("view_count"),
                )
            )
        return videos


def search_duckduckgo(
    query, search_type: Literal["text", "news", "images", "videos"] = "text", max_results=10, region="us-en"
):
    """Search web info.

    Return:
        text:
            {
        'title': '5 Ways to Make a Salad - wikiHow',
        'href': 'https://www.wikihow.com/Make-a-Salad',
        'body': 'To make a salad , start by choosing a base, like lettuce, leafy kale, or spinach.
          Then, add delicious toppings to the base, like fresh vegetables,
            fruit, nuts, beans, and cheese.' }

        news:
            {
            'date': '2025-11-14T04:58:33+00:00',
            'title': 'Thanksgiving salad with pears, Parmesan and pomegranate seeds,
    starring puff...',
            'body': 'First of all, anytime you want to make a salad feel very festive
    and holiday-ish, you can’t go wrong...',
            'url': 'https://www.pilotonline.com/2025/11/14/recipe-thanksgiving-salad/',
            'image': 'https://s.yimg.com/am/60d/c71bf029af203671bc1ce8784183ca7e',
            'source': 'The Virginian-Pilot'
            }

        images:
            {
            'title': 'How to Make Salad: Recipes, Tips and More | Taste of Home',
            'image':
    'https://www.tasteofhome.com/wp-content/uploads/2018/01/exps178590_TH143194D06_19_6b-2.jpg?fit=680,680',
            'thumbnail':
    'https://tse4.mm.bing.net/th/id/OIP.amLkQpSN09YAPBN81LKHFwHaHa?pid=Api',
            'url': 'https://www.tasteofhome.com/article/how-to-make-salad/',
            'height': 680,
            'width': 680,
            'source': 'Bing'}

        videos:
            {
            'title': 'How to Make a Salad | Easy Salad Recipe | My Favorite Salad',
            'content':
    'https://www.msn.com/en-us/foodanddrink/recipes/how-to-make-a-salad-easy-salad-recipe-my-favorite-salad/vi-AA1Oel7c',
            'description': 'In this episode of In the Kitchen with Matt I will show you
    how to make a salad. This easy salad recipe is my favorite salad to eat and I eat
    it all the time. Salads can be super healthy for you depending on what you put on
    them. I had a request to do a video on a vegetable salad so here we go! In order to
    be a true vegetable salad just leave ...',
            'duration': '5:49',
            'embed_html': '',
            'embed_url': '',
            'image_token':
    'ba50cd4ae35ff833dc773b8e60dc199301ebe14d5f6b842f0e96dc5fd95bb14b',
            'images': {
                'large':
    'https://tse2.mm.bing.net/th/id/OVP.wY50AYw4JyQCT0wrJoJsBwHgEO?pid=Api',
                'medium':
    'https://tse2.mm.bing.net/th/id/OVP.wY50AYw4JyQCT0wrJoJsBwHgEO?pid=Api',
                'motion': 'https://tse4.mm.bing.net/th/id/OM2.iAhzIXo2IHZNWw?pid=Api',
                'small':
    'https://tse2.mm.bing.net/th/id/OVP.wY50AYw4JyQCT0wrJoJsBwHgEO?pid=Api'
            },
            'provider': 'Bing',
            'published': '2025-10-22T22:25:03.0000000',
            'publisher': 'Microsoft News',
            'statistics': {'viewCount': None},
            'uploader': 'In The Kitchen With Matt'
            }
    """
    match search_type:
        case "text":
            results = DDGS().text(query, region=region, max_results=max_results)
        case "news":
            results = DDGS().news(query, region=region, max_results=max_results)
        case "images":
            results = DDGS().images(query, region=region, max_results=max_results)
        case "videos":
            results = DDGS().videos(query, region=region, max_results=max_results)

    return results
