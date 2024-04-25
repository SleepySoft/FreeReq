import traceback

from extra.ChatLLM import LocalChatGLM3
from extra.WebChat import WebChat


def main():
    llm = LocalChatGLM3('')
    llm.async_init_llm()
    web_chat = WebChat(llm)
    web_chat.setup_web_chat()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit(-2)
    finally:
        pass
