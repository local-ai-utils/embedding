# Local AI Utils - Embedding
A plugin for [local-ai-utils](https://github.com/local-ai-utils/core), adding the ability to generate embeddings. It is exposed as a CLI utility named `embedding`, which can be sent a prompt.

![Embed Demo](/docs/assist.gif)

## Quickstart

### Installation
Currently installation is only supported via the GitHub remote.
```
pip install git+https://github.com/local-ai-utils/embedding
```

### Configuration
Then update your `ai-utils.yml` file.

- `keys.openai` is your [Open AI secret key](https://platform.openai.com/settings/organization/api-keys).

### Usage
```
$ embed "this is some text to embed"
-0.0028965063
-0.023933379
0.00607678
-0.0015598569
-0.022410722
-0.019919105
...
```

## Configuration
Only an OpenAI key is required

`~/.config/ai-utils.yaml`
```
keys:
    openai: "sk-proj-abc"
```