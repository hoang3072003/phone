import os
# from dotenv import load_dotenv
from RAG import RAG
def fetch_data(collection):
    data = collection.find({})  
    phones = []
    for item in data:
        phones.append({
            "name": item.get("name"),
            "price": item.get("price"),
            "specs_special": item.get("specs_special"),
            "product_promotion": item.get("product_promotion"),
            "colors": item.get("colors")
        })
    return {"phones": phones}

rag = RAG()
phones_data = fetch_data(rag.collection)

