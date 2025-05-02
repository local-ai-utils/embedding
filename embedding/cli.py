import fire
from .main import generate_embeddings, search_similar, parse_filter_arg
from datetime import datetime, timezone
import sys # For exiting on error
import logging

# Define allowed operators
VALID_OPERATORS = {'>', '<', '=', '>=', '<=', '~', '~>', '<~'}
# Sort operators by length descending to ensure longer ones match first (e.g., >= before >)
SORTED_OPERATORS = sorted(list(VALID_OPERATORS), key=len, reverse=True)

def main():
    return fire.Fire({
        "get": get,
        "search": search
    })

log = logging.getLogger(__name__)

def get(prompt, save=False, relevant_date=None, no_index=False):
    """
    Generates embeddings for a given text prompt.

    Args:
        prompt (str): The text to generate embeddings for.
        save (bool, optional): If True, saves the embedding to the database. Defaults to False.
        relevant_date (str, optional): An optional ISO8601 timestamp string (e.g., 'YYYY-MM-DDTHH:MM:SS' or 'YYYY-MM-DD')
                                       associated with the note's content relevance. Assumed UTC if no timezone provided.
                                       Defaults to None.
        no_index (bool, optional): If True and saving, skips the index rebuild step. Defaults to False.
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

    embeddings = generate_embeddings(prompt, save=save, relevant_date=parsed_relevant_date_obj, no_index=no_index)

    if save:
        print("Embedding saved.")
    else:
        print(embeddings)

def search(query, count=5, created_date=None, relevant_date=None):
    """
    Searches for embeddings similar to the query text, with optional date filters.
    Datetime filters can use the following operators:
    - '>': greater than
    - '<': less than
    - '=': equal to
    - '>=': greater than or equal to
    - '<=': less than or equal to
    - '~': approximately equal to
    - '~>': approximately greater than
    - '<~': approximately less than

    Args:
        query (str): The text to search for.
        count (int, optional): Number of results to return. Defaults to 5.
        created_date (str or tuple[str], optional): Filter(s) based on creation date.
                                                    Format: "OPERATOR TIMESTAMP" (e.g., ">= 2024-01-01", "~> 2024-07-01").
                                                    Can be provided multiple times.
        relevant_date (str or tuple[str], optional): Filter(s) based on relevance date.
                                                     Format: "OPERATOR TIMESTAMP". Can be provided multiple times.
    """
    query_embedding = generate_embeddings(query)

    parsed_filters = parse_filter_arg(created_date, "created_date")
    parsed_filters.extend(parse_filter_arg(relevant_date, "relevant_date"))

    results = search_similar(query_embedding, k=count, filters=parsed_filters)

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
            # Format dates for display
            created_date = item.get('created_date', 'N/A')
            if isinstance(created_date, datetime):
                created_date = created_date.strftime('%Y-%m-%d %H:%M')
            
            relevant_date = item.get('relevant_date', 'N/A')
            if isinstance(relevant_date, datetime):
                relevant_date = relevant_date.strftime('%Y-%m-%d %H:%M')
            
            print(f"{i}. {item['metadata']} - Distance: {item['_distance']:.4f} (Relative similarity: {relative_similarity:.1f}%)")
            print(f"   Created: {created_date} | Relevant: {relevant_date}")

if __name__ == '__main__':
    main()