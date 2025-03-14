#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 11 13:20:16 2025

@author: cuijian
"""

import os
import glob
from openai import OpenAI
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
import chromadb
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain


class Chat:
    instance = None

    def __init__(self):
        openai = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
        llm = ChatOllama(model="llama3.2", temperature=0.7)
        memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
        vectorstore = self.load_vectordb("vector_db", "llama3.2")
        retriever = vectorstore.as_retriever()
        self.model = "llama3.2"
        self.db_name = "vector_db"
        self.conversation_chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever=retriever, memory=memory)
        self.system_message = (
            "You are an expert in answering accurate questions about Insurellm, the Insurance Tech company. "
            "Give brief, accurate answers. If you don't know the answer, say so. Do "
            "not make anything up if"
            "you haven't been provided with relevant context.")

    def split_documents(self,file_path):
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

    def embedding_vectors(self, chunks,db_path,model):
        embeddings = OllamaEmbeddings(model=model)

        vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=db_path)
        print(f"Vectorstore created with {vectorstore._collection.count()} documents")
        return vectorstore

    def load_vectordb(self, db_name, model):
        path = os.path.dirname(__file__)
        db_path = f'{path}/{db_name}'
        if os.path.exists(db_path):
            chroma_client = chromadb.PersistentClient(path=db_path)
            collection_names = chroma_client.list_collections()
            print("Available collections:", collection_names)
            collection = chroma_client.get_collection("langchain")
            embeddings = OllamaEmbeddings(model=model)
            vectorstore = Chroma(client=chroma_client, collection_name="langchain", embedding_function=embeddings)
            return vectorstore
        else:
            file_path = f'{path}/knowledge-base/*'
            chunks = self.split_documents(file_path)
            return self.embedding_vectors(chunks,db_path,model)

    @staticmethod
    def get_instance():
        if not Chat.instance:
            Chat.instance = Chat()
            return Chat.instance
        else:
            return Chat.instance

    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_message}] + history

        messages.append({"role": "user", "content": message})

        response = self.conversation_chain.invoke({"question": message}, stream=True)
        print(response['answer'])
        return response['answer']


__all__ = ['Chat']
