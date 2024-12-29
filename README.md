# mychat
Enhanced Multi-API Chat Application provides a powerful and flexible platform for interacting with multiple AI providers. With its advanced features and user-friendly interface, it is well-suited for both casual and professional use.

Complete code is in mychat.py

Design document is in Design_Document_mychat-latest.txt

cross reference design document is in Design_Document_mychat-improved.txt

How to run:

1) create config.yaml:

Google Gemini:
  api_key: <your_own_key>
  base_url: https://generativelanguage.googleapis.com/v1beta
  model: gemini-2.0-flash-exp
  system_prompt: You are a helpful assistant and also a deep thinking software engineer
    who excels in coming up with innovative and user-friendly software for clients.
  temperature: 1.0
Ollama:
  api_key: ''
  base_url: http://127.0.0.1:11434
  model: granite3.1-dense
  system_prompt: You are a helpful assistant.
  temperature: 1.0
OpenAI:
  api_key: <your_own_key>
  base_url: https://api.openai.com/v1
  model: gpt-4o-mini
  system_prompt: You are a helpful assistant and an expert software developer.
    Be creative.
  temperature: 1.0
active_provider: OpenAI
xAI Grok:
  api_key: <your_own_key>
  base_url: https://api.x.ai/v1
  model: grok-2-1212
  system_prompt: You are a helpful assistant.
  temperature: 1.0

2) execute the code:
   python3 mychat.py
