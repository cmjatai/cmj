import os
import re
import google.generativeai as genai

from pypdf import PdfReader
from chromadb import Documents, EmbeddingFunction, Embeddings
from dotenv import load_dotenv

from typing import List

import chromadb

load_dotenv()

#pip install google-generativeai
#pip install pypdf
#pip install chromadb
#pip install grpcio-status==1.67.1 grpcio==1.67.1

gemini_api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)


class GeminiEmbeddingFunction(EmbeddingFunction):
    """
    Custom embedding function using the Gemini AI API for document retrieval.

    This class extends the EmbeddingFunction class and implements the __call__ method
    to generate embeddings for a given set of documents using the Gemini AI API.

    Parameters:
    - input (Documents): A collection of documents to be embedded.

    Returns:
    - Embeddings: Embeddings generated for the input documents.
    """
    def __call__(self, input: Documents) -> Embeddings:
        if not gemini_api_key:
            raise ValueError("Gemini API Key not provided. Please provide GEMINI_API_KEY as an environment variable")
        genai.configure(api_key=gemini_api_key)
        #model = 'models/text-multilingual-embedding-002'
        model = 'models/text-embedding-004'
        title = "Custom query"
        embed = genai.embed_content(model=model,
                                   content=input,
                                   task_type="retrieval_document",
                                   title=title)["embedding"]

        return embed



def load_pdf(file_path):
    """
    Reads the text content from a PDF file and returns it as a single string.

    Parameters:
    - file_path (str): The file path to the PDF file.

    Returns:
    - str: The concatenated text content of all pages in the PDF.
    """
    # Logic to read pdf
    reader = PdfReader(file_path)

    # Loop over each page and store it in a variable
    text = ""
    for page in reader.pages:
        text += page.extract_text()

    return text

# replace the path with your file path
pdf_text = load_pdf(file_path="data/ed_814.pdf")

def split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200):
    chunks = []
    i = 0
    while i < len(text):
        chunk_size_local = chunk_size
        while len(text) > i+chunk_size_local and text[i+chunk_size_local] != ' ':
            chunk_size_local += 1

        chunks.append(text[i:i+chunk_size_local])
        i += chunk_size_local - chunk_overlap

        while 0 < i < len(text) and text[i] != ' ':
            i -= 1

    return chunks

chunked_text = split_text(text=pdf_text)

def create_chroma_db(documents:List, path:str, name:str):
    """
    Creates a Chroma database using the provided documents, path, and collection name.

    Parameters:
    - documents: An iterable of documents to be added to the Chroma database.
    - path (str): The path where the Chroma database will be stored.
    - name (str): The name of the collection within the Chroma database.

    Returns:
    - Tuple[chromadb.Collection, str]: A tuple containing the created Chroma Collection and its name.
    """
    chroma_client = chromadb.PersistentClient(path=path)
    db = chroma_client.create_collection(name=name, embedding_function=GeminiEmbeddingFunction())

    for i, d in enumerate(documents):
        db.add(documents=d, ids=str(i))

    return db, name


def load_chroma_collection(path, name):
    """
    Loads an existing Chroma collection from the specified path with the given name.

    Parameters:
    - path (str): The path where the Chroma database is stored.
    - name (str): The name of the collection within the Chroma database.

    Returns:
    - chromadb.Collection: The loaded Chroma Collection.
    """
    chroma_client = chromadb.PersistentClient(path=path)
    db = chroma_client.get_collection(name=name, embedding_function=GeminiEmbeddingFunction())
    return db

if os.path.exists('old/rag/contents/chroma.sqlite3'):
    db = load_chroma_collection(path="old/rag/contents", name="rag_experiment")
else:
    db, name = create_chroma_db(
        documents=chunked_text,
        path="old/rag/contents", #replace with your path
        name="rag_experiment")


def get_relevant_passage(query, db, n_results):
    passage = db.query(query_texts=[query], n_results=n_results)['documents'][0]
    return passage

def make_rag_prompt(query, relevant_passage):
    escaped = relevant_passage.replace("'", "").replace('"', "").replace("\n", " ")
    prompt = ("""Você é um bot útil e informativo que responde \
              a perguntas usando contexto de referência \
              incluída abaixo. Certifique-se de responder em uma \
              frase completa, sendo abrangente, \
              incluindo todas as informações de contexto relevantes. \
              No entanto, você está falando para um público não técnico, \
              então certifique-se de quebrar conceitos complicados e \
              adotar um tom amigável e coloquial. \
              Se a passagem for irrelevante para a resposta, \
              você pode ignorá-la.

    PERGUNTA: '{query}'

    CONTEXTO: '{relevant_passage}'

    ANSWER:
    """).format(query=query, relevant_passage=escaped)

    return prompt


def generate_answer(db, query):
    generation_config = {
      "temperature": 0.3,
      "top_p": 0.95,
      "top_k": 40,
      "max_output_tokens": 8192,
      "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
      model_name="gemini-2.0-flash-exp",
      generation_config=generation_config,
    )

    relevant_text = get_relevant_passage(query, db, n_results=5)
    prompt = make_rag_prompt(query,
                             relevant_passage="".join(relevant_text))

    answer = model.generate_content(prompt)
    return answer.text


query = "quais representantes eclisiásticos e/ou pastores estiveram na posse?"

response = generate_answer(db, query)
print(response)
