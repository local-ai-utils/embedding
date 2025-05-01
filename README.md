# Local AI Utils - Embedding
A plugin for [local-ai-utils](https://github.com/local-ai-utils/core), adding the ability to generate and search text embeddings. It is exposed as a CLI utility named `embedding`.

![Embed Demo](/docs/assist.gif)

## Quickstart

### Installation
Currently installation is only supported via the GitHub remote.
```bash
pip install git+https://github.com/local-ai-utils/embedding
```

### Configuration
An OpenAI API key is required for generating embeddings using the `text-embedding-3-large` model. Configure it in your `ai-utils.yml` file.

`~/.config/ai-utils.yaml`
```yaml
keys:
    openai: "sk-proj-abc..."
```

### Usage

**Generate and Save an Embedding:**
```bash
# Save with just the prompt
embedding get "Review pull request #482" --save

# Save with a relevant date (e.g., meeting date)
embedding get "Discuss Q3 roadmap in meeting" --save --relevant-date '2024-07-15'

# Save with a specific relevant time
embedding get "Team lunch at noon" --save --relevant-date '2024-07-18T12:00:00'
```

**Search Embeddings:**
```bash
$ embedding search "roadmap planning" --count 3
Top 3 similar items for 'roadmap planning':
1. Book conference room for roadmap review
2. Sync roadmap slide with updated metrics
3. Create T-shirt sizes for roadmap items
```