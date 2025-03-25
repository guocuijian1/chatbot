#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 11 13:20:16 2025

@author: cuijian
"""

import os
import glob
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
import chromadb
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain


class ChatUtil:
    instance = None
    llm = ChatOllama(model="llama3.2", temperature=0.7)
    db_name = "vector_db"
    model = "llama3.2"
    system_message = (
        "You are an expert in answering accurate questions about Insurellm, the Insurance Tech company. "
        "Give brief answers. If you don't know the answer, use your knowledge to generate one . "
        "please return the following information in HTML format"
    )

    @classmethod
    def split_documents(cls, file_path):
        folders = glob.glob(file_path)
        text_loader_kwargs = {"encoding": "utf-8"}

        documents = []
        for folder in folders:
            doc_type = os.path.basename(folder)
            loader = DirectoryLoader(folder, glob="**/*.md", loader_cls=TextLoader, loader_kwargs=text_loader_kwargs)
            folder_docs = loader.load()
            for doc in folder_docs:
                doc.metadata["doc_type"] = doc_type
                documents.append(doc)

        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=True)
        chunks = text_splitter.split_documents(documents)
        return chunks

    @classmethod
    def load_vectordb(cls):
        path = os.path.dirname(__file__)
        db_path = f'{path}/{cls.db_name}'
        if os.path.exists(db_path):
            chroma_client = chromadb.PersistentClient(path=db_path)
            collection_names = chroma_client.list_collections()
            print("Available collections:", collection_names)
            collection = chroma_client.get_collection("langchain")
            embeddings = OllamaEmbeddings(model=cls.model)
            vectorstore = Chroma(client=chroma_client, collection_name="langchain", embedding_function=embeddings)
            return vectorstore
        else:
            file_path = f'{path}/knowledge-base/*'
            chunks = cls.split_documents(file_path)
            embeddings = OllamaEmbeddings(model=cls.model)

            vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=db_path)
            print(f"Vectorstore created with {vectorstore._collection.count()} documents")
            return vectorstore

    @classmethod
    def format_html(cls, message):
        if not message:
            return message

        return message.replace("\n", "<br/>")


class Chat:
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    vectorstore = ChatUtil.load_vectordb()
    retriever = vectorstore.as_retriever()
    conversation_chain = ConversationalRetrievalChain.from_llm(llm=ChatUtil.llm, retriever=retriever, memory=memory)

    @classmethod
    def chat(cls, message, history):
        messages = [{"role": "system", "content": ChatUtil.system_message}] + history
        messages.append({"role": "user", "content": message})

        response = cls.conversation_chain.invoke({"question": message})
        answer = ChatUtil.format_html(response['answer'])
        print(answer)
        return answer


__all__ = ['ChatUtil', 'Chat']
