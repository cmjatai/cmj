from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory.buffer import ConversationBufferMemory
from langchain_community.llms.huggingface_hub import HuggingFaceHub
from langchain_community.vectorstores import FAISS
from sentence_transformers import SentenceTransformer


def create_vectorstore(chunks):
    embeddings = SentenceTransformer("WhereIsAI/UAE-Large-V1")
    vectorstore = FAISS.from_texts(texts=chunks, embedding=embeddings)

    return vectorstore


def create_conversation_chain(vectorstore):
    llm = HuggingFaceHub(repo_id='google/flan-t5-large',
                         model_kwargs={"max_length": 512, "temperature": 0.1})

    memory = ConversationBufferMemory(
        memory_key='chat_history', return_messages=True)

    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )

    return conversation_chain
