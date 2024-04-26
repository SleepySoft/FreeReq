import torch
import threading
from typing import Iterable

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
DEFAULT_CHAT_PARAMETER = {
    'max_length': 8192,
    'top_p': 0.8,
    'temperature': 0.8
}


# ======================================================================================================================

class ChatLLM:
    """
    Specify a unified interface for large language model chat.
    """

    CHAT_STYLE_NONE = 0                 # Empty
    CHAT_STYLE_SENTENCE = 1             # Reply to a continuously growing string
    CHAT_STYLE_PER_TOKEN = 2            # Reply a token each time
    CHAT_STYLE_FULL_REPLY = 3           # Block and return all replies at once

    def __init__(self, model_url: str, on_device: str):
        self.model_url = model_url
        self.on_device = on_device
        self.llm_ready = False
        self.chat_hook = None
        self.init_thread = None
        self.lock = threading.Lock()
        self.chat_parameters = DEFAULT_CHAT_PARAMETER.copy()

    def chat_style(self) -> int:
        """
        Override this function to specify chat style. See the comments in the enumeration declaration.
        :return: One of [CHAT_STYLE_NONE, CHAT_STYLE_SENTENCE, CHAT_STYLE_PER_TOKEN, CHAT_STYLE_FULL_REPLY]
        """
        return ChatLLM.CHAT_STYLE_NONE

    def do_init_llm(self) -> bool:
        """
        Override this function to initialize llm.
        :return: True if initialization is successful else False.
        """
        pass

    def do_chat(self, text: str) -> Iterable[str]:
        """
        Override this function to implement llm sync chat. The return value should match the chat_style() returns.
        :param text: User input.
        :return: The generator generated by yield.
        """
        pass

    def clear_history(self) -> bool:
        """
        Override this function to clear llm chat history.
        :return: None
        """
        pass

    # ----------------- Not have to override the following functions -----------------

    def chat(self, text: str):
        try:
            if not self.llm_ready:
                yield 'LLM is not ready.'
                return
            if self.chat_hook is not None:
                text = self.chat_hook(text)
            yield from self.do_chat(text)
        except Exception as e:
            yield f'Error: {str(e)}'
            return
        finally:
            pass

    def set_chat_hook(self, hook):
        """
        Set up chat hooks to process user input before submitting it to LLM.
        Hook function accepts user input and return a processed text for LLM.
        :param hook: Hook function
        :return: None
        """
        self.chat_hook = hook

    def update_chat_parameters(self, **update_param):
        """
        Parameters reference to DEFAULT_CHAT_PARAMETER
        :param update_param: The parameters that need to be updated
        :return: None
        """
        self.chat_parameters.update(update_param)

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
            print(f'Loading LLM: {self.model_url}')
            self.try_init_llm()
            print(f'Loading LLM: {self.model_url} - Done')
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

    def chat_style(self) -> int:
        return ChatLLM.CHAT_STYLE_SENTENCE

    def do_init_llm(self) -> bool:
        if self.llm_ready:
            return True
        # device = torch.device(self.on_device)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_url, trust_remote_code=True, device_map='auto')
        # self.model = AutoModelForCausalLM.from_pretrained(
        #   self.model_url, trust_remote_code=True, device_map='auto').half().to(device).eval()
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
                yield self.messages[-1]["content"]

    def clear_history(self) -> bool:
        if self.chat_thread is not None:
            return False
        self.history.clear()
        self.messages.clear()
        return True

    def __chat_thread(self, **kwargs):
        print('Generate thread starts.')
        self.model.generate(**kwargs)
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

    def chat_style(self) -> int:
        return ChatLLM.CHAT_STYLE_SENTENCE

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
            self.history[-1] = (text, response)
            yield response

    def clear_history(self) -> bool:
        self.history = []
        self.history2 = []
        self.past_key_values = None
        return True


class OnlineChatOpenAI(ChatLLM):
    START_MESSAGE = [
            {
                "role": "system",
                "content": "Follow the user's instructions carefully. Respond using markdown.",
            }
        ]

    def __init__(self, model_url: str, model_selection: str, api_key: str = 'EMPTY'):
        super(OnlineChatOpenAI, self).__init__(model_url, '')
        self.model_selection = model_selection
        self.api_key = api_key
        self.client = None
        self.messages = list(OnlineChatOpenAI.START_MESSAGE)

    def chat_style(self) -> int:
        return ChatLLM.CHAT_STYLE_PER_TOKEN

    def do_init_llm(self) -> bool:
        # openai library is optional.
        from openai import OpenAI
        self.client = OpenAI(api_key=self.api_key)
        self.llm_ready = True
        return True

    def do_chat(self, text: str) -> Iterable[str]:
        self.messages.append({
            "role": "user",
            "content": text
        })
        response = self.client.chat.completions.create(
            model=self.model_selection,
            messages=self.messages,
            stream=True,
            max_tokens=self.chat_parameters.get('max_length', 256),
            temperature=self.chat_parameters.get('temperature', 0.8),
            presence_penalty=self.chat_parameters.get('presence_penalty', 1.1),
            top_p=self.chat_parameters.get('top_p', 0.8)
        )

        self.messages.append({
            "role": "system",
            "content": ""
        })
        if response:
            for chunk in response:
                delta_content = chunk.choices[0].delta.content
                self.messages[-1]['content'] += delta_content
                yield delta_content
        else:
            yield f"Error: {response.status_code}"

    def clear_history(self) -> bool:
        self.messages = list(OnlineChatOpenAI.START_MESSAGE)
        return True


# ----------------------------------------------------------------------------------------------------------------------

def main():
    chat = LocalChatGLM3('')


if __name__ == '__main__':
    main()
