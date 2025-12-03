import requests
from typing import Optional, List, Any, Dict

from config import API_URL, API_SECRET_BOT_KEY


class APIUtils:
    USERS_PATH = "/users/"
    
    def __init__(self, base_url: str = API_URL):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "X-API-KEY": API_SECRET_BOT_KEY
        }

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> dict:
        url = f"{self.base_url}{path}"
        resp = requests.get(url, params=params, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, payload: Optional[Dict[str, Any]] = None) -> dict:
        url = f"{self.base_url}{path}"
        resp = requests.post(url, json=payload, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def _delete(self, path: str) -> dict:
        url = f"{self.base_url}{path}"
        resp = requests.delete(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()


    def get_user(self, user_uuid: str) -> dict | int:
        try:
            return self._get(f"{self.USERS_PATH}{user_uuid}")
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return 404
            raise

    def create_user(self, user_uuid: str, audiolist: Optional[List[int]] = None) -> dict:
        payload = {"user_uuid": user_uuid, "audiolist": audiolist or []}
        return self._post(self.USERS_PATH, payload)

    def add_audiolist(self, user_uuid: str, audiolist: List[int]) -> dict:
        payload = {"audiolist": audiolist}
        return self._post(f"{self.USERS_PATH}{user_uuid}/audiolist", payload)

    def delete_audio_item(self, user_uuid: str, item_id: int) -> dict:
        return self._delete(f"{self.USERS_PATH}{user_uuid}/audiolist/{item_id}")