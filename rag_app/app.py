import os  # Imports the operating system library to check for files on your computer

# =========================================================================
# 1. THE IMPORTS (Loading our tools)
# =========================================================================

from langchain_community.document_loaders import PyMuPDFLoader  # Loads the fast PyMuPDF tool to read the textbook
from langchain_text_splitters import RecursiveCharacterTextSplitter  # Loads the tool to chop text into smaller chunks
from langchain_community.vectorstores import FAISS  # Loads FAISS, our local math search engine database
from langchain_ollama import OllamaEmbeddings, OllamaLLM  # Loads the tools to connect Python to your Ollama models
from langchain_classic.chains import create_retrieval_chain  # Loads the tool to connect the search engine to the AI
from langchain_classic.chains.combine_documents import create_stuff_documents_chain  # Loads the tool to stuff text into the prompt
from langchain_core.prompts import ChatPromptTemplate  # Loads the tool to format our strict rules and questions
from tqdm import tqdm  # Loads the progress bar visualizer

INDEX_DIR = "faiss_science_index"  # Creates a variable to store the exact name of our database folder

# =========================================================================
# PHASE 1 & 2: THE "MATH" PHASE (Data Preparation)
# =========================================================================

if not os.path.exists(INDEX_DIR):  # Checks if the database folder already exists on your hard drive
    print("--- Step 1: Processing your textbook PDF... ---")  # Prints a status message to the terminal
    
    loader = PyMuPDFLoader("10th_science_book.pdf")  # Tells the PyMuPDF tool exactly which file to open
    docs = []  # Creates an empty list to hold the text of the pages
    
    print("Extracting text page-by-page:")  # Prints a status message
    for page in tqdm(loader.lazy_load(), desc="Reading Pages"):  # Loops through the book page-by-page with a loading bar
        docs.append(page)  # Adds the text of the current page into our 'docs' list
        
    print(f"\nSuccess: Loaded {len(docs)} pages.")  # Prints how many pages were successfully loaded

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)  # Sets the rules for chopping the text (1000 chars, 200 overlap)
    chunks = text_splitter.split_documents(docs)  # Actually chops the loaded pages into smaller chunks
    print(f"Success: Split book into {len(chunks)} pieces.")  # Prints how many pieces the book was chopped into

    print("\n--- Step 2: Creating mathematical embeddings via Ollama... ---")  # Prints a status message
    embeddings = OllamaEmbeddings(model="nomic-embed-text")  # Tells Ollama to wake up the 'nomic-embed-text' math model
    
    batch_size = 25  # Sets a rule to process the math 25 chunks at a time
    
    db = FAISS.from_documents(chunks[:batch_size], embeddings)  # Gives FAISS the first 25 chunks to initialize the database
    
    for i in tqdm(range(batch_size, len(chunks), batch_size), desc="Calculating Vectors"):  # Loops through the remaining chunks with a loading bar
        batch = chunks[i : i + batch_size]  # Grabs the next 25 chunks
        db.add_documents(batch)  # Does the math and adds those 25 chunks to the FAISS database
    
    db.save_local(INDEX_DIR)  # Saves the finished FAISS database securely to your hard drive
    print(f"\nSuccess: Vector database saved to '{INDEX_DIR}' folder.")  # Prints a success message

else:  # If the database folder ALREADY exists (meaning we ran this before)
    print("--- Vector database found on disk! Skipping processing step. ---")  # Prints a status message
    embeddings = OllamaEmbeddings(model="nomic-embed-text")  # Wakes up the 'nomic-embed-text' model again
    db = FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)  # Instantly loads the saved database from your hard drive


# =========================================================================
# PHASE 3 & 4: THE "THINKING" PHASE (Talking to Qwen 2.5)
# =========================================================================

print("\n--- Step 3: Initializing Qwen 2.5 via Ollama... ---")  # Prints a status message
llm = OllamaLLM(model="qwen2.5:7b")  # Wakes up the massive Qwen 2.5 brain model for thinking

system_prompt = (  # Creates a variable to hold the strict rules for the AI
    "You are a helpful 10th-grade science tutor.\n"  # Tells the AI its personality
    "Answer the user's question using ONLY the provided text from the textbook.\n"  # Sets a strict rule to only use the book
    "If the answer cannot be found in the text, say 'I am sorry, but that information is not in the textbook.'\n"  # Gives it an escape route
    "Do not invent facts or use outside knowledge.\n\n"  # Prevents it from hallucinating or making things up
    "Textbook Context:\n{context}"  # Creates a placeholder where we will inject the 3 matching paragraphs
)

prompt = ChatPromptTemplate.from_messages([  # Builds the final template that will be sent to the AI
    ("system", system_prompt),  # Adds the strict rules we just wrote above
    ("human", "{input}"),  # Adds a placeholder for your actual question
])

retriever = db.as_retriever(search_kwargs={"k": 3})  # Turns FAISS into a search engine and tells it to find the 3 best paragraphs

combine_docs_chain = create_stuff_documents_chain(llm, prompt)  # Creates a mini-pipeline to stuff the paragraphs into the prompt
rag_chain = create_retrieval_chain(retriever, combine_docs_chain)  # Links the search engine and the prompt pipeline together


# =========================================================================
# PHASE 5: RUNNING A TEST QUESTION
# =========================================================================

print("\n--- Step 4: Your AI Tutor is Ready! ---")
print("Type your questions below. (Type 'exit' or 'quit' to shut down).")

# This 'while True' loop keeps the program running forever until you type 'exit'
while True:
    # 1. Wait for the user to type a question into the terminal
    user_question = input("\nYour Question: ")
    
    # 2. If the user types 'exit', break the loop and close the program
    if user_question.lower() in ['exit', 'quit']:
        print("Shutting down the AI Tutor. Goodbye!")
        break
        
    # 3. If the user accidentally hits Enter without typing, skip and ask again
    if not user_question.strip():
        continue
        
    # 4. Send the typed question into the RAG pipeline!
    print("Thinking...")
    response = rag_chain.invoke({"input": user_question})

    # 5. Print the generated answer
    print("\n================ ANSWER ================")
    print(response["answer"])
    print("========================================")