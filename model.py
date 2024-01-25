import requests

def complete(text:str,key:str,temperature:float=0.7,max_tokens:int=256,stop:list[str]=[],model:str='pai-001-light')->str:
    headers = {
        'Authorization': key,
        'Content-Type': 'application/json',
    }

    json_data = {
        'model': model,
        'prompt': text,
        'temperature': temperature,
        'max_tokens': max_tokens,
        'stop': stop,
    }

    response = requests.post('https://api.pawan.krd/v1/completions', headers=headers, json=json_data)

    try:
        return response.json()["choices"][0]["text"]
    except Exception as e:
        print(str(e))
        print(response.text)