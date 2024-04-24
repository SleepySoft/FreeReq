import sys
import time
import threading
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


class ChatLLM:
    def __init__(self, model_url: str, on_device: str):
        self.model_url = model_url
        self.on_device = on_device
        self.llm_ready = False
        self.init_thread = None
        self.lock = threading.Lock()

    def do_init_llm(self) -> bool:
        pass

    def chat(self, text: str):
        pass

    def clear_history(self):
        pass

    def try_init_llm(self) -> bool:
        try:
            if self.do_init_llm():
                self.llm_ready = True
            return self.llm_ready
        except Exception as e:
            print(e)
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


class StopOnTokens(StoppingCriteria):
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        stop_ids = [0, 2]
        for stop_id in stop_ids:
            if input_ids[0][-1] == stop_id:
                return True
        return False


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
        self.model = AutoModelForCausalLM.from_pretrained(self.model_url, trust_remote_code=True).half().to(device)
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
        self.messages.append({"role": "assistant", "content": text})

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

    def clear_history(self):
        if self.chat_thread is not None:
            return
        self.history.clear()
        self.messages.clear()

    def __chat_thread(self, kwargs):
        print('Generate thread starts.')
        self.model.generate(kwargs)
        self.chat_thread = None
        print('Generate thread finished.')


# ----------------------------------------------------------------------------------------------------------------------

def main():
    chat = LocalChatGLM3('')


if __name__ == '__main__':
    main()
