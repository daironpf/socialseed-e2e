# Record and Replay Test Sessions

socialseed-e2e includes a built-in recorder that allows you to capture manual API interactions and convert them into automated test modules instantly.

## 🔴 Recording a Session

To start recording, use the `recorder record` command:

```bash
e2e recorder record my-session
```

This starts a recording proxy on `http://localhost:8090`.

### Pointing your tools to the proxy

You need to configure your API client (Postman, Insomnia, cURL, or Browser) to use the proxy.

#### cURL example:
```bash
curl -x http://localhost:8090 http://api.example.com/users
```

#### Postman:
Go to **Settings** > **Proxy** and enable **Manual Proxy Configuration**. Set the proxy server to `localhost` and port `8090`.

Once you are done interacting with your API, press `Ctrl+C` in the terminal to save the session. The session will be saved as a JSON file in `recordings/my-session.json`.

## ▶️ Replaying a Session

You can replay a recorded session exactly as it was captured:

```bash
e2e recorder replay recordings/my-session.json
```

This will execute each interaction in sequence and verify that the status codes match the original recording.

## 🛠️ Converting to Test Code

The most powerful feature of the recorder is converting sessions into maintainable Python code:

```bash
e2e recorder convert recordings/my-session.json
```

This generates a new test module (e.g., `services/recorded/modules/my-session_flow.py`) that uses the standard `BasePage` API. You can then move this file to any service and enhance it with more complex logic or assertions.

### Example Generated Code:

```python
"""Recorded test session: my-session"""
from socialseed_e2e.core import tag

@tag("recorded")
def run(page):
    """Run recorded interactions for my-session."""

    # Interaction 1: GET http://api.example.com/users
    response = page.get('http://api.example.com/users')
    page.assert_status(response, 200)

    # Interaction 2: POST http://api.example.com/users
    response = page.post('http://api.example.com/users', json={
        "name": "New User",
        "email": "user@example.com"
    })
    page.assert_status(response, 201)
```

## Advanced Usage

- **Custom Port**: Use `--port` to change the proxy port.
- **Custom Output**: Use `--output` to specify where to save the session JSON or the generated Python module.
- **HTTPS**: For recording HTTPS traffic, ensure your client is configured to ignore SSL certificate validation (since the simple proxy uses standard `requests` and doesn't handle certificate injection yet).
