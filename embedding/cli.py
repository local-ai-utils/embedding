import fire
from .main import generate_embeddings, search_similar
from datetime import datetime, timezone
import sys # For exiting on error
import logging

def main():
    return fire.Fire({
        "get": get,
        "search": search
    })

log = logging.getLogger(__name__)

def get(prompt, save=False, relevant_date=None):
    """
    Generates embeddings for a given text prompt.

    Args:
        prompt (str): The text to generate embeddings for.
        save (bool, optional): If True, saves the embedding to the database. Defaults to False.
        relevant_date (str, optional): An optional ISO8601 timestamp string (e.g., 'YYYY-MM-DDTHH:MM:SS' or 'YYYY-MM-DD')
                                       associated with the note's content relevance. Assumed UTC if no timezone provided.
                                       Defaults to None.
    """
    parsed_relevant_date_obj = None
    if relevant_date is not None:
        try:
            # Attempt to parse the string to validate format
            parsed_relevant_date_obj = datetime.fromisoformat(relevant_date)
            # If the parsed datetime has no timezone, assume it's UTC
            if parsed_relevant_date_obj.tzinfo is not None:
                parsed_relevant_date_obj = parsed_relevant_date_obj.astimezone(timezone.utc).replace(tzinfo=None)
                
        except ValueError:
            log.error(f"Invalid relevant_date format: '{relevant_date}'. Please use ISO8601 format (e.g., 'YYYY-MM-DDTHH:MM:SS' or 'YYYY-MM-DD').")
            sys.exit(1) # Exit if validation fails

    embeddings = generate_embeddings(prompt, save=save, relevant_date=parsed_relevant_date_obj)
    print(embeddings)

    if save:
        print("Embedding saved.")

def search(query, count=5):
    # Generate embeddings for the query
    query_embedding = generate_embeddings(query)
    
    # Search for similar embeddings
    results = search_similar(query_embedding, k=count)
    
    # Print results
    print(f"Top {len(results)} similar items for '{query}':")
    
    # Calculate min and max distances for relative comparison
    if results:
        distances = [item['_distance'] for item in results]
        min_dist = min(distances)
        max_dist = max(distances)
        range_dist = max_dist - min_dist if max_dist > min_dist else 1.0
        
        for i, item in enumerate(results, 1):
            # Calculate relative similarity (0-100%)
            relative_similarity = 100 * (1 - (item['_distance'] - min_dist) / range_dist) if range_dist else 100
            print(f"{i}. {item['metadata']} - Distance: {item['_distance']:.4f} (Relative similarity: {relative_similarity:.1f}%)")

if __name__ == '__main__':
    main()