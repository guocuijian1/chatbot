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
    model = "deepseek-r1:1.5b"
    system_message = (
        """
        你是Insurellm公司的专家。以下是你的指导原则：
        如果有人问“你是谁？”，解释你代表Insurellm并提供相关背景信息。
        如果有人问“公司名称是什么？”，从知识库中检索文档类型为“公司”的信息。
        如果有人询问产品，提供来自知识库中文档类型为“产品”的信息。
        如果有人询问职业机会，从知识库中检索文档类型为“公司”的信息。
        如果有人询问合同，提供来自知识库中文档类型为“合同”的详细信息。
        如果有人询问员工，从知识库中检索文档类型为“员工”的信息。
        其它情况，请从知识库中搜索后回答，若搜索不到，请用户确认
        请始终用中文回答问题
        """
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
    def split_documents_for_given_dir(cls, target_dir):
        text_loader_kwargs = {"encoding": "utf-8"}

        documents = []
        doc_type = os.path.basename(target_dir)
        loader = DirectoryLoader(target_dir, glob="**/*.md", loader_cls=TextLoader, loader_kwargs=text_loader_kwargs)
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
    def load_given_db(cls, target_file_dir):
        current_file_dir = os.path.dirname(__file__)
        db_path = f'{current_file_dir}/{cls.db_name}'
        file_path = f'{current_file_dir}/knowledge-base/{target_file_dir}'
        chunks = cls.split_documents_for_given_dir(file_path)
        embeddings = OllamaEmbeddings(model=cls.model)

        vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=db_path)
        print(f"Vectorstore created with {vectorstore._collection.count()} documents")

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

    @classmethod
    def new_topic(cls):
        try:
            cls.memory.clear()
            return "对话上下文已经被清楚"
        except Exception as e:
            return f"清除对话上下文过程中出现错误：{e}"


__all__ = ['ChatUtil', 'Chat']
