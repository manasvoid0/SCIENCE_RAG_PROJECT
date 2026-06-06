from fastapi import FastAPI, HTTPException  # <--- Added HTTPException here
from pydantic import BaseModel
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# =========================================================================
# 1. INITIALIZE THE FASTAPI APP
# =========================================================================
app = FastAPI(title="10th Grade Science AI Tutor")

class UserRequest(BaseModel):
    question: str

# =========================================================================
# 2. LOAD THE RAG PIPELINE
# =========================================================================
INDEX_DIR = "faiss_science_index"

print("Booting up the AI Engine...")
embeddings = OllamaEmbeddings(model="nomic-embed-text")
db = FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
llm = OllamaLLM(model="qwen2.5:7b")

system_prompt = (
    "You are a helpful 10th-grade science tutor.\n"
    "Answer the user's question using ONLY the provided text from the textbook.\n"
    "If the answer cannot be found in the text, say 'I am sorry, but that information is not in the textbook.'\n"
    "Do not invent facts or use outside knowledge.\n\n"
    "Textbook Context:\n{context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

retriever = db.as_retriever(search_kwargs={"k": 3})
combine_docs_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, combine_docs_chain)
print("Engine Ready! Web server is live.")

# =========================================================================
# 3. CREATE THE API ENDPOINT (Now with Error Catching!)
# =========================================================================

@app.post("/ask")
def ask_tutor(request: UserRequest):
    try:
        # We TRY to do the normal process...
        response = rag_chain.invoke({"input": request.question})
        return {"answer": response["answer"]}
        
    except Exception as e:
        # IF IT FAILS, catch the exact error and print it to the web browser!
        print(f"CRASH REPORT: {str(e)}")
        raise HTTPException(status_code=500, detail=f"The AI Engine Crashed: {str(e)}")