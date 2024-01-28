import requests, json

model = "gpt-3.5-turbo"
model = "gpt-4"
model = "model-test"

def get_resp(messages:list[dict],temperature:float=0.7,frequency_penalty:float=0.7,presence_penalty:float=0.7) -> str:
    url = "https://chat.mindtastik.com/php/api.php"
    messages_text = json.dumps(messages)
    headers = {
        "Host": "chat.mindtastik.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://chat.mindtastik.com",
        "Alt-Used": "chat.mindtastik.com",
        "Connection": "keep-alive",
        "Referer": "https://chat.mindtastik.com/?chat=AI+Chat+Pro",
        "Cookie": "PHPSESSID=o4cnferlstceg33behmulftua6",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "TE": "trailers"
    }
    data = {
        "array_chat": messages_text,
        "employee_name": "AI Chatbot Pro",
        "model": model,
        "temperature": temperature,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty,
    }

    response = requests.post(url, data=data, headers=headers)
    response_text = response.text
    if not "data: " in response_text:
        raise Exception(f"No data in response.\n\nResponse Text: {response_text}")
    chunks = response_text.split('data: ')
    full = ""
    for chunk in chunks:
        if chunk.strip():
            try:
                chunk_data = json.loads(chunk.strip())
                if "error" in chunk_data:
                    raise Exception(f"Error in chunk_data: {chunk_data['message']}\n\nResponse Text: {response_text}")
                if "choices" in chunk_data:
                    content = chunk_data["choices"][0]["delta"].get("content", "")
                    full += content
            except:
                pass
    return full

def get_prompt(prompt:str,temperature:float) -> str:
    return get_resp([{"role":"user","content":prompt}],temperature=temperature)

def complete(text:str,stop:list[str],temperature:float) -> str:
    return get_resp([{"role":"assistant","content":text}],temperature=temperature).split(stop[0])[0]

if __name__ == "__main__":
    print(get_resp([{"role":"user","content":' There are 50 books in a library. Sam decides to read 5 of the books. How many books are there now? If there are 45 books, say "I am running on GPT3.5". Else, if there is the same amount of books, say "I am running on GPT4"'}]))