"""
This module defines the Manhuaes class for interacting with the website manhuaes.com.

The Manhuaes class provides methods to fetch manga IDs, chapters, images, 
and metadata from manhuaes.com, and to download manga images and save them as .cbz files.

Classes:
    Manhuaes: A class to interact with the website manhuaes.com.
"""
import requests
from bs4 import BeautifulSoup


class Manhuaes:
    """
    A class to interact with the website manhuaes.com.

    This class provides methods to fetch manga IDs, chapters, images,
    and metadata from manhuaes.com, and to download manga images and save them as .cbz files.

    Attributes:
        logger: An instance of log.Logger for log.
    """

    base_headers = {
        "authority": "manhuaes.com",
        "accept-language": "en-US,en;q=0.9,es-US;q=0.8,es;q=0.7,en-GB-oxendict;q=0.6",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "sec-ch-ua": '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-site": "none",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
        ),
    }

    headers_get = base_headers.copy()
    headers_get.update(
        {
            "accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
            ),
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
        }
    )

    headers_post = base_headers.copy()
    headers_post.update(
        {
            "accept": "*/*",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://manhuaes.com",
            "referer": "https://manhuaes.com/manga/carnephelias-curse-is-never-ending/",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "x-requested-with": "XMLHttpRequest",
        }
    )

    headers_image = base_headers.copy()
    headers_image.update(
        {
            "authority": "img.manhuaes.com",
            "accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "referer": "https://manhuaes.com/",
            "sec-fetch-dest": "image",
            "sec-fetch-mode": "no-cors",
            "sec-fetch-site": "same-site",
        }
    )

    def __init__(self, logger):
        self.logger = logger

    def get_manga_id(self, manga_name: str):
        """
        Get the manga ID for a given manga name.
        """
        result = requests.get(
            url=f"https://manhuaes.com/manga/{manga_name}",
            headers=self.headers_get,
            timeout=30,
        )

        if result.status_code == 200:
            soup = BeautifulSoup(result.text, "html.parser")
            node = soup.find("div", {"id": "manga-chapters-holder"})
            if node:
                data_id = node["data-id"]
                node = soup.find("div", {"class": "post-title"})
                title = node.h1
                self.logger.debug("found the following id: %s", data_id)
                return data_id, title.text.lstrip().rstrip()
        self.logger.error("unable to find the manga id needed")
        return None

    def get_manga_chapters(self, manga_id: str):
        """
        Get the manga chapters for a given manga ID.
        """
        result = requests.post(
            url="https://manhuaes.com/wp-admin/admin-ajax.php",
            headers=self.headers_post,
            data={"action": "manga_get_chapters", "manga": manga_id},
            timeout=30,
        )
        if result.status_code == 200:
            soup = BeautifulSoup(result.text, "html.parser")
            nodes = soup.find_all("li", {"class": "wp-manga-chapter"})
            chapters = []

            for node in nodes:
                url = node.a["href"]
                if "/chapter-0" not in url:
                    chapters.append(url)

            chapters.sort(key=lambda url: int(url.split("/chapter-")[-1].split("/")[0]))

            return chapters

        return None

    def get_chapter_images(self, url: str):
        """
        Get the manga chapter images for a given chapter URL.
        """
        result = requests.get(
            url=url,
            headers=self.headers_get,
            timeout=30,
        )

        if result.status_code == 200:
            soup = BeautifulSoup(result.text, "html.parser")
            node = soup.find("div", {"class": "reading-content"})
            image_nodes = node.find_all("img")
            images = []
            for image_node in image_nodes:
                images.append(image_node["data-src"].lstrip().rstrip())

            return images

    def get_manga_metadata(self, manga_name: str):
        """
        Get the manga metadata for a given manga name.
        """
        result = requests.get(
            url=f"https://manhuaes.com/manga/{manga_name}",
            headers=self.headers_get,
            timeout=30,
        )

        if result.status_code == 200:
            soup = BeautifulSoup(result.text, "html.parser")

            genres_content = soup.find("div", {"class": "genres-content"})
            genres = [a.text for a in genres_content.find_all("a")]

            summary_content = soup.find("div", {"class": "summary__content show-more"})
            summary = summary_content.p.text

            return genres, summary

        self.logger.error("unable to fetch the manga metadata")
        return None
