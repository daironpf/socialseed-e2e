"""Page class for JSONPlaceholder API.

This is a human-written Page class that demonstrates how to manually write
API interaction code without relying on AI agents. It provides methods to
interact with the JSONPlaceholder API (https://jsonplaceholder.typicode.com/).

The Page Object Pattern:
------------------------
The Page class encapsulates all API interactions for a specific service.
Instead of scattering HTTP calls throughout your tests, you define them here
in a clean, reusable way. This makes tests more readable and maintainable.
"""

# Import BasePage - this is the base class that provides HTTP methods
# like get(), post(), put(), delete(), etc.
from socialseed_e2e.core.base_page import BasePage

# Optional: Import type hints for better code clarity
from typing import Optional, Any, Dict


class JsonPlaceholderPage(BasePage):
    """Page object for JSONPlaceholder API interactions.

    This class extends BasePage and provides methods to interact with
    the JSONPlaceholder fake REST API. Each method represents a specific
    API operation.

    Attributes:
        base_url: The base URL for the API, passed to the parent BasePage

    Example:
        >>> page = JsonPlaceholderPage(base_url="https://jsonplaceholder.typicode.com")
        >>> response = page.get_post(1)
        >>> print(response.status)  # 200
    """

    def __init__(self, base_url: str, **kwargs):
        """Initialize the JsonPlaceholderPage with base URL.

        This constructor is REQUIRED. It must:
        1. Accept base_url as the first parameter
        2. Call super().__init__() to initialize the parent BasePage
        3. Pass base_url and any additional kwargs to the parent

        Args:
            base_url: The base URL for the API endpoint.
                     Example: "https://jsonplaceholder.typicode.com"
            **kwargs: Additional arguments passed to BasePage (optional).
                     Can include timeout, headers, etc.

        Example:
            >>> page = JsonPlaceholderPage(
            ...     base_url="https://jsonplaceholder.typicode.com",
            ...     timeout=10000  # 10 second timeout
            ... )
        """
        # Call the parent class constructor with base_url
        # This is REQUIRED - without it, the Page won't work properly
        super().__init__(base_url=base_url, **kwargs)

    def get_post(self, post_id: int) -> Any:
        """Fetch a single post by ID.

        This method demonstrates a simple GET request to fetch a resource.
        It uses the inherited get() method from BasePage.

        Args:
            post_id: The ID of the post to fetch.
                    JSONPlaceholder has posts with IDs 1-100.

        Returns:
            APIResponse: The HTTP response object containing:
                - status: HTTP status code (200 for success)
                - json(): Parsed JSON response body
                - headers: Response headers
                - ok: Boolean indicating success (status < 400)

        Example:
            >>> response = page.get_post(1)
            >>> assert response.status == 200
            >>> data = response.json()
            >>> print(data['title'])  # "sunt aut facere..."

        API Endpoint: GET /posts/{post_id}
        """
        # Construct the endpoint URL by combining the base_url (from parent)
        # with the specific path for this resource
        endpoint = f"/posts/{post_id}"

        # Call the get() method inherited from BasePage
        # This performs the actual HTTP GET request
        response = self.get(endpoint)

        # Return the response object for further assertions in tests
        return response

    def get_all_posts(self) -> Any:
        """Fetch all posts from the API.

        Demonstrates fetching a collection of resources.

        Returns:
            APIResponse: Response containing a list of posts.

        API Endpoint: GET /posts
        """
        # Simple GET request to the /posts endpoint
        return self.get("/posts")

    def create_post(self, title: str, body: str, user_id: int) -> Any:
        """Create a new post (simulated - JSONPlaceholder doesn't actually save).

        Demonstrates a POST request with a JSON body. Note that
        JSONPlaceholder is a fake API, so this won't actually create
        a persistent resource, but it will return a mock response.

        Args:
            title: The title of the post
            body: The body/content of the post
            user_id: The user ID to associate with the post

        Returns:
            APIResponse: Response containing the "created" post with an ID.

        API Endpoint: POST /posts
        """
        # Prepare the request body as a dictionary
        # This will be automatically serialized to JSON by the post() method
        data = {"title": title, "body": body, "userId": user_id}

        # Make the POST request with JSON body
        response = self.post("/posts", json=data)

        return response
