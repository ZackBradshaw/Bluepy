import os
import json
import pandas as pd
import asyncio
import aiohttp
from itertools import combinations
import random
from tqdm import tqdm  # tqdm is a library to display progress bars in console

# Fetch the OpenAI API key from environment variables.
# Ensure the API key is set in the environment before running this script.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_ENDPOINT = "https://api.openai.com/v1/chat/completions"


class TokenBucket:
    """
    This class implements the token bucket algorithm which helps in rate limiting.
    The idea is that tokens are added to the bucket at a fixed rate and consumed when requests are made.
    If the bucket is empty, it means the rate limit has been exceeded.
    """

    def __init__(self, rate: int, capacity: int):
        """
        Initialize a new instance of TokenBucket.

        Parameters:
        - rate: The rate at which tokens are added to the bucket.
        - capacity: Maximum number of tokens the bucket can hold.
        """
        self._rate = rate
        self._capacity = capacity
        self._tokens = capacity
        self._last_refill = asyncio.get_event_loop().time()

    async def consume(self):
        """
        Consume a token from the bucket. If no tokens are available, it waits.
        """
        while not self._consume():
            await asyncio.sleep(0)
        await asyncio.sleep(1 / self._rate)

    def _consume(self):
        """
        Internal method to consume a token. Refills the bucket based on elapsed time.
        """
        current_time = asyncio.get_event_loop().time()
        elapsed_time = current_time - self._last_refill

        refill_tokens = self._rate * elapsed_time
        self._tokens = min(self._capacity, self._tokens + refill_tokens)
        self._last_refill = current_time

        if self._tokens >= 1:
            self._tokens -= 1
            return True
        return False

# Semaphore is used to limit the number of simultaneous requests.
SEMAPHORE = asyncio.Semaphore(80)
RATE_LIMITER = TokenBucket(80, 80)  # Set rate and capacity both to 100.


async def fetch(session, url, payload, retries=2, backoff_factor=1.0):
    """
    A utility asynchronous function to make POST requests.

    Parameters:
    - session: An aiohttp session object.
    - url: API endpoint to make request.
    - payload: Data payload to send in POST request.
    - retries: Number of retries in case of failure.
    - backoff_factor: Multiplier used to increase the delay between retries.
    """
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    # Retry mechanism in case of failures
    for attempt in range(retries):
        try:
            async with session.post(url, headers=headers,
                                    json=payload) as response:
                if response.status != 200:
                    error_content = await response.text()
                    print(f"API returned an error (status {response.status}): {error_content}")
                    continue
                return await response.json()
        except Exception as e:
            if attempt + 1 == retries:
                print(f"API Error after {retries} attempts: {e}")
                raise
            else:
                wait_time = backoff_factor * (2**attempt) * 1.5
                print(f"API Error: {e}. Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)


async def generate_response_async(chunks, num_triplets, model_choice, custom_system_message, custom_prompt_prefix, custom_json_format):
    """
    Asynchronous function to generate a response from the OpenAI API.

    Parameters:
    - chunks: List of text chunks to consider.
    - num_triplets: Number of questions and answers to generate.
    - model_choice: The model choice for the OpenAI API.
    - custom_system_message: Custom system message for the OpenAI prompt.
    - custom_prompt_prefix: Custom prefix for the OpenAI prompt.
    - custom_json_format: Desired format of the response JSON.
    """
    # Ensure we are within rate limits
    await RATE_LIMITER.consume()

    async with SEMAPHORE:
        combined_text = "\n\n".join([
            f"Text {chunk['ChunkID']} {{\n{chunk['ChunkText']}\n}}"
            for chunk in chunks
        ])

        # Construct the prompt for the API
        prompt = custom_prompt_prefix + combined_text + "\n\nThe structure of your JSON response should be:\n[" + ",\n".join(
            [custom_json_format for _ in range(num_triplets)]) + "\n]"

        # List of potential models
        models = [
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-0301",
            "gpt-3.5-turbo-0613"
        ]

        # Choose a model randomly from the list
        random_model_choice = random.choice(models)

        # Construct the payload for the API
        payload = {
            "model": random_model_choice,
            "messages": [{
                "role": "system",
                "content": custom_system_message
            }, {
                "role": "user",
                "content": prompt
            }],
            "temperature": 0.0
        }

        # Make the API request and handle any exceptions
        try:
            async with aiohttp.ClientSession() as session:
                response = await fetch(session, API_ENDPOINT, payload)
                return json.loads(response['choices'][0]['message']['content'])
        except Exception as e:
            print(f"API Error: {e}")
            return [{
                "error": "API Error",
                "question": "NA",
                "answer": "NA",
                "quoted_text": "NA"
            } for _ in range(num_triplets)]


async def main(input_csv):
    """
    Main function to orchestrate the process.

    Parameters:
    - input_csv: Path to the input CSV file containing text chunks.
    """
    # Read the CSV file
    df = pd.read_csv(input_csv, encoding='utf-8')
    questions = []

    # Custom messages and formats
    custom_system_message = "You are an expert in splitting ."
    custom_json_format = '{"question": "insert question", "answer":"insert answer", "quoted_text": "insert the number of the text that was used to answer the question"}'
    num_triplets = 6
    custom_prompt_prefix = (f"Your task is to write {num_triplets} distinct questions and sarcastic, rude answers about the provided texts. "
                            "The answers should be written in a California Valley girl style, similar to how Kim Kardashian speaks. "
                            "The answers should end with exclamation points. The questions should be able to be "
                            "answered directly by using only one of the texts at a time. The questions should be written in a normal tone. "
                            "Important: The answers should be written in a sarcastic, funny, dry tone (slightly humorous)! The answers must be entertaining. "
                            "Provide a JSON list of {num_triplets} questions and their answers, along with an indication of which text the answer was derived from, from the following texts:\n")

    model_choice = 'gpt-3.5-turbo-0613'
    num_chunks = 3

    # Create all possible combinations of chunks
    chunk_combinations = list(combinations(df.iterrows(), num_chunks))

    # Initialize a progress bar
    pbar = tqdm(total=len(chunk_combinations), desc="Processing chunks", position=0, leave=True)

    async def wrapped_generate_response_async(chunk_group):
        """Helper function to wrap the generation and update progress bar."""
        result = await generate_response_async([row[1] for row in chunk_group], num_triplets, model_choice, custom_system_message, custom_prompt_prefix, custom_json_format)
        pbar.update(1)
        return result

    # Create a list of tasks for all chunk combinations
    tasks = [
        wrapped_generate_response_async(chunk_group)
        for chunk_group in chunk_combinations
    ]

    # Execute all tasks and wait for their completion
    results = await asyncio.gather(*tasks)

    pbar.close()

    # Process results and append to questions list
    for triplet_group, chunk_group in zip(results, chunk_combinations):
        for triplet in triplet_group:
            if 'error' in triplet:
                questions.append(["NA", "NA", "NA", "NA", "NA"])
            else:
                try:
                    question = triplet['question']
                    answer = triplet['answer']
                    quoted_text_id = triplet['quoted_text']
                    chunk_ids = ", ".join(
                        [str(row[1]['ChunkID']) for row in chunk_group])
                    chunk_texts = "\n".join([
                        f"Text {row[1]['ChunkID']} {{\n{json.dumps(row[1]['ChunkText'])}\n}}"
                        for row in chunk_group
                    ])
                    questions.append(
                        [chunk_ids, chunk_texts, question, answer, quoted_text_id])
                except:
                    questions.append(["NA", "NA", "NA", "NA", "NA"])
                    pass

    # Convert questions list to DataFrame and save to CSV
    question_df = pd.DataFrame(questions,
                               columns=[
                                   'ChunkIDs', 'ChunkTexts', 'Question',
                                   'Answer', 'Quoted_Text_ID'
                               ])
    question_df.to_csv('output.csv', index=False)

# If script is run as main, execute the main function
if __name__ == '__main__':
    asyncio.run(main("chunks.csv")) #the name of your file

