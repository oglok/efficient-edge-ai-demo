Benchmarking instructions/repo can be found here: https://github.com/mlc-ai/llm-perf-bench/tree/main

In order to benchmark, I had to add this folder to the image which is based on a release from dustynv: https://github.com/mlc-ai/mlc-llm/tree/main/python/mlc_chat/cli

I also had to edit benchmark.py in that cli folder to remove the num_shared value from the ChatConfig, the model_lib_path, and verbose=True from the stats function call at the bottom. To call this without any of the above steps, you can run a script like this (this is configured for the vicuna image):

from mlc_chat import ChatConfig, ChatModule

chat_module = ChatModule(
        model="./params",
        device="cuda:0",
        chat_config=ChatConfig(),
    )
output = chat_module.benchmark_generate("What is the meaning of life?", generate_length=256)
print(f"Generated text:\n{output}\n")
print(f"Statistics: {chat_module.stats()}")
