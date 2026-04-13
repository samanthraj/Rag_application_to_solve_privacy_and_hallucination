# Rag_application_to_solve_privacy_and_hallucination
its a rag application with a user interface similar to chatgpt, where we can tailor the response of the ai (groq) model give more accurate answer. using something called context, there are two pipelines here, data retreival pipeline and data ingestion pipeline, we inject data, chunk it and embed and store it in vector db, next is QR pipeline
where when a user sends a query, first it will be embeded then, it will go to the vector data base, similarity search will run, which will take this vector of query and finds top 5 related vectors, this vectors are then sent to llm as a context with a prompt which will give a more tailored output
pros:
-dont have to fine tune the model with your data, simply can add your data through data ingestion pipeline
-model will have less chance to hallucinate because of this context and the prompt.
cons:
-output given by llm maybe be small, depending on the model used(high end models will give better response)


