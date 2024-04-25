import gradio as gr
from typing import Iterable, Union, List
from extra.ChatLLM import ChatLLM


DEFAULT_HEADER_BAR = """<h1 align="center">ChatReq - by Sleepy</h1>"""
DEFAULT_GRADIO_KWARGS = {'server_name': "127.0.0.1", 'server_port': 20000, 'inbrowser': True, 'share': False}


class WebChat:
    def __init__(self, chatllm: Union[ChatLLM, None], header_bar: str = DEFAULT_HEADER_BAR, **gradio_kwargs):
        self.chatllm = chatllm
        self.header_bar = header_bar
        self.gradio_kwargs = {**DEFAULT_GRADIO_KWARGS, **gradio_kwargs}

    def setup_web_chat(self):
        with gr.Blocks() as demo:
            gr.HTML(self.header_bar)
            chat_bot = gr.Chatbot()

            with gr.Row():
                with gr.Column(scale=4):
                    with gr.Column(scale=12):
                        user_input = gr.Textbox(show_label=False, placeholder="Input...", lines=10)
                    with gr.Row():
                        with gr.Column(scale=9):
                            submit_btn = gr.Button("Submit")
                        with gr.Column(scale=1):
                            empty_btn = gr.Button("Clear History")
                with gr.Column(scale=1):
                    max_length = gr.Slider(0, 32768, value=8192, step=1.0, label="Maximum length", interactive=True)
                    top_p = gr.Slider(0, 1, value=0.8, step=0.01, label="Top P", interactive=True)
                    temperature = gr.Slider(0.01, 1, value=0.6, step=0.01, label="Temperature", interactive=True)

            def clear_user_input_and_echo(text: str, conversation):
                return '', conversation + [(WebChat.reformat_text(text), '')]

            submit_btn.click(clear_user_input_and_echo, [user_input, chat_bot], [user_input, chat_bot], queue=False).\
                then(self.__handle_web_chat, [chat_bot, max_length, top_p, temperature], chat_bot)
            empty_btn.click(self.__handle_clear, None, chat_bot, queue=False)

        demo.queue()
        demo.launch(**self.gradio_kwargs)

    def __handle_clear(self):
        if self.chatllm is not None:
            self.chatllm.clear_history()
        # Return None to empty the chatbot
        return None

    def __handle_web_chat(self, conversation, max_length: int, top_p: float, temperature: float) -> Iterable[str]:
        if self.chatllm is not None:
            if self.chatllm.llm_ready:
                new_user_input = conversation[-1][-1]
                for new_token in self.chatllm.chat(new_user_input):
                    if new_token != '':
                        conversation[-1][1] += new_token
                        yield conversation
            else:
                conversation[-1][-1] = 'LLM is not ready.'
                yield conversation
        else:
            yield conversation

    @staticmethod
    def reformat_text(text):
        """copy from https://github.com/GaiZhenbiao/ChuanhuChatGPT/"""

        lines = text.split("\n")
        lines = [line for line in lines if line != ""]
        count = 0
        for i, line in enumerate(lines):
            if "```" in line:
                count += 1
                items = line.split('`')
                if count % 2 == 1:
                    lines[i] = f'<pre><code class="language-{items[-1]}">'
                else:
                    lines[i] = f'<br></code></pre>'
            else:
                if i > 0:
                    if count % 2 == 1:
                        line = line.replace("`", "\\`")
                        line = line.replace("<", "&lt;")
                        line = line.replace(">", "&gt;")
                        line = line.replace(" ", "&nbsp;")
                        line = line.replace("*", "&ast;")
                        line = line.replace("_", "&lowbar;")
                        line = line.replace("-", "&#45;")
                        line = line.replace(".", "&#46;")
                        line = line.replace("!", "&#33;")
                        line = line.replace("(", "&#40;")
                        line = line.replace(")", "&#41;")
                        line = line.replace("$", "&#36;")
                    lines[i] = "<br>" + line
        text = "".join(lines)
        return text


# ----------------------------------------------------------------------------------------------------------------------

def main():
    WebChat(None).setup_web_chat()


if __name__ == '__main__':
    main()
