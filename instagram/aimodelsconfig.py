api_key = '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'
models_openai = ['openai/gpt-4.1', 'openai/gpt-4o', 'openai/gpt-4.1-mini', 'openai/gpt-4.1-nano', 'openai/gpt-4o-mini', "openai/o4-mini"]
deepseek = ['deepseek/DeepSeek-R1', 'deepseek/DeepSeek-R1-0528', 'deepseek/DeepSeek-V3-0324']
models_msft= ['microsoft/MAI-DS-R1', 'microsoft/Phi-3.5-MoE-instruct', 'microsoft/Phi-3.5-mini-instruct', 'microsoft/Phi-3.5-vision-instruct',
              'microsoft/Phi-3-medium-128k-instruct', 'microsoft/Phi-3-medium-4k-instruct', 'microsoft/Phi-3-mini-128k-instruct', 'microsoft/Phi-3-mini-4k-instruct',
              'microsoft/Phi-3-small-128k-instruct', 'microsoft/Phi-3-small-8k-instruct', 'microsoft/Phi-4', 'microsoft/Phi-4-mini-instruct',
              'microsoft/Phi-4-mini-reasoning', 'microsoft/Phi-4-multimodal-instruct', 'microsoft/Phi-4-reasoning']
llama = ['meta/Llama-3.2-11B-Vision-Instruct', 'meta/Llama-3.2-90B-Vision-Instruct', 'meta/Llama-3.3-70B-Instruct', 'meta/Llama-4-Maverick-17B-128E-Instruct-FP8'
        'meta/Llama-4-Maverick-17B-128E-Instruct-FP8', 'meta/Llama-4-Scout-17B-16E-Instruct', 'meta/Meta-Llama-3.1-405B-Instruct',
        'meta/Meta-Llama-3.1-8B-Instruct']
grok = ['xai/grok-3', 'xai/grok-3-mini']
ai21jamba = ['ai21-labs/AI21-Jamba-1.5-Large', 'ai21-labs/AI21-Jamba-1.5-Mini']
codestral = ['mistral-ai/Codestral-2501']
cohere = ['cohere/Cohere-command-r-08-2024', 'cohere/Cohere-command-r-plus-08-2024', 'cohere/cohere-command-a']
mistral = ['mistral-ai/Ministral-3B', 'mistral-ai/Mistral-Large-2411', 'mistral-ai/Mistral-Nemo', 'mistral-ai/mistral-medium-2505', 'mistral-ai/mistral-small-2503']
jais = ['core42/jais-30b-chat']

models = models_openai + deepseek + models_msft + llama + grok + ai21jamba + codestral + cohere + mistral + jais
model_configs = [{"model_name": model, "api_key": api_key, "priority": index} for index, model in enumerate(models)]