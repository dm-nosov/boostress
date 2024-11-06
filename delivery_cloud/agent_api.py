import requests


class AgentApi:

    @staticmethod
    def _build_url(url, token, method):
        return "{}/{}/{}".format(url, token, method)

    @classmethod
    def create(cls, url, token, chat_id, res_url, endpoint_label=None):
        post_url = cls._build_url(url, token, "sendPhoto")
        if endpoint_label:
            r = requests.post(post_url, json={"chat_id": chat_id, "photo": res_url, "caption": "@" + endpoint_label})
        else:
            r = requests.post(post_url, json={"chat_id": chat_id, "photo": res_url})

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
