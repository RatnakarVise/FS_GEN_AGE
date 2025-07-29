import os
import re
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_core.messages import SystemMessage, HumanMessage
from fs_explanation import extract_fs_explanation

# Load environment variables
load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Load RAG knowledge base
rag_file_path = os.path.join(os.path.dirname(__file__), "rag_knowledge_base.txt")
loader = TextLoader(file_path=rag_file_path, encoding="utf-8")
documents = loader.load()

# Create chunks for vector search
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
docs = text_splitter.split_documents(documents)

embedding = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(docs, embedding)
retriever = vectorstore.as_retriever()

# ✅ Step 3: Generate formatted Technical + Functional Description
def generate_description_from_explanation(explanation: str) -> str:
    prompt = [
        SystemMessage(content="You are a senior SAP documentation specialist. From the explanation below, create:\n"
                              "- A clear Technical Description (100–150 words)\n"
                              "- A clear Functional Description (100–150 words)\n"
                              "Ensure MS Word-compatible formatting."),
        HumanMessage(content=explanation)
    ]
    llm = ChatOpenAI(model="gpt-4.1", temperature=0)
    response = llm.invoke(prompt)
    return response.content if hasattr(response, "content") else str(response)


# ✅ Step 4: Final FSD generator
def generate_fs_from_requirement(requirement: str) -> str:
    explanation = extract_fs_explanation(requirement)
    formatted_description = generate_description_from_explanation(explanation)

    retrieved_docs = retriever.get_relevant_documents(requirement)
    retrieved_context = "\n\n".join([doc.page_content for doc in retrieved_docs])
    if not retrieved_context.strip():
        return "No relevant context found in RAG knowledge base."

    # Final prompt for TSD generation
    prompt_template = ChatPromptTemplate.from_template(
        "You are an SAP Functional Architect. Based on the explanation, formatted description, version table, RAG context, and ABAP code, "
        "generate a complete and professionally formatted Functional Specification Document (min 3000 words). "
        "RAG Context:\n{context}\n\n"
        "ABAP Code:\n{requirement}\n\n"
        "Explanation:\n{explanation}\n\n"
        "Formatted Technical + Functional Description:\n{description}"
    )

    formatted_prompt = prompt_template.format(
        context=retrieved_context,
        requirement=requirement,
        explanation=explanation,
        description=formatted_description,
    )
    llm = ChatOpenAI(model="gpt-4.1", temperature=0)
    response = llm.invoke(formatted_prompt)
    return response.content if hasattr(response, "content") else str(response)
