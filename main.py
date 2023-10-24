import openai
import streamlit as st
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.vectorstore import VectorStoreRetriever


st.title("Chat with my custom chatbot!")

openai.api_key = st.secrets["OPENAI_API_KEY"]

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=message["avatar"]):
        st.markdown(message["content"])


@st.cache_resource(ttl=3600)  # 1h
def get_retriever():
    vectorstore_path = "./vectorstore"
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.load_local(vectorstore_path, embeddings)
    st.write("get_retriever 함수 실행")

    return vectorstore.as_retriever()


@st.cache_resource(ttl=3600, hash_funcs={VectorStoreRetriever: lambda x: x.tags})
def get_chain(retriever):
    template = """You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise. Be sure to answer in Korean and use polite language.

    Question: {question}
    Context: {context}
    Answer:
    """
    prompt = ChatPromptTemplate.from_template(template)
    model = ChatOpenAI(temperature=0.5)
    qa_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | model
    )

    return qa_chain


retriever = get_retriever()
chain = get_chain(retriever)

user_avatar = "😊"
assistant_avatar = "🤖"

if query := st.chat_input("Send a message"):
    st.session_state.messages.append({"role": "user", "content": query, "avatar": user_avatar})
    with st.chat_message("user", avatar=user_avatar):
        st.markdown(query)

    with st.chat_message("assistant", avatar=assistant_avatar):
        message_placeholder = st.empty()
        full_response = ""

        for response in chain.stream(query):
            full_response += response.content
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response, "avatar": assistant_avatar})