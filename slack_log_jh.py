
from slack_sdk import WebClient
from idodb_key.slack import slack_token
#현재 슬랙봇은 1개만 생성(추후 봇개수 늘어날 때 수정 필요)
class slack_api:
    """
    슬랙 API 핸들러
    """

    def __init__(self):
        # 슬랙 클라이언트 인스턴스 생성
        self.client = WebClient(slack_token)

    def get_channel_id(self,channel_name,priv_yn = None):
        if priv_yn != None:
            priv_yn = 'private_channel'
        """
        슬랙 채널ID 조회
        """
        # conversations_list() 메서드 호출
        result = self.client.conversations_list(types=priv_yn)
        channels = result.data['channels']
        channel = list(filter(lambda c: c["name"] == channel_name, channels))[0]
        # 채널ID 파싱
        channel_id = channel["id"]
        return channel_id

    def post_thread_message(self, channel_id, text):
        """
        슬랙 채널 내 메세지의 Thread에 댓글 달기
        """
        # chat_postMessage() 메서드 호출
        result = self.client.chat_postMessage(
            channel=channel_id,
            text=text
        )
        return result


def slack_message(channel_name,text):
    id = slack_api().get_channel_id(channel_name,priv_yn='Y')
    slack_api().post_thread_message(id,str(text))
    return print('error_messages to slack!')




