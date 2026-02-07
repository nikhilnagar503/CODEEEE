import tiktoken


def get_tokenizer(Model : str):
    try :
         encoding  = tiktoken.encoding_for_model(Model)
         return encoding.encode 
    except Exception:
        encoding  = tiktoken.get_encoding("cl100k_base")

        return encoding.encode
    
def count_tokens(text : str , Model : str) -> int :
    tokenizer = get_tokenizer(Model)
    
    if tokenizer :
        len(tokenizer(text))
        
    return estimate_token(text)
    
def estimate_token(text:str) -> int :
    return  max(1, len(text) //4)  # rough estimate 4 characters per token 