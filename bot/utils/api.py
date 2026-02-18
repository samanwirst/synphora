import asyncio
from typing import Any, Dict, List, Optional

import requests

from config import SERVER_API_URL, AUDIO_STORAGE_API_URL, API_SECRET_BOT_KEY


class APIUtils:
    USERS_PATH = "/users/"
    ROOMS_PATH = "/rooms/"
    
    def __init__(self):
        if not API_SECRET_BOT_KEY:
            raise RuntimeError("API_SECRET_BOT_KEY is not configured")
        self.headers = {
            "X-API-KEY": API_SECRET_BOT_KEY
        }

    def _get(self, base: str, path: str, params: Optional[Dict[str, Any]] = None) -> dict:
        url = f"{base}{path}"
        resp = requests.get(url, params=params, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def _post(self, base: str, path: str, payload: Optional[Dict[str, Any]] = None) -> dict:
        url = f"{base}{path}"
        resp = requests.post(url, json=payload, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def _delete(self, base: str, path: str) -> dict | None:
        url = f"{base}{path}"
        resp = requests.delete(url, headers=self.headers)
        resp.raise_for_status()
        if resp.content:
            return resp.json()
        return None
    
    def _post_file(self, base: str, path: str, file_field: str, file_path: str, body: Dict[str, Any]) -> dict:
        url = f"{base}{path}"
        with open(file_path, "rb") as f:
            files = {file_field: (body.get("file_name", "file"), f)}
            data = {k: v for k, v in body.items()}
            resp = requests.post(url, files=files, data=data, headers=self.headers)
            resp.raise_for_status()
            return resp.json()


    def get_user(self, user_uuid: str) -> dict | int:
        try:
            return self._get(SERVER_API_URL, f"{self.USERS_PATH}{user_uuid}")
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return 404
            raise

    def create_user(self, user_uuid: str, audiolist: Optional[List[str]] = None) -> dict:
        payload = {"user_uuid": user_uuid, "audiolist": audiolist or []}
        return self._post(SERVER_API_URL, self.USERS_PATH, payload)

    def add_audiolist(self, user_uuid: str, audiolist: List[str]) -> dict:
        payload = {"audiolist": audiolist}
        return self._post(SERVER_API_URL, f"{self.USERS_PATH}{user_uuid}/audiolist", payload)

    def delete_audio_item(self, user_uuid: str, item_uuid: str) -> dict | None:
        return self._delete(SERVER_API_URL, f"{self.USERS_PATH}{user_uuid}/audiolist/{item_uuid}")

    def create_room(self, creator_user_uuid: str, creator_telegram_id: int, track_ids: List[str]) -> dict:
        payload = {
            "creator_user_uuid": creator_user_uuid,
            "creator_telegram_id": creator_telegram_id,
            "track_ids": track_ids,
        }
        return self._post(SERVER_API_URL, self.ROOMS_PATH, payload)
    
    
    def upload_audio_file(self, file_path: str, file_name: str) -> dict:
        body = {"file_name": file_name}
        return self._post_file(AUDIO_STORAGE_API_URL, "/files/", "file", file_path, body)

    async def upload_audio_file_async(self, file_path: str, file_name: str) -> dict:
        return await asyncio.to_thread(self.upload_audio_file, file_path, file_name)

    def delete_audio_file(self, file_name: str) -> dict | None:
        return self._delete(AUDIO_STORAGE_API_URL, f"/files/{file_name}")
