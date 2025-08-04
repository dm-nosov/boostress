import requests


class AgentApi:

    @staticmethod
    def _build_url(url, token, method):
        return "{}/{}/{}".format(url, token, method)

    @classmethod
    def create(cls, url, token, chat_id, res_url, endpoint_label=None, resource_type='photo', caption=None):
        if resource_type == 'video':
            method = "sendVideo"
            media_key = "video"
        else:
            method = "sendPhoto"
            media_key = "photo"
        
        post_url = cls._build_url(url, token, method)
        payload = {"chat_id": chat_id, media_key: res_url}
        
        if caption:
            payload["caption"] = caption
        elif endpoint_label:
            payload["caption"] = "@" + endpoint_label
            
        r = requests.post(post_url, json=payload)

        if r.status_code == 200:
            return r.json()["result"]["message_id"]

        return 0

    @classmethod
    def forward(cls, url, token, chat_id, other_endpoint_ext_id, res_id):
        post_url = cls._build_url(url, token, "forwardMessage")
        r = requests.post(post_url,
                          json={"chat_id": chat_id, "from_chat_id": other_endpoint_ext_id, "message_id": res_id})

        if r.status_code == 200:
            return r.json()["result"]["message_id"]

        return 0
