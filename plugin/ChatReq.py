import sys
import torch
from typing import Union, List, Dict
from transformers import AutoModel, AutoTokenizer

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton
from PyQt5.QtCore import QThread, pyqtSignal

from FreeReq import RequirementUI, IReqAgent, ReqNode, STATIC_FIELD_CONTENT

# ----------------------------------------------------------------------------------------------------------------------

EMBEDDING_PLUGIN_NAME = 'EmbeddingIndexing'
LLM_DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# The LLM model name could be one of the following or local path:
#   THUDM/chatglm-6b-int4-qe
#   THUDM/chatglm-6b-int4
#   THUDM/chatglm-6b-int8
#   THUDM/chatglm-6b
LLM_MODEL = 'THUDM/chatglm-6b-int4-qe'

PROMPT_TEMPLATE = """已知信息：
{context} 

根据上述已知信息，简洁和专业的来回答用户的问题。如果无法从中得到答案，请说 “根据已知信息无法回答该问题” 或 “没有提供足够的相关信息”，不允许在答案中添加编造成分，答案请使用中文。 问题是：{question}
"""


# ----------------------------------------------------------------------------------------------------------------------

class ChatWindow(QWidget):
    send_message = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.__init_ui()
        self.thread = ChatThread()
        self.send_message.connect(self.thread.handle_input)
        self.thread.append_text.connect(self.append_text)
        self.thread.start()

    def __init_ui(self):
        vbox = QVBoxLayout()
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        vbox.addWidget(self.text_display, 8)

        hbox = QHBoxLayout()
        self.text_input = QLineEdit()
        hbox.addWidget(self.text_input, 4)
        send_button = QPushButton('发送')
        send_button.clicked.connect(self.send)
        hbox.addWidget(send_button, 1)

        vbox.addLayout(hbox, 2)
        self.setLayout(vbox)

        self.setWindowTitle('Chat')
        self.resize(800, 600)

    def send(self):
        text = self.text_input.text()
        if text:
            self.send_message.emit(text)
            self.text_input.clear()

    def append_text(self, text):
        self.text_display.append(text)

    def closeEvent(self, event):
        self.thread.quit()
        self.thread.wait()
        super().closeEvent(event)


def setup_llm():
    try:
        device = torch.device(LLM_DEVICE)
        model = AutoModel.from_pretrained(LLM_MODEL, trust_remote_code=True).half().to(device)
        tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL, trust_remote_code=True)
        return model, tokenizer
    except Exception as e:
        print(e)
        return None, None
    finally:
        pass


class ChatThread(QThread):
    append_text = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.model = None
        self.tokenizer = None
        self.history = []

    def chat_init(self):
        model, tokenizer = setup_llm()
        if model is None or tokenizer is None:
            exit(-2)
        model = model.eval()

        self.model, self.tokenizer = model, tokenizer

    def handle_input(self, text: str):
        text = text.strip()
        if text != '':
            self.append_text.emit(text)

            search_result = main_ui.get_plugin().call_module_function(EMBEDDING_PLUGIN_NAME, 'search_req_nodes', text)
            prompts = ChatThread.generate_llm_prompts(question=text, search_result=search_result)

            response, _ = self.model.chat(
                self.tokenizer,
                prompts,
                history=self.history,
                max_length=10000,
                temperature=2.0
            )
            self.append_text.emit(str(response))

            # for i, (stream_resp, _) in enumerate(self.model.stream_chat(
            #         self.tokenizer,
            #         prompts,
            #         history=self.history,
            #         max_length=10000,
            #         temperature=2.0)):
            #     self.append_text.emit(stream_resp)

            torch.cuda.empty_cache()

    @staticmethod
    def generate_llm_prompts(question: str, search_result: List[ReqNode]) -> str:
        context = '\n'.join([node.get_title() + '\n' + node.get(STATIC_FIELD_CONTENT) for node in search_result])
        return PROMPT_TEMPLATE.replace('{question}', question).replace('{context}', context)


# ----------------------------------------------------------------------------------------------------------------------

chat_window: ChatWindow = None


def on_chat():
    global chat_window
    if chat_window is None:
        chat_window = ChatWindow()
        chat_window.thread.chat_init()
    chat_window.show()


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> Dict[str, str]:
    return {
        'name': 'ChatRequirement',
        'version': '1.0.0.0',
        'tags': 'llm'
    }


def plugin_capacities() -> List[str]:
    return []


# ----------------------------------------------------------------------------------------------------------------------

def req_agent_prepared(req: IReqAgent):
    pass


def after_ui_created(req_ui: RequirementUI):
    global main_ui
    main_ui = req_ui
    chat_button = QPushButton('Chat')
    main_ui.edit_board.layout_plugin_area.addWidget(chat_button)
    chat_button.clicked.connect(on_chat)


# ----------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    app = QApplication(sys.argv)
    chat_window = ChatWindow()
    chat_window.show()
    sys.exit(app.exec_())

