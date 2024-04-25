import sys
import time
import threading
from typing import Iterable
import gradio as gr

import torch
from typing import Union, List, Dict
from transformers import (
    AutoModelForCausalLM,
    AutoModel,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizer,
    PreTrainedTokenizerFast,
    StoppingCriteria,
    StoppingCriteriaList,
    TextIteratorStreamer
)

DEFAULT_DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'


# ======================================================================================================================

def parse_text(text):
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
                lines[i] = "<br>"+line
    text = "".join(lines)
    return text


# ======================================================================================================================

class ChatLLM:
    def __init__(self, model_url: str, on_device: str, max_len: int = 8192):
        self.model_url = model_url
        self.on_device = on_device
        self.llm_ready = False
        self.init_thread = None
        self.lock = threading.Lock()

    def do_init_llm(self) -> bool:
        pass

    def chat(self, text: str) -> Iterable[str]:
        pass

    def clear_history(self) -> bool:
        pass

    def try_init_llm(self) -> bool:
        try:
            if self.do_init_llm():
                self.llm_ready = True
            return self.llm_ready
        except Exception as e:
            print('-' * 75)
            print('LLM init fail:')
            print(e)
            print('-' * 75)
            return False
        finally:
            pass

    def async_init_llm(self):
        with self.lock:
            if self.init_thread is None or not self.init_thread.is_alive():
                self.init_thread = threading.Thread(target=self.__init_wrapper)
                self.init_thread.start()

    def __init_wrapper(self):
        if not self.llm_ready:
            self.try_init_llm()
        with self.lock:
            self.init_thread = None


# ======================================================================================================================

class StopOnTokens(StoppingCriteria):
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        stop_ids = [0, 2]
        for stop_id in stop_ids:
            if input_ids[0][-1] == stop_id:
                return True
        return False


# ======================================================================================================================

class LocalChatGLM3(ChatLLM):
    def __init__(self, model_url: str, on_device: str = DEFAULT_DEVICE):
        super(LocalChatGLM3, self).__init__(model_url, on_device)
        self.history = []
        self.messages = []
        self.model = None
        self.tokenizer = None
        self.chat_thread = None

    def do_init_llm(self) -> bool:
        if self.llm_ready:
            return True
        device = torch.device(self.on_device)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_url, trust_remote_code=True).half().to(device).eval()
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_url, trust_remote_code=True)
        return True

    def chat(self, text: str):
        if not self.llm_ready:
            return
        if self.chat_thread is not None:
            return

        stop = StopOnTokens()
        self.history.append([text, ''])
        self.messages.append({"role": "user", "content": text})
        self.messages.append({"role": "assistant", "content": ""})

        model_inputs = self.tokenizer.apply_chat_template(
            self.messages, add_generation_prompt=True, tokenize=True, return_tensors="pt").\
            to(next(self.model.parameters()).device)
        streamer = TextIteratorStreamer(self.tokenizer, timeout=60, skip_prompt=True, skip_special_tokens=True)

        generate_kwargs = {
            "input_ids": model_inputs,
            "streamer": streamer,
            "max_new_tokens": 8192,
            "do_sample": True,
            "top_p": 0.8,
            "temperature": 0.8,
            "stopping_criteria": StoppingCriteriaList([stop]),
            "repetition_penalty": 1.2,
        }

        self.chat_thread = threading.Thread(target=self.__chat_thread, kwargs=generate_kwargs)
        self.chat_thread.start()

        for new_token in streamer:
            if new_token != '':
                self.history[-1][-1] += new_token
                self.messages[-1]["content"] += new_token
                yield self.history

    def clear_history(self) -> bool:
        if self.chat_thread is not None:
            return False
        self.history.clear()
        self.messages.clear()
        return True

    def __chat_thread(self, kwargs):
        print('Generate thread starts.')
        self.model.generate(kwargs)
        self.chat_thread = None
        print('Generate thread finished.')


class LocalChatGLM2(ChatLLM):
    def __init__(self, model_url: str = '"THUDM/chatglm2-6b"', on_device: str = DEFAULT_DEVICE):
        super(LocalChatGLM2, self).__init__(model_url, on_device)
        self.model = None
        self.tokenizer = None
        self.history = []
        self.history2 = []      # 这两个History一样吗？
        self.past_key_values = None

    def do_init_llm(self) -> bool:
        device = torch.device(self.on_device)
        self.model = AutoModel.from_pretrained(self.model_url, trust_remote_code=True).half().to(device).eval()
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_url, trust_remote_code=True)
        return True

    def chat(self, text: str):
        if not self.llm_ready:
            return
        self.history.append((text, ''))

        for response, self.history2, self.past_key_values in self.model.stream_chat(
                self.tokenizer, text, self.history2, past_key_values=self.past_key_values,
                return_past_key_values=True, max_length=8196, top_p=0.8, temperature=0.8):
            self.history[-1] = (parse_text(text), parse_text(response))
            yield self.history

    def clear_history(self) -> bool:
        self.history = []
        self.history2 = []
        self.past_key_values = None
        return True


# ----------------------------------------------------------------------------------------------------------------------

def main():
    chat = LocalChatGLM3('')


if __name__ == '__main__':
    main()
