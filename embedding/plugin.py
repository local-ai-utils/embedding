from . import tools

def register(_, plugin_config):
    """Registers the embedding plugin with its tools and functions."""
    return {
        "name": "embedding",
        "tools": tools,
        "functions": [
            {
                "name": "store_embedding",
                "description": "Generates and stores a vector embedding for a given piece of text. Optionally include a relevant date (ISO8601 format) associated with the text's content.",
                "strict": True, # Ensure only defined parameters are accepted
                "parameters": {
                    "type": "object",
                    "required": ["text", "relevant_date"],
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text content to generate an embedding for and store."
                        },
                        "relevant_date": {
                            "type": ["string", "null"],
                            "description": "Optional. An ISO8601 timestamp string (e.g., 'YYYY-MM-DDTHH:MM:SS') indicating a date/time the content is relevant to, for example a scheduled note or a reference to something in the past. Assumed UTC if timezone is omitted.",
                        }
                    },
                    "additionalProperties": False
                }
            },
            {
                "name": "search_embeddings",
                "description": "Searches stored embeddings for text similar to the query. Allows filtering by creation date and relevance date using specific operators.",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "required": ["query", "count", "created_date_filters", "relevant_date_filters"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The text query to search for similar embeddings."
                        },
                        "count": {
                            "type": ["integer", "null"],
                            "description": "Optional. The maximum number of similar results to return. Default is 5",
                        },
                        "created_date_filters": {
                            "type": ["array", "null"],
                            "description": "Optional. List of filters for the embedding's creation date. Operators are >, <, =, >=, <=, ~, ~>, <~. The tilde operators (~, ~>, <~) are approximate operators, and give a little bit of leeway to the date filters. The format for this parameter is '<operator> <ISO8601_TIMESTAMP>'. Example: '~> 2024-01-01' would be any date after January 1st, 2024.",
                            "items": {
                                "type": "string",
                                "description": "Filter string (e.g., '>= 2024-01-01', '<~ 2024-07-10T12:00:00')"
                            }
                        },
                        "relevant_date_filters": {
                            "type": ["array", "null"],
                            "description": "Optional. List of filters for the embedding's relevance date. Embeddings can optionally have a 'relevant_date' for future scheduled notes or referencing things in the past. Filter by relevancy date by using an ISO8601 timestamp. Operators are >, <, =, >=, <=, ~, ~>, <~. The tilde operators (~, ~>, <~) are approximate operators, and give a little bit of leeway to the date filters. The format for this parameter is '<operator> <ISO8601_TIMESTAMP>'. Example: '~> 2024-01-01' would be any date after January 1st, 2024.",
                            "items": {
                                "type": "string",
                                "description": "Filter string (e.g., '<= 2024-08-01', '~ 2024-07-15')"
                            }
                        }
                    },
                    "additionalProperties": False
                }
            }
        ]
    }
