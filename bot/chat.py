import os
from chroma.storage import semantic_search
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

model = ChatOpenAI(model='gpt-4o-mini', 
               api_key=os.getenv('OPENAI_API_KEY'))

def user_query(query):
    print(f"User Query: {query}")
    # retrival
    relevent_context = semantic_search(query)
    docs, sources = relevent_context
    context = "\n\n".join(doc for doc in docs)
    all_source = "\n\n".join(f"https://{source.replace('_', '/').replace('.txt', '')}" for source in sources)
    # Step 2: Augmentation - Create prompt template
    prompt = ChatPromptTemplate.from_template(
        """You are a helpful customer assistance agent. 
        
        Use the following context to answer the user's question. If the context doesn't contain relevant information, politely say so and provide general guidance.

        Context:
        {context}

        Question: {query}

        Provide a clear, professional, and helpful response:"""
    )
#     prompt = f"""
#     provide a professional response of the following query

#     #context:
#     {relevent_context}

#     #question:
#     {query}

# """
    # generate
    # response = client.chat.completions.create(
    #     model='gpt-4o-mini',
    #     messages=[
    #         {"role": "system", "content": f"You are a helpful client support assistant. Having this context:\n {relevent_context}"},
    #         {"role": "user", "content": prompt}
    #     ]
    # )
    chain = prompt | model | StrOutputParser()

    result = chain.invoke({"query":f"{query}", "context": f"{context}"})
    final_result = f"""
        {result} \n
        source: \n
        {all_source}
"""
    return result, all_source