# AI assistant

## Why use it

You want fast answers with citations.
You want a direct link to the right MolSysSuite page.

## How to use it

1. Ask a question about MolSysViewer.
2. Open the “Sources” links to verify the answer.
3. Retry if the backend is busy.

```{raw} html
<div id="molsys-ai-chat"></div>
```

## Notes

- The assistant calls `https://api.uibcdf.org/v1/chat`.
- It does not execute commands or modify files.
- If the backend is offline, you will see a short error message.
