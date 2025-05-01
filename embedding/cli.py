import fire
from .main import generate_embeddings, add_embedding, search_similar

def main():
    return fire.Fire({
        "get": get,
        "search": search
    })

def get(prompt, save=False):
    embeddings = generate_embeddings(prompt, save=save)
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
        distances = [distance for _, _, distance in results]
        min_dist = min(distances)
        max_dist = max(distances)
        range_dist = max_dist - min_dist if max_dist > min_dist else 1.0
        
        for i, (metadata, vector, distance) in enumerate(results, 1):
            # Calculate relative similarity (0-100%)
            relative_similarity = 100 * (1 - (distance - min_dist) / range_dist) if range_dist else 100
            print(f"{i}. {metadata} - Distance: {distance:.4f} (Relative similarity: {relative_similarity:.1f}%)")

if __name__ == '__main__':
    main()